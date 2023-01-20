"""Liquid specific Exceptions and warnings."""

from typing import Any
from typing import Dict
from typing import Optional
from typing import Type
from typing import Union

from pathlib import Path


class Error(Exception):
    """Base class for all Liquid exceptions."""

    def __init__(
        self,
        *args: object,
        linenum: Optional[int] = None,
        filename: Optional[Union[str, Path]] = None,
    ):
        self.linenum = linenum
        self.filename = filename
        super().__init__(*args)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.linenum:
            msg = f"{msg}, on line {self.linenum}"
        if self.filename:
            msg += f" of {self.filename}"
        return msg

    @property
    def message(self) -> object:
        """Return the exception's error message if one was given."""
        if self.args:
            return self.args[0]
        return None


class LiquidInterrupt(Exception):
    """Loop interrupt"""


class StopRender(Exception):
    """An interrupt used to signal that ``BoundTemplate.render_with_context`` should
    stop rendering more nodes. This is used by template inheritance tags and is not
    an error condition."""


class LiquidEnvironmentError(Error):
    """An exception raised due to a misconfigured environment."""


class LiquidSyntaxError(Error):
    """Exception raised when there is a parser error."""

    def __init__(
        self,
        *args: object,
        linenum: Optional[int] = None,
        filename: Optional[Union[str, Path]] = None,
    ):
        super().__init__(*args, linenum=linenum, filename=filename)
        self.source: Optional[str] = None

    @property
    def name(self) -> str:
        """Return the name of the template that raised this exception. Return an empty
        string if a name is not available."""
        if isinstance(self.filename, Path):
            return self.filename.as_posix()
        if self.filename:
            return str(self.filename)
        return ""


class TemplateInheritanceError(LiquidSyntaxError):
    """An exceptions raised when template inheritance tags are used incorrectly."""


class RequiredBlockError(TemplateInheritanceError):
    """An exception raised when a required block has not been overridden."""


class LiquidTypeError(Error):
    """Exception raised when an error occurs at render time."""


class DisabledTagError(Error):
    """Exception raised when an attempt is made to render a disabled tag."""


class NoSuchFilterFunc(Error):
    """Exception raised when a filter lookup fails."""


class FilterError(Error):
    """Exception raised when a filter fails."""


class FilterArgumentError(Error):
    """Exception raised when a filter's arguments are invalid."""


class FilterValueError(Error):
    """Exception raised when a filters value is invalid."""


class TemplateNotFound(Error):
    """Exception raised when a template could not be found."""

    def __str__(self) -> str:
        msg = super().__str__()
        msg = f"template not found {msg}"
        return msg


class ResourceLimitError(Error):
    """Base class for exceptions relating to resource limits."""


class ContextDepthError(ResourceLimitError):
    """Exception raised when the maximum context depth is reached.

    Usually indicates recursive use of ``render`` or ``include`` tags.
    """


class LoopIterationLimitError(ResourceLimitError):
    """Exception raised when the maximum number of loop iterations has
    been exceeded.
    """


class OutputStreamLimitError(ResourceLimitError):
    """Exception raised when an output stream limit has been exceeded."""


class LocalNamespaceLimitError(ResourceLimitError):
    """Exception raised when the maximum size of a render context's local namespace
    has been exceeded."""


# LiquidValueError inheriting from LiquidSyntaxError does not make complete sense.
# The alternative is to have multiple to_int functions that raise more appropriate
# exceptions depending on whether we are parsing or rendering when attempting to
# convert long strings to integers.


class LiquidValueError(LiquidSyntaxError):
    """Exception raised when a cast from str to int exceeds the length limit."""


class UndefinedError(Error):
    """Exception raised by the StrictUndefined type."""


class BreakLoop(LiquidInterrupt):
    """Exception raised when a BreakNode is rendered."""


class ContinueLoop(LiquidInterrupt):
    """Exception raised when a ContinueNode is rendered."""


class TemplateTraversalError(Error):
    """Exception raised when an AST node or expression can not be visited."""


class LiquidWarning(UserWarning):
    """Base warning."""


class LiquidSyntaxWarning(LiquidWarning):
    """Replaces LiquidSyntaxError when in WARN mode."""


class LiquidTypeWarning(LiquidWarning):
    """Replaces LiquidTypeError when in WARN mode."""


class FilterWarning(LiquidWarning):
    """Replaces filter exceptions when in WARN mode."""


WARNINGS: Dict[Type[Error], Type[LiquidWarning]] = {
    LiquidSyntaxError: LiquidSyntaxWarning,
    LiquidTypeError: LiquidTypeWarning,
    FilterArgumentError: FilterWarning,
    NoSuchFilterFunc: FilterWarning,
}


def lookup_warning(exc: Type[Error]) -> Type[LiquidWarning]:
    """Return a warning equivalent of the given exception."""
    return WARNINGS.get(exc, LiquidWarning)


def escape(val: Any) -> str:
    """A dummy escape function that always raises an exception."""
    raise Error("autoescape requires Markupsafe to be installed")


class Markup(str):
    """A dummy markup class that always raises an exception."""

    def __init__(self, _: object):
        super().__init__()
        raise Error("autoescape requires Markupsafe to be installed")

    def join(self, _: object) -> str:
        raise Error(
            "autoescape requires Markupsafe to be installed"
        )  # pragma: no cover

    # pylint: disable=missing-function-docstring
    def unescape(self) -> str:
        raise Error(
            "autoescape requires Markupsafe to be installed"
        )  # pragma: no cover

    def format(self, *args: Any, **kwargs: Any) -> str:
        raise Error(
            "autoescape requires Markupsafe to be installed"
        )  # pragma: no cover
