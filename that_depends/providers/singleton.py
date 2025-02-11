import asyncio
import typing

from that_depends.providers.base import AbstractProvider


class Singleton(AbstractProvider):
    __slots__ = "_factory", "_args", "_kwargs", "_override", "_instance", "_resolving_lock"

    def __init__(self, factory: typing.Callable, *args, **kwargs) -> None:
        super().__init__()
        self._factory = factory
        self._args = args
        self._kwargs = kwargs
        self._instance = None
        self._resolving_lock = asyncio.Lock()

    async def async_resolve(self) -> typing.Any:
        if self._override is not None:
            return self._override

        if self._instance is not None:
            return self._instance

        # lock to prevent resolving several times
        async with self._resolving_lock:
            if self._instance is None:
                self._instance = self._factory(
                    *[
                        await x.async_resolve() if isinstance(x, AbstractProvider) else x
                        for x in self._args
                    ],
                    **{
                        k: await v.async_resolve() if isinstance(v, AbstractProvider) else v
                        for k, v in self._kwargs.items()
                    },
                )
            return self._instance

    def sync_resolve(self) -> typing.Any:
        if self._override is not None:
            return self._override

        if self._instance is None:
            self._instance = self._factory(
                *[
                    x.sync_resolve() if isinstance(x, AbstractProvider) else x
                    for x in self._args
                ],
                **{
                    k: v.sync_resolve() if isinstance(v, AbstractProvider) else v
                    for k, v in self._kwargs.items()
                },
            )
        return self._instance

    async def tear_down(self) -> None:
        if self._instance is not None:
            self._instance = None