import inspect
import logging
import typing
import uuid
import warnings
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from contextvars import ContextVar, Token
from functools import wraps
from types import TracebackType

from that_depends.providers.base import AbstractResource, ResourceContext


logger: typing.Final[logging.Logger] = logging.getLogger(__name__)
T_co = typing.TypeVar("T_co", covariant=True)
P = typing.ParamSpec("P")
_CONTAINER_CONTEXT: typing.Final[ContextVar[dict[str, typing.Any]]] = ContextVar("CONTAINER_CONTEXT")
AppType = typing.TypeVar("AppType", covariant=True)
Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]
Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]
ASGIApp = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]
_ASYNC_CONTEXT_KEY: typing.Final[str] = "__ASYNC_CONTEXT__"

ContextType = dict[str, typing.Any]


class container_context(  # noqa: N801
    AbstractAsyncContextManager[ContextType], AbstractContextManager[ContextType]
):
    """Manage the context of ContextResources.\n\n    Can be entered using ``async with container_context()`` or with ``with container_context()``\n    as async-context-manager or context-manager respectively.\n    When used as async-context-manager, it will allow setup & teardown of both sync and async resources.\n    When used as sync-context-manager, it will only allow setup & teardown of sync resources.\n    """

    __slots__ = "_initial_context", "_context_token"

    def __init__(self, initial_context: ContextType | None = None) -> None:
        self._initial_context: ContextType = initial_context or {}
        self._context_token: Token[ContextType] | None = None

    def __enter__(self) -> ContextType:
        self._initial_context[_ASYNC_CONTEXT_KEY] = False
        return self._enter()

    async def __aenter__(self) -> ContextType:
        self._initial_context[_ASYNC_CONTEXT_KEY] = True
        return self._enter()

    def _enter(self) -> ContextType:
        self._context_token = _CONTAINER_CONTEXT.set(self._initial_context or {})
        return _CONTAINER_CONTEXT.get()

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        if self._context_token is None:
            msg = "Context is not set, call ``__enter__`` first"
            raise RuntimeError(msg)

        try:
            for context_item in reversed(_CONTAINER_CONTEXT.get().values()):
                if isinstance(context_item, ResourceContext):
                    # we don't need to handle the case where the ResourceContext is async\n                    context_item.sync_tear_down()\n\n        finally:\n            _CONTAINER_CONTEXT.reset(self._context_token)\n\n    async def __aexit__(\n        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, traceback: TracebackType | None\n    ) -> None:\n        if self._context_token is None:\n            msg = "Context is not set, call ``__aenter__`` first"\n            raise RuntimeError(msg)\n\n        try:\n            for context_item in reversed(_CONTAINER_CONTEXT.get().values()):\n                if not isinstance(context_item, ResourceContext):\n                    continue\n\n                if context_item.is_context_stack_async(context_item.context_stack):\n                    await context_item.tear_down()\n                else:\n                    context_item.sync_tear_down()\n        finally:\n            _CONTAINER_CONTEXT.reset(self._context_token)\n\n    def __call__(self, func: typing.Callable[P, T_co]) -> typing.Callable[P, T_co]:\n        if inspect.iscoroutinefunction(func):\n\n            @wraps(func)\n            async def _async_inner(*args: P.args, **kwargs: P.kwargs) -> T_co:\n                async with container_context(self._initial_context):\n                    return await func(*args, **kwargs)  # type: ignore[no-any-return]\n\n            return typing.cast(typing.Callable[P, T_co], _async_inner)\n\n        @wraps(func)\n        def _sync_inner(*args: P.args, **kwargs: P.kwargs) -> T_co:\n            with container_context(self._initial_context):\n                return func(*args, **kwargs)\n\n        return _sync_inner\n\n\nclass DIContextMiddleware:\n    def __init__(self, app: ASGIApp) -> None:\n        self.app: typing.Final[ASGIApp] = app\n\n    @container_context()\n    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:\n        return await self.app(scope, receive, send)\n\n\ndef _get_container_context() -> dict[str, typing.Any]:\n    try:\n        return _CONTAINER_CONTEXT.get()\n    except LookupError as exc:\n        msg = "Context is not set. Use container_context"\n        raise RuntimeError(msg) from exc\n\n\ndef _is_container_context_async() -> bool:\n    """Check if the current container context is async.\n\n    :return: Whether the current container context is async.\n    :rtype: bool\n    """\n    return typing.cast(bool, _get_container_context().get(_ASYNC_CONTEXT_KEY, False))\n\n\ndef fetch_context_item(key: str, default: typing.Any = None) -> typing.Any:  # noqa: ANN401\n    return _get_container_context().get(key, default)\n\n\nclass ContextResource(AbstractResource[T_co]):\n    __slots__ = (\n        "_is_async",\n        "_creator",\n        "_args",\n        "_kwargs",\n        "_override",\n        "_internal_name",\n    )\n\n    def __init__(\n        self,\n        creator: typing.Callable[P, typing.Iterator[T_co] | typing.AsyncIterator[T_co]],\n        *args: P.args,\n        **kwargs: P.kwargs,\n    ) -> None:\n        super().__init__(creator, *args, **kwargs)\n        self._internal_name: typing.Final[str] = f"{creator.__name__}-{uuid.uuid4()}"\n\n    def _fetch_context(self) -> ResourceContext[T_co]:\n        container_context = _get_container_context()\n        if resource_context := container_context.get(self._internal_name):\n            return typing.cast(ResourceContext[T_co], resource_context)\n\n        resource_context = ResourceContext[T_co](is_async=_is_container_context_async())\n        container_context[self._internal_name] = resource_context\n        return resource_context\n\n\nclass AsyncContextResource(ContextResource[T_co]):\n    def __init__(\n        self,\n        creator: typing.Callable[P, typing.AsyncIterator[T_co]],\n        *args: P.args,\n        **kwargs: P.kwargs,\n    ) -> None:\n        warnings.warn("AsyncContextResource is deprecated, use ContextResource instead", RuntimeWarning, stacklevel=1)\n        super().__init__(creator, *args, **kwargs)