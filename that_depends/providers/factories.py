import typing

from that_depends.providers.base import AbstractFactory, AbstractProvider

T_co = typing.TypeVar("T_co")
P = typing.ParamSpec("P")


class Factory(AbstractFactory[T_co]):
    __slots__ = "_factory", "_args", "_kwargs", "_override"

    def __init__(self, factory, *args, **kwargs):
        super().__init__()
        self._factory = factory
        self._args = args
        self._kwargs = kwargs
        self._override = None

    async def async_resolve(self):
        if self._override:
            return typing.cast(T_co, self._override)

        return self._factory(
            *[await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
            **{k: await v.async_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
        )

    def sync_resolve(self):
        if self._override:
            return typing.cast(T_co, self._override)

        return self._factory(
            *[x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
            **{k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
        )


class AsyncFactory(AbstractFactory[T_co]):
    __slots__ = "_factory", "_args", "_kwargs", "_override"

    def __init__(self, factory, *args, **kwargs):
        self._factory = factory
        self._args = args
        self._kwargs = kwargs
        self._override = None

    async def async_resolve(self):
        if self._override:
            return typing.cast(T_co, self._override)

        return await self._factory(
            *[await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
            **{k: await v.async_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
        )

    def sync_resolve(self):
        msg = "AsyncFactory cannot be resolved synchronously"
        raise RuntimeError(msg)