import inspect
import logging
import typing
import uuid
import warnings
from contextlib import AbstractAsyncContextManager, AbstractContextManager, asynccontextmanager, contextmanager
from contextvars import ContextVar, Token
from functools import wraps
from types import TracebackType
from that_depends.providers.base import AbstractResource, ResourceContext

logger: typing.Final = logging.getLogger(__name__)
T = typing.TypeVar("T")
P = typing.ParamSpec("P")
_CONTAINER_CONTEXT: typing.Final[ContextVar[dict[str, typing.Any]]] = ContextVar("CONTAINER_CONTEXT")
AppType = typing.TypeVar("AppType")
Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]
Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]
ASGIApp = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]
_ASYNC_CONTEXT_KEY: typing.Final[str] = "__ASYNC_CONTEXT__"

ContextType = dict[str, typing.Any]


@asynccontextmanager
async def container_context(initial_context_: ContextType | None = None) -> typing.AsyncGenerator[None, None]:
    """Manage the context of ContextResources for both sync and async tests."""
    context = initial_context_ or {}
    context[_ASYNC_CONTEXT_KEY] = True
    token = _CONTAINER_CONTEXT.set(context)
    try:
        yield
    finally:
        try:
            for context_item in reversed(_CONTAINER_CONTEXT.get().values()):
                if isinstance(context_item, ResourceContext):
                    if context_item.is_context_stack_async(context_item.context_stack):
                        await context_item.tear_down()
                    else:
                        context_item.sync_tear_down()
        finally:
            _CONTAINER_CONTEXT.reset(token)


@contextmanager
def sync_container_context(initial_context_: ContextType | None = None) -> typing.Generator[None, None, None]:
    """Manage the context of ContextResources for synchronous tests."""
    context = initial_context_ or {}
    context[_ASYNC_CONTEXT_KEY] = False
    token = _CONTAINER_CONTEXT.set(context)
    try:
        yield
    finally:
        try:
            for context_item in reversed(_CONTAINER_CONTEXT.get().values()):
                if isinstance(context_item, ResourceContext):
                    context_item.sync_tear_down()
        finally:
            _CONTAINER_CONTEXT.reset(token)


class DIContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app: typing.Final = app

    @container_context()
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        return await self.app(scope, receive, send)


def _get_container_context() -> dict[str, typing.Any]:
    try:
        return _CONTAINER_CONTEXT.get()
    except LookupError as exc:
        raise RuntimeError("Context is not set. Use container_context") from exc


def _is_container_context_async() -> bool:
    """Check if the current container context is async.

    :return: Whether the current container context is async.
    :rtype: bool
    """
    return typing.cast(bool, _get_container_context().get(_ASYNC_CONTEXT_KEY, False))


def fetch_context_item(key: str, default: typing.Any = None) -> typing.Any:  # noqa: ANN401
    return _get_container_context().get(key, default)


class ContextResource(AbstractResource[T]):
    __slots__ = (
        "_is_async",
        "_creator",
        "_args",
        "_kwargs",
        "_override",
        "_internal_name",
    )

    def __init__(
        self,
        creator: typing.Callable[P, typing.Iterator[T] | typing.AsyncIterator[T]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        super().__init__(creator, *args, **kwargs)
        self._internal_name: typing.Final = f"{creator.__name__}-{uuid.uuid4()}"

    def _fetch_context(self) -> ResourceContext[T]:
        container_context = _get_container_context()
        if resource_context := container_context.get(self._internal_name):
            return typing.cast(ResourceContext[T], resource_context)

        resource_context = ResourceContext(is_async=_is_container_context_async())
        container_context[self._internal_name] = resource_context
        return resource_context


class AsyncContextResource(ContextResource[T]):
    def __init__(
        self,
        creator: typing.Callable[P, typing.AsyncIterator[T]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        warnings.warn("AsyncContextResource is deprecated, use ContextResource instead", RuntimeWarning, stacklevel=1)
        super().__init__(creator, *args, **kwargs)