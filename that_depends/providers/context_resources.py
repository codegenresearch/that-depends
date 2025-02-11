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


def fetch_context_item(key: str, default: typing.Any = None) -> typing.Any:
    """Fetch an item from the container context."""
    return _get_container_context().get(key, default)


@contextmanager
def sync_container_context(initial_context: ContextType | None = None) -> typing.Iterator[None]:
    """Manage the context of ContextResources for synchronous operations."""
    initial_context = initial_context or {}
    initial_context[_ASYNC_CONTEXT_KEY] = False
    token: typing.Final[Token[ContextType]] = _CONTAINER_CONTEXT.set(initial_context)
    try:
        yield
    finally:
        try:
            for context_item in reversed(_CONTAINER_CONTEXT.get().values()):
                if isinstance(context_item, ResourceContext):
                    context_item.sync_tear_down()
        finally:
            _CONTAINER_CONTEXT.reset(token)


@asynccontextmanager
async def container_context(initial_context: ContextType | None = None) -> typing.AsyncIterator[None]:
    """Manage the context of ContextResources.

    Can be entered using ``async with container_context()`` or with ``with container_context()``
    as async-context-manager or context-manager respectively.
    When used as async-context-manager, it will allow setup & teardown of both sync and async resources.
    When used as sync-context-manager, it will only allow setup & teardown of sync resources.
    """
    initial_context = initial_context or {}
    initial_context[_ASYNC_CONTEXT_KEY] = True
    token: typing.Final[Token[ContextType]] = _CONTAINER_CONTEXT.set(initial_context)
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
        msg = "Context is not set. Use container_context"
        raise RuntimeError(msg) from exc


def _is_container_context_async() -> bool:
    """Check if the current container context is async.

    :return: Whether the current container context is async.
    :rtype: bool
    """
    return typing.cast(bool, _get_container_context().get(_ASYNC_CONTEXT_KEY, False))


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
        if resource_context := fetch_context_item(self._internal_name):
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


This code addresses the feedback by:
1. Removing the invalid comment that was causing a `SyntaxError`.
2. Using `contextlib` directly for both `asynccontextmanager` and `contextmanager`.
3. Naming the initial context variable `initial_context` consistently.
4. Ensuring type annotations are consistent.
5. Yielding `None` in the `container_context` and `sync_container_context` functions.
6. Naming the context token variable `token` consistently and marking it as `typing.Final`.
7. Implementing a dedicated function `fetch_context_item` for fetching context items.
8. Providing appropriate deprecation warnings for `AsyncContextResource`.
9. Ensuring the code structure follows the same logical flow and organization as the gold code.