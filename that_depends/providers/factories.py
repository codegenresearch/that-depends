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
            *[await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],  # type: ignore[arg-type]
            **{k: await v.async_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},  # type: ignore[arg-type]
        )

    def sync_resolve(self) -> T_co:
        if self._override:
            return typing.cast(T_co, self._override)

        return self._factory(
            *[x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],  # type: ignore[arg-type]
            **{k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},  # type: ignore[arg-type]
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
            *[await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],  # type: ignore[arg-type]
            **{k: await v.async_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},  # type: ignore[arg-type]
        )

    def sync_resolve(self) -> typing.NoReturn:
        msg = "AsyncFactory cannot be resolved synchronously"
        raise RuntimeError(msg)


I have addressed the feedback by:
1. Ensuring that the list and dictionary comprehensions have their opening brackets and braces on the same line as the `*` and `**` operators.
2. Placing the `# type: ignore[arg-type]` comments directly after the comprehensions.
3. Ensuring consistency in method definitions and return types.