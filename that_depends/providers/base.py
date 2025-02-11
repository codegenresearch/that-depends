import abc
import asyncio
import contextlib
import inspect
import typing
from contextlib import contextmanager
from operator import attrgetter


T_co = typing.TypeVar("T_co", covariant=True)
R = typing.TypeVar("R")
P = typing.ParamSpec("P")


class AbstractProvider(typing.Generic[T_co], abc.ABC):
    """Abstract Provider Class."""

    __slots__ = "_override"

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

    def __getattr__(self, attr_name: str) -> typing.Any:
        """Dynamic attribute access."""
        if attr_name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{attr_name}'")
        return AttrGetter(provider=self, attr_name=attr_name)


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
        self.is_async: typing.Final = is_async

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
        creator: typing.Callable[P, typing.Iterator[T_co] | typing.AsyncIterator[T_co]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        super().__init__()
        if inspect.isasyncgenfunction(creator):
            self._is_async: typing.Final = True
        elif inspect.isgeneratorfunction(creator):
            self._is_async: typing.Final = False
        else:
            msg = f"{type(self).__name__} must be a generator function"
            raise RuntimeError(msg)

        self._creator: typing.Final = creator
        self._args: typing.Final = args
        self._kwargs: typing.Final = kwargs

    def _is_creator_async(
        self, _: typing.Callable[P, typing.Iterator[T_co] | typing.AsyncIterator[T_co]]
    ) -> typing.TypeGuard[typing.Callable[P, typing.AsyncIterator[T_co]]]:
        return self._is_async

    def _is_creator_sync(
        self, _: typing.Callable[P, typing.Iterator[T_co] | typing.AsyncIterator[T_co]]
    ) -> typing.TypeGuard[typing.Callable[P, typing.Iterator[T_co]]]:
        return not self._is_async

    @abc.abstractmethod
    def _fetch_context(self) -> ResourceContext[T_co]: ...

    async def async_resolve(self) -> T_co:
        if self._override:
            return typing.cast(T_co, self._override)

        context = self._fetch_context()

        if context.instance is not None:
            return context.instance

        if not context.is_async and self._is_creator_async(self._creator):
            msg = "AsyncResource cannot be resolved in a sync context."
            raise RuntimeError(msg)

        # lock to prevent race condition while resolving
        async with context.resolving_lock:
            if context.instance is None:
                if self._is_creator_async(self._creator):
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
                elif self._is_creator_sync(self._creator):
                    context.context_stack = contextlib.ExitStack()
                    context.instance = context.context_stack.enter_context(
                        contextlib.contextmanager(self._creator)(
                            *[x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
                            **{k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
                        ),
                    )
            return typing.cast(T_co, context.instance)

    def sync_resolve(self) -> T_co:
        if self._override:
            return typing.cast(T_co, self._override)

        context = self._fetch_context()
        if context.instance is not None:
            return context.instance

        if self._is_creator_async(self._creator):
            msg = "AsyncResource cannot be resolved synchronously"
            raise RuntimeError(msg)

        if self._is_creator_sync(self._creator):
            context.context_stack = contextlib.ExitStack()
            context.instance = context.context_stack.enter_context(
                contextlib.contextmanager(self._creator)(
                    *[x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
                    **{k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
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


class AttrGetter(AbstractProvider[T_co]):
    """Provider that resolves an attribute from another provider."""

    __slots__ = "_provider", "_attr_name"

    def __init__(self, provider: AbstractProvider[object], attr_name: str) -> None:
        super().__init__()
        self._provider: typing.Final = provider
        self._attr_name: typing.Final = attr_name

    async def async_resolve(self) -> T_co:
        resolved = await self._provider.async_resolve()
        return _get_value_from_object_by_dotted_path(resolved, self._attr_name)

    def sync_resolve(self) -> T_co:
        resolved = self._provider.sync_resolve()
        return _get_value_from_object_by_dotted_path(resolved, self._attr_name)


def _get_value_from_object_by_dotted_path(obj: object, dotted_path: str) -> typing.Any:
    """Helper function to resolve attributes by a dotted path."""
    attrs = dotted_path.split('.')
    value = obj
    for attr in attrs:
        value = attrgetter(attr)(value)
    return value


This code addresses the feedback by:
1. Removing the invalid comment that caused the `SyntaxError`.
2. Ensuring that the `__getattr__` method returns an instance of `AttrGetter` with the correct parameters.
3. Ensuring consistent error messages and type annotations.
4. Implementing the helper function `_get_value_from_object_by_dotted_path` using `attrgetter` for efficiency.
5. Ensuring the `AttrGetter` class has the correct `__slots__` and handles dynamic attribute access properly.
6. Ensuring clear and consistent documentation.
7. Using `typing.Final` for variables that should not be reassigned after initialization.
8. Ensuring consistent handling of async and sync contexts.