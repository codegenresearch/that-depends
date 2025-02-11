import typing

from that_depends.providers.base import AbstractFactory, AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)
P = typing.ParamSpec("P")


class Factory(AbstractFactory[T_co]):
    __slots__ = "_factory", "_args", "_kwargs", "_override"

    def __init__(self, factory: typing.Callable[P, T_co], *args: P.args, **kwargs: P.kwargs) -> None:
        super().__init__()
        self._factory: typing.Final = factory
        self._args: typing.Final = args
        self._kwargs: typing.Final = kwargs

    async def async_resolve(self) -> T_co:
        if self._override:
            return typing.cast(T_co, self._override)

        resolved_args = [
            await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args  # type: ignore[arg-type]
        ]
        resolved_kwargs = {
            k: await v.async_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()  # type: ignore[arg-type]
        }
        return self._factory(*resolved_args, **resolved_kwargs)

    def sync_resolve(self) -> T_co:
        if self._override:
            return typing.cast(T_co, self._override)

        resolved_args = [x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args]
        resolved_kwargs = {k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()}
        return self._factory(*resolved_args, **resolved_kwargs)


class AsyncFactory(AbstractFactory[T_co]):
    __slots__ = "_factory", "_args", "_kwargs", "_override"

    def __init__(self, factory: typing.Callable[P, typing.Awaitable[T_co]], *args: P.args, **kwargs: P.kwargs) -> None:
        super().__init__()
        self._factory: typing.Final = factory
        self._args: typing.Final = args
        self._kwargs: typing.Final = kwargs

    async def async_resolve(self) -> T_co:
        if self._override:
            return typing.cast(T_co, self._override)

        resolved_args = [
            await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args  # type: ignore[arg-type]
        ]
        resolved_kwargs = {
            k: await v.async_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()  # type: ignore[arg-type]
        }
        return await self._factory(*resolved_args, **resolved_kwargs)

    def sync_resolve(self) -> typing.NoReturn:
        msg = "AsyncFactory cannot be resolved synchronously. Use async_resolve instead."
        raise RuntimeError(msg)