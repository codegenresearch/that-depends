import abc
import asyncio
import contextlib
import inspect
import typing
from contextlib import contextmanager


T = typing.TypeVar("T")
P = typing.ParamSpec("P")
T_co = typing.TypeVar("T_co", covariant=True)


class AbstractProvider(typing.Generic[T_co], abc.ABC):
    """Abstract Provider Class."""

    @abc.abstractmethod
    async def async_resolve(self) -> T_co:
        """Resolve dependency asynchronously."""

    @abc.abstractmethod
    def sync_resolve(self) -> T_co:
        """Resolve dependency synchronously."""

    async def __call__(self) -> T_co:
        return await self.async_resolve()

    def override(self, mock: object) -> None:
        self._override = mock

    @contextmanager
    def override_context(self, mock: object) -> typing.Iterator[None]:
        self.override(mock)
        try:
            yield
        finally:
            self.reset_override()

    def reset_override(self) -> None:
        self._override = None

    @property
    def cast(self) -> T_co:
        """Returns self, but cast to the type of the provided value.\n\n        This helps to pass providers as input to other providers while avoiding type checking errors:\n\n            class A: ...\n\n            def create_b(a: A) -> B: ...\n\n            class Container(BaseContainer):\n                a_factory = Factory(A)\n                b_factory1 = Factory(create_b, a_factory)  # works, but mypy (or pyright, etc.) will complain\n                b_factory2 = Factory(create_b, a_factory.cast)  # works and passes type checking\n        """
        return typing.cast(T_co, self)


class ResourceContext(typing.Generic[T_co]):
    __slots__ = "context_stack", "instance", "resolving_lock", "is_async"

    def __init__(
        self,
        is_async: bool,
        context_stack: contextlib.AsyncExitStack | contextlib.ExitStack | None = None,
        instance: T_co | None = None,
    ) -> None:
        self.instance = instance
        self.resolving_lock: typing.Final = asyncio.Lock()
        self.context_stack = context_stack
        self.is_async = is_async
        if not self.is_async and self.is_context_stack_async(self.context_stack):
            msg = "Cannot use async resource in sync mode."
            raise RuntimeError(msg)

    def is_context_stack_sync(
        self, _: contextlib.AsyncExitStack | contextlib.ExitStack | None
    ) -> typing.TypeGuard[contextlib.ExitStack]:
        return isinstance(_, contextlib.ExitStack)

    def is_context_stack_async(
        self, _: contextlib.AsyncExitStack | contextlib.ExitStack | None
    ) -> typing.TypeGuard[contextlib.AsyncExitStack]:
        return isinstance(_, contextlib.AsyncExitStack)

    async def tear_down(self) -> None:
        if self.context_stack is None:
            return

        try:
            if isinstance(self.context_stack, contextlib.AsyncExitStack):
                await self.context_stack.aclose()
            else:
                self.context_stack.close()
        finally:
            self.context_stack = None
            self.instance = None

    def sync_tear_down(self) -> None:
        if self.context_stack is None:
            return
        try:
            if self.is_context_stack_sync(self.context_stack):
                self.context_stack.close()
            else:
                raise RuntimeError("Cannot tear down async context in sync mode")
        finally:
            self.context_stack = None
            self.instance = None


class AbstractResource(AbstractProvider[T], abc.ABC):
    def __init__(
        self,
        creator: typing.Callable[P, typing.Iterator[T] | typing.AsyncIterator[T]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        if inspect.isasyncgenfunction(creator):
            self._is_async = True
        elif inspect.isgeneratorfunction(creator):
            self._is_async = False
        else:
            raise RuntimeError(f"{type(self).__name__} must be a generator function")

        self._creator: typing.Final = creator
        self._args: typing.Final = args
        self._kwargs: typing.Final = kwargs
        self._override = None

    @abc.abstractmethod
    def _fetch_context(self) -> ResourceContext[T]: ...

    async def async_resolve(self) -> T:
        if self._override:
            return typing.cast(T, self._override)

        context = self._fetch_context()

        if context.instance is not None:
            return context.instance

        if not context.is_async and self._is_async:
            raise RuntimeError("AsyncResource cannot be resolved in a sync context.")

        async with context.resolving_lock:
            if context.instance is None:
                context.context_stack = contextlib.AsyncExitStack() if self._is_async else contextlib.ExitStack()
                context.instance = await context.context_stack.enter_async_context(
                    contextlib.asynccontextmanager(self._creator)(
                        *[await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
                        **{k: await v.async_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
                    )
                ) if self._is_async else context.context_stack.enter_context(
                    contextlib.contextmanager(self._creator)(
                        *[x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
                        **{k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
                    )
                )
        return typing.cast(T, context.instance)

    def sync_resolve(self) -> T:
        if self._override:
            return typing.cast(T, self._override)

        context = self._fetch_context()
        if context.instance is not None:
            return context.instance

        if self._is_async:
            raise RuntimeError("AsyncResource cannot be resolved synchronously")

        context.context_stack = contextlib.ExitStack()
        context.instance = context.context_stack.enter_context(
            contextlib.contextmanager(self._creator)(
                *[x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
                **{k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
            )
        )
        return typing.cast(T, context.instance)