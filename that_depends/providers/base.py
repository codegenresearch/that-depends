import abc
import asyncio
import contextlib
import inspect
import typing
from contextlib import contextmanager


T_co = typing.TypeVar("T_co", covariant=True)
P = typing.ParamSpec("P")


class AttrGetter:
    def __init__(self, provider: 'AbstractProvider', attr_name: str):
        self._provider = provider
        self._attr_name = attr_name

    def __await__(self):
        async def inner():
            resolved = await self._provider.async_resolve()
            return getattr(resolved, self._attr_name)
        return inner().__await__()

    def __call__(self):
        resolved = self._provider.sync_resolve()
        return getattr(resolved, self._attr_name)


class AbstractProvider(typing.Generic[T_co], abc.ABC):
    """Abstract Provider Class."""

    def __init__(self) -> None:
        super().__init__()
        self._override: typing.Any = None

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

    def __getattr__(self, attr_name: str) -> AttrGetter:
        return AttrGetter(self, attr_name)

    @property
    def cast(self) -> T_co:
        """Returns self, but cast to the type of the provided value.

        This helps to pass providers as input to other providers while avoiding type checking errors:
        :example:

            class A: ...

            def create_b(a: A) -> B: ...

            class Container(BaseContainer):
                a_factory = Factory(A)
                b_factory1 = Factory(create_b, a_factory)  # works, but mypy (or pyright, etc.) will complain
                b_factory2 = Factory(create_b, a_factory.cast)  # works and passes type checking
        """
        return typing.cast(T_co, self)


class ResourceContext(typing.Generic[T_co]):
    __slots__ = "context_stack", "instance", "resolving_lock", "is_async"

    def __init__(self, is_async: bool) -> None:
        """Create a new ResourceContext instance.

        :param is_async: Whether the ResourceContext was created in an async context.
        For example within a ``async with container_context(): ...`` statement.
        :type is_async: bool
        """
        self.instance: T_co | None = None
        self.resolving_lock: typing.Final = asyncio.Lock()
        self.context_stack: contextlib.AsyncExitStack | contextlib.ExitStack | None = None
        self.is_async = is_async

    @staticmethod
    def is_context_stack_async(
        context_stack: contextlib.AsyncExitStack | contextlib.ExitStack | None,
    ) -> typing.TypeGuard[contextlib.AsyncExitStack]:
        return isinstance(context_stack, contextlib.AsyncExitStack)

    @staticmethod
    def is_context_stack_sync(
        context_stack: contextlib.AsyncExitStack | contextlib.ExitStack,
    ) -> typing.TypeGuard[contextlib.ExitStack]:
        return isinstance(context_stack, contextlib.ExitStack)

    async def tear_down(self) -> None:
        """Async tear down the context stack."""
        if self.context_stack is None:
            return

        if self.is_context_stack_async(self.context_stack):
            await self.context_stack.aclose()
        elif self.is_context_stack_sync(self.context_stack):
            self.context_stack.close()
        self.context_stack = None
        self.instance = None

    def sync_tear_down(self) -> None:
        """Sync tear down the context stack.

        :raises RuntimeError: If the context stack is async and the tear down is called in sync mode.
        """
        if self.context_stack is None:
            return

        if self.is_context_stack_sync(self.context_stack):
            self.context_stack.close()
            self.context_stack = None
            self.instance = None
        elif self.is_context_stack_async(self.context_stack):
            msg = "Cannot tear down async context in sync mode"
            raise RuntimeError(msg)


class AbstractResource(AbstractProvider[T_co], abc.ABC):
    def __init__(
        self,
        creator: typing.Callable[P, typing.AsyncIterator[T_co]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        super().__init__()
        if not inspect.isasyncgenfunction(creator):
            msg = f"{type(self).__name__} must be async generator function"
            raise RuntimeError(msg)

        self._creator: typing.Final = creator
        self._args: typing.Final = args
        self._kwargs: typing.Final = kwargs

    @abc.abstractmethod
    def _fetch_context(self) -> ResourceContext[T_co]: ...

    async def async_resolve(self) -> T_co:
        context = self._fetch_context()

        if context.instance is not None:
            return context.instance

        if not context.is_async:
            msg = "AsyncResource cannot be resolved in a sync context."
            raise RuntimeError(msg)

        # lock to prevent race condition while resolving
        async with context.resolving_lock:
            if context.instance is None:
                context.context_stack = contextlib.AsyncExitStack()
                context.instance = typing.cast(
                    T_co,
                    await context.context_stack.enter_async_context(
                        contextlib.asynccontextmanager(self._creator)(
                            *[await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
                            **{
                                k: await v.async_resolve() if isinstance(v, AbstractProvider) else v
                                for k, v in self._kwargs.items()
                            },
                        ),
                    ),
                )
            return typing.cast(T_co, context.instance)


class AbstractFactory(AbstractProvider[T_co], abc.ABC):
    """Abstract Factory Class."""

    @property
    def provider(self) -> typing.Callable[[], typing.Coroutine[typing.Any, typing.Any, T_co]]:
        return self.async_resolve

    @property
    def sync_provider(self) -> typing.Callable[[], T_co]:
        return self.sync_resolve


This code addresses the feedback by:
1. Adding the `AttrGetter` class for dynamic attribute access.
2. Implementing the `_override` mechanism with methods for setting and resetting the override.
3. Ensuring `sync_resolve` is an abstract method.
4. Including a context manager for overriding behavior.
5. Enhancing error handling with clear messages.
6. Using type guards to differentiate between async and sync contexts.
7. Implementing the `sync_tear_down` method for synchronous teardown of resources.