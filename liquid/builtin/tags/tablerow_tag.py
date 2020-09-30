""""""
import sys
import collections.abc
import math
from itertools import islice
from typing import Any, List, TextIO

from liquid.token import Token, TOKEN_TAG_NAME, TOKEN_EXPRESSION
from liquid import ast
from liquid.tag import Tag
from liquid.context import Context
from liquid.lex import TokenStream, get_expression_lexer
from liquid.expression import LoopExpression
from liquid.parse import expect, parse_loop_expression, get_parser

from liquid import Compiler
from liquid import Opcode
from liquid.object import CompiledBlock

from liquid.builtin.drops import IterableDrop


TAG_TABLEROW = sys.intern("tablerow")
TAG_ENDTABLEROW = sys.intern("endtablerow")


class TableRow(collections.abc.Mapping):
    """Table row helper variables."""

    __slots__ = (
        "name",
        "length",
        "ncols",
        "item",
        "first",
        "last",
        "index",
        "index0",
        "rindex",
        "rindex0",
        "col",
        "col0",
        "col_first",
        "col_last",
        "keys",
        "row",
        "nrows",
    )

    def __init__(self, name: str, length: int, ncols: int):
        self.name = name
        self.length = length
        self.ncols = ncols
        self.item = None

        self.first = False
        self.last = False
        self.index = 0
        self.index0 = -1
        self.rindex = self.length + 1
        self.rindex0 = self.length

        self.col = 0
        self.col0 = -1
        self.col_first = True
        self.col_last = False

        # Zero based row counter is not exposed to templates.
        self.row = 0
        self.nrows = math.ceil(self.length / self.ncols)

        self.keys: List[str] = [
            "length",
            "index",
            "index0",
            "rindex",
            "rindex0",
            "first",
            "last",
            "col",
            "col0",
            "col_first",
            "col_last",
        ]

    def __repr__(self):  # pragma: no cover
        return f"TableRow(name='{self.name}', length={self.length})"

    def __getitem__(self, key):
        if key in self.keys:
            return getattr(self, key)
        raise KeyError(key)

    def __len__(self):
        return len(self.keys)

    def __iter__(self):
        return iter(self.keys)

    def step(self, item: Any):
        """Set the value for the current/next loop iteration and update forloop
        helper variables."""
        self.item = item

        self.index += 1
        self.index0 += 1
        self.rindex -= 1
        self.rindex0 -= 1

        if self.index0 == 0:
            self.first = True
        else:
            self.first = False

        if self.rindex0 == 0:
            self.last = True
        else:
            self.last = False

        self.col0 = self.index0 % self.ncols
        self.col = self.col0 + 1

        if self.col == 1:
            self.col_first = True
        else:
            self.col_first = False

        if self.col == self.ncols:
            self.col_last = True
        else:
            self.col_last = False

        if self.col == 1:
            self.row += 1


class TableRowDrop(IterableDrop, collections.abc.Mapping):
    """Wrap a `TableRow` so it can be used as a `Context` namepsace."""

    __slots__ = ("tablerow", "name")

    def __init__(self, name: str, length: int, ncols: int):
        self.tablerow = TableRow(name, length, ncols)
        self.name = name

        self._exit = []

    def __contains__(self, item):
        if item in ("tablerowloop", self.name):
            return True
        return False

    def __getitem__(self, key):
        if key == "tablerowloop":
            return self.tablerow
        if key == self.name:
            return self.tablerow.item
        raise KeyError(str(key))

    def __len__(self):
        return 2

    def __iter__(self):
        return iter(["tablerowloop", self.name])

    def __str__(self):
        return f"TableRowDrop(name='{self.name}', tablerow={self.tablerow})"

    def step(self, item: Any):
        self.tablerow.step(item)

    def step_write(self, item: Any, buffer: TextIO):
        self.empty_exit_buffer(buffer)
        self.step(item)

        if self.tablerow.col == 1 and self.tablerow.row <= self.tablerow.nrows:
            buffer.write(f'<tr class="row{self.tablerow.row}">')

        buffer.write(f'<td class="col{self.tablerow.col}">')

        if (
            self.tablerow.col == self.tablerow.ncols
            or self.tablerow.index == self.tablerow.length
        ):
            self._exit.append("</td></tr>")
        else:
            self._exit.append("</td>")

    def empty_exit_buffer(self, buffer: TextIO):
        try:
            buffer.write(self._exit.pop())
        except IndexError:
            pass


