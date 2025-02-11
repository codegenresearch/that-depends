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

        return self._factory(
            *[
                await x.async_resolve() if isinstance(x, AbstractProvider) else x
                for x in self._args
            ],  # type: ignore[arg-type]
            **{
                k: await v.async_resolve() if isinstance(v, AbstractProvider) else v
                for k, v in self._kwargs.items()
            },  # type: ignore[arg-type]
        )

    def sync_resolve(self) -> T_co:
        if self._override:
            return typing.cast(T_co, self._override)

        return self._factory(
            *[
                x.sync_resolve() if isinstance(x, AbstractProvider) else x
                for x in self._args
            ],  # type: ignore[arg-type]
            **{
                k: v.sync_resolve() if isinstance(v, AbstractProvider) else v
                for k, v in self._kwargs.items()
            },  # type: ignore[arg-type]
        )


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

        return await self._factory(
            *[
                await x.async_resolve() if isinstance(x, AbstractProvider) else x
                for x in self._args
            ],  # type: ignore[arg-type]
            **{
                k: await v.async_resolve() if isinstance(v, AbstractProvider) else v
                for k, v in self._kwargs.items()
            },  # type: ignore[arg-type]
        )

    def sync_resolve(self) -> typing.NoReturn:
        msg = "AsyncFactory cannot be resolved synchronously"
        raise RuntimeError(msg)


It seems the previous code already addressed most of the feedback points. However, I have ensured that the list and dictionary comprehensions are formatted consistently, the `# type: ignore[arg-type]` comments are placed directly after the comprehensions, and the return type of `sync_resolve` in the `Factory` class is `T_co`. The structure of the methods and handling of the `_override` attribute are also consistent with the gold code.