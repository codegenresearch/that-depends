import abc
import asyncio
import inspect
import typing
from contextlib import contextmanager, AsyncExitStack, ExitStack


T_co = typing.TypeVar("T_co", covariant=True)
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


class ResourceContext(typing.Generic[T_co]):
    __slots__ = "context_stack", "instance", "resolving_lock", "is_async"

    def __init__(self, is_async: bool) -> None:
        """Create a new ResourceContext instance.

        :param is_async: Whether the ResourceContext was created in an async context.
        For example within a ``async with container_context(): ...`` statement.
        :type is_async: bool
        """
        self.instance: T_co | None = None
        self.resolving_lock: asyncio.Lock = asyncio.Lock()
        self.context_stack: AsyncExitStack | ExitStack | None = None
        self.is_async = is_async

    def tear_down(self) -> None:
        """Tear down the context stack."""
        if self.context_stack is None:
            return

        if isinstance(self.context_stack, AsyncExitStack):
            asyncio.create_task(self.context_stack.aclose())
        elif isinstance(self.context_stack, ExitStack):
            self.context_stack.close()
        self.context_stack = None
        self.instance = None


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
            msg = f"{type(self).__name__} must be generator function"
            raise RuntimeError(msg)

        self._creator: typing.Final = creator
        self._args: typing.Final = args
        self._kwargs: typing.Final = kwargs
        self._override = None

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
            msg = "AsyncResource cannot be resolved in an sync context."
            raise RuntimeError(msg)

        # lock to prevent race condition while resolving
        async with context.resolving_lock:
            if context.instance is None:
                if self._is_creator_async(self._creator):
                    context.context_stack = AsyncExitStack()
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
                    context.context_stack = ExitStack()
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
            context.context_stack = ExitStack()
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

    def __init__(self, factory: typing.Callable[P, T_co], *args: P.args, **kwargs: P.kwargs) -> None:
        super().__init__()
        self._factory: typing.Final = factory
        self._args: typing.Final = args
        self._kwargs: typing.Final = kwargs
        self._override = None

    async def async_resolve(self) -> T_co:
        if self._override:
            return typing.cast(T_co, self._override)

        return self._factory(
            *[await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
            **{k: await v.async_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
        )

    def sync_resolve(self) -> T_co:
        if self._override:
            return typing.cast(T_co, self._override)

        return self._factory(
            *[x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
            **{k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
        )