class TablerowNode(ast.Node):
    __slots__ = ("tok", "expression", "block")

    statement = False

    def __init__(
        self,
        tok: Token,
        expression: LoopExpression,
        block: ast.BlockNode,
    ):
        self.tok = tok
        self.expression = expression
        self.block = block

    def __str__(self) -> str:
        return f"tablerow({ self.expression }) {{ {self.block} }}"

    def render_to_output(self, context: Context, buffer: TextIO):
        loop_items = list(self.expression.evaluate(context))

        if self.expression.cols:
            cols = self.expression.cols.evaluate(context)
            assert isinstance(cols, int)
            loop_iter = tuple(grouper(loop_items, cols))
        else:
            cols = 1
            loop_iter = (loop_items,)

        drop = TableRowDrop(self.expression.name, len(loop_items), cols)
        ctx = context.extend(drop)

        for i, row in enumerate(loop_iter):
            buffer.write(f'<tr class="row{i+1}">')
            for j, data in enumerate(row):
                drop.step(data)
                buffer.write(f'<td class="col{j+1}">')
                self.block.render(context=ctx, buffer=buffer)
                buffer.write("</td>")
            buffer.write("</tr>")

    def compile_node(self, compiler: Compiler):
        # tablerow tags have two block scoped variables, the loop variable and
        # the `tablerow` helper drop.
        compiler.enter_scope()

        symbol = compiler.symbol_table.define(self.expression.name)
        compiler.symbol_table.define("tablerowloop")

        top_of_loop = len(compiler.current_instructions())

        self.block.compile(compiler)

        compiler.emit(Opcode.STE, symbol.index)  # step
        compiler.emit(Opcode.JMP, top_of_loop)  # jump

        compiler.emit(Opcode.STO)

        # Must instpect the scoped symbol table before leaving the scope.
        free_symbols = compiler.symbol_table.free_symbols
        num_block_vars = compiler.symbol_table.locals.size
        assert num_block_vars == 2

        instructions = compiler.leave_scope()

        # num_locals is always 2, the loop variable and the `forloop` drop.
        compiled_block = CompiledBlock(
            instructions=instructions,
            num_locals=2,
            num_arguments=self.expression.num_arguments(),
            num_free=len(free_symbols),
        )

        compiler.emit(Opcode.CONSTANT, compiler.add_constant_block(compiled_block))

        for free_symbol in reversed(free_symbols):
            compiler.load_symbol(free_symbol)

        if self.expression.cols:
            self.expression.cols.compile(compiler)
        else:
            compiler.emit(Opcode.NIL)

        self.expression.compile(compiler)
        compiler.emit(Opcode.TAB, compiled_block.num_arguments, compiled_block.num_free)


class TablerowTag(Tag):

    name = TAG_TABLEROW
    end = TAG_ENDTABLEROW

    def parse(self, stream: TokenStream) -> TablerowNode:
        lexer = get_expression_lexer(self.env)
        parser = get_parser(self.env)

        expect(stream, TOKEN_TAG_NAME, value=TAG_TABLEROW)
        tok = stream.current
        stream.next_token()

        expect(stream, TOKEN_EXPRESSION)
        expr_iter = lexer.tokenize(stream.current.value)
        loop_expression = parse_loop_expression(expr_iter)
        stream.next_token()

        block = parser.parse_block(stream, (TAG_ENDTABLEROW,))
        expect(stream, TOKEN_TAG_NAME, value=TAG_ENDTABLEROW)

        return TablerowNode(tok, expression=loop_expression, block=block)


def grouper(iterable, n):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3) --> ABC DEF G"
    iterable = iter(iterable)
    return iter(lambda: tuple(islice(iterable, n)), ())
