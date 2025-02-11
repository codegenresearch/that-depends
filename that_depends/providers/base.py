import abc
import asyncio
import contextlib
import inspect
import typing
from contextlib import contextmanager


T_co = typing.TypeVar("T_co", covariant=True)
R = typing.TypeVar("R")
P = typing.ParamSpec("P")


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
        """Override the provider with a mock object."""
        self._override = mock

    @contextmanager
    def override_context(self, mock: object) -> typing.Iterator[None]:
        """Context manager to temporarily override the provider with a mock object."""
        self.override(mock)
        try:
            yield
        finally:
            self.reset_override()

    def reset_override(self) -> None:
        """Reset the override to None."""
        self._override = None

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
    def is_context_stack_async(context_stack: contextlib.AsyncExitStack | contextlib.ExitStack | None) -> bool:
        """Check if the context stack is an instance of AsyncExitStack."""
        return isinstance(context_stack, contextlib.AsyncExitStack)

    @staticmethod
    def is_context_stack_sync(context_stack: contextlib.AsyncExitStack | contextlib.ExitStack | None) -> bool:
        """Check if the context stack is an instance of ExitStack."""
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
            raise RuntimeError("Cannot tear down async context in sync mode")


class AbstractResource(AbstractProvider[T_co], abc.ABC):
    def __init__(
        self,
        creator: typing.Callable[P, typing.Iterator[T_co] | typing.AsyncIterator[T_co]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        super().__init__()
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

    def _is_creator_async(
        self, _: typing.Callable[P, typing.Iterator[T_co] | typing.AsyncIterator[T_co]]
    ) -> typing.TypeGuard[typing.Callable[P, typing.AsyncIterator[T_co]]]:
        """Check if the creator is an async generator function."""
        return self._is_async

    def _is_creator_sync(
        self, _: typing.Callable[P, typing.Iterator[T_co] | typing.AsyncIterator[T_co]]
    ) -> typing.TypeGuard[typing.Callable[P, typing.Iterator[T_co]]]:
        """Check if the creator is a sync generator function."""
        return not self._is_async

    @abc.abstractmethod
    def _fetch_context(self) -> ResourceContext[T_co]:
        """Fetch the resource context."""

    async def async_resolve(self) -> T_co:
        """Resolve the resource asynchronously."""
        if self._override:
            return typing.cast(T_co, self._override)

        context = self._fetch_context()

        if context.instance is not None:
            return context.instance

        if not context.is_async and self._is_creator_async(self._creator):
            raise RuntimeError("AsyncResource cannot be resolved in an sync context.")

        # lock to prevent race condition while resolving
        async with context.resolving_lock:
            if context.instance is None:
                if self._is_creator_async(self._creator):
                    context.context_stack = contextlib.AsyncExitStack()
                    context.instance = typing.cast(
                        T_co,
                        await context.context_stack.enter_async_context(
                            contextlib.asynccontextmanager(self._creator)(
                                *[
                                    await x.async_resolve() if isinstance(x, AbstractProvider) else x
                                    for x in self._args
                                ],
                                **{
                                    k: await v.async_resolve() if isinstance(v, AbstractProvider) else v
                                    for k, v in self._kwargs.items()
                                },
                            ),
                        ),
                    )
                elif self._is_creator_sync(self._creator):
                    context.context_stack = contextlib.ExitStack()
                    context.instance = context.context_stack.enter_context(
                        contextlib.contextmanager(self._creator)(
                            *[
                                x.sync_resolve() if isinstance(x, AbstractProvider) else x
                                for x in self._args
                            ],
                            **{
                                k: v.sync_resolve() if isinstance(v, AbstractProvider) else v
                                for k, v in self._kwargs.items()
                            },
                        ),
                    )
            return typing.cast(T_co, context.instance)

    def sync_resolve(self) -> T_co:
        """Resolve the resource synchronously."""
        if self._override:
            return typing.cast(T_co, self._override)

        context = self._fetch_context()
        if context.instance is not None:
            return context.instance

        if self._is_creator_async(self._creator):
            raise RuntimeError("AsyncResource cannot be resolved synchronously")

        if self._is_creator_sync(self._creator):
            context.context_stack = contextcontextlib.ExitStack()
            context.instance = context.context_stack.enter_context(
                contextlib.contextmanager(self._creator)(
                    *[
                        x.sync_resolve() if isinstance(x, AbstractProvider) else x
                        for x in self._args
                    ],
                    **{
                        k: v.sync_resolve() if isinstance(v, AbstractProvider) else v
                        for k, v in self._kwargs.items()
                    },
                ),
            )
        return typing.cast(T_co, context.instance)


class AbstractFactory(AbstractProvider[T_co], abc.ABC):
    """Abstract Factory Class."""

    @property
    def provider(self) -> typing.Callable[[], typing.Coroutine[typing.Any, typing.Any, T_co]]:
        """Return the async resolve method as a provider."""
        return self.async_resolve

    @property
    def sync_provider(self) -> typing.Callable[[], T_co]:
        """Return the sync resolve method as a provider."""
        return self.sync_resolve


**Corrections Made:**
1. **Error Messages**: Updated the error messages to match the expected phrases in the tests.
2. **Type Checking**: Added type hints to the `is_context_stack_async` and `is_context_stack_sync` methods.
3. **Context Stack Handling**: Ensured the context stack handling logic is consistent.
4. **Async and Sync Logic**: Ensured the logic for resolving dependencies is consistent.
5. **Use of `typing.cast`**: Ensured consistent use of `typing.cast`.
6. **Code Formatting**: Ensured consistent code formatting and spacing.