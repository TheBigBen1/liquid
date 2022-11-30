# pylint: disable=missing-module-docstring
from __future__ import annotations
from typing import TYPE_CHECKING

from .filters import index
from .filters import JSON
from .filters import script_tag
from .filters import stylesheet_tag

from .tags import CallTag
from .tags import IfNotTag
from .tags import InlineIfAssignTag
from .tags import InlineIfAssignTagWithParens
from .tags import InlineIfEchoTag
from .tags import InlineIfEchoTagWithParens
from .tags import InlineIfStatement
from .tags import InlineIfStatementWithParens
from .tags import MacroTag
from .tags import WithTag


if TYPE_CHECKING:  # pragma: no cover
    from liquid import Environment

__all__ = (
    "index",
    "JSON",
    "script_tag",
    "stylesheet_tag",
    "CallTag",
    "IfNotTag",
    "InlineIfAssignTag",
    "InlineIfAssignTagWithParens",
    "InlineIfEchoTag",
    "InlineIfEchoTagWithParens",
    "InlineIfStatement",
    "InlineIfStatementWithParens",
    "MacroTag",
    "WithTag",
    "add_filters",
    "add_inline_expression_tags",
    "add_extended_inline_expression_tags",
    "add_macro_tags",
    "add_tags",
    "add_tags_and_filters",
)


def add_inline_expression_tags(env: Environment) -> None:
    """Replace standard implementations of the output statement,
    `echo` tag and `assign` tag with ones that support inline `if`
    expressions."""
    env.add_tag(InlineIfAssignTag)
    env.add_tag(InlineIfEchoTag)
    env.add_tag(InlineIfStatement)


def add_extended_inline_expression_tags(env: Environment) -> None:
    """Replace standard implementations of the output statement,
    `echo` tag and `assign` tag with ones that support inline `if`
    expressions."""
    env.add_tag(InlineIfAssignTagWithParens)
    env.add_tag(InlineIfEchoTagWithParens)
    env.add_tag(InlineIfStatementWithParens)


def add_macro_tags(env: Environment) -> None:
    """Register both the `macro` and `call` tags with an environment."""
    env.add_tag(CallTag)
    env.add_tag(MacroTag)


def add_tags(env: Environment) -> None:  # pragma: no cover
    """Register all extra tags with an environment."""
    env.add_tag(IfNotTag)
    env.add_tag(WithTag)
    add_macro_tags(env)
    add_extended_inline_expression_tags(env)


def add_filters(env: Environment) -> None:
    """Register all extra filters with an environment with their default
    and options."""
    env.add_filter("index", index)
    env.add_filter("json", JSON())
    env.add_filter("script_tag", script_tag)
    env.add_filter("stylesheet_tag", stylesheet_tag)


def add_tags_and_filters(env: Environment) -> None:  # pragma: no cover
    """Register all extra tags and filters with an environment."""
    add_tags(env)
    add_filters(env)
