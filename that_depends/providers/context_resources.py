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


@contextmanager
def sync_container_context(initial_context: ContextType | None = None) -> typing.Iterator[ContextType]:
    """Manage the context of ContextResources synchronously."""
    initial_context = initial_context or {}
    initial_context[_ASYNC_CONTEXT_KEY] = False
    context_token = _CONTAINER_CONTEXT.set(initial_context)
    try:
        yield _CONTAINER_CONTEXT.get()
    finally:
        try:
            for context_item in reversed(_CONTAINER_CONTEXT.get().values()):
                if isinstance(context_item, ResourceContext):
                    context_item.sync_tear_down()
        finally:
            _CONTAINER_CONTEXT.reset(context_token)


@asynccontextmanager
async def container_context(initial_context: ContextType | None = None) -> typing.AsyncIterator[ContextType]:
    """Manage the context of ContextResources asynchronously."""
    initial_context = initial_context or {}
    initial_context[_ASYNC_CONTEXT_KEY] = True
    context_token = _CONTAINER_CONTEXT.set(initial_context)
    try:
        yield _CONTAINER_CONTEXT.get()
    finally:
        try:
            for context_item in reversed(_CONTAINER_CONTEXT.get().values()):
                if isinstance(context_item, ResourceContext):
                    if context_item.is_context_stack_async(context_item.context_stack):
                        await context_item.tear_down()
                    else:
                        context_item.sync_tear_down()
        finally:
            _CONTAINER_CONTEXT.reset(context_token)


def _get_container_context() -> dict[str, typing.Any]:
    try:
        return _CONTAINER_CONTEXT.get()
    except LookupError:
        raise RuntimeError("Context is not set. Use container_context or sync_container_context")


def _is_container_context_async() -> bool:
    """Check if the current container context is async."""
    return _get_container_context().get(_ASYNC_CONTEXT_KEY, False)


def fetch_context_item(key: str, default: typing.Any = None) -> typing.Any:
    return _get_container_context().get(key, default)


class DIContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app: typing.Final = app

    @container_context()
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        return await self.app(scope, receive, send)


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


This code refactors the context management to use `contextlib.contextmanager` and `contextlib.asynccontextmanager` decorators, simplifies the context management logic, and ensures that the error messages are clear and concise. It also removes redundant methods and aligns with the expected structure and functionality.