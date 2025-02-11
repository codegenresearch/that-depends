import asyncio
import typing

from that_depends.providers import AttrGetter
from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)
P = typing.ParamSpec("P")


class Singleton(AbstractProvider[T_co]):
    __slots__ = "_factory", "_args", "_kwargs", "_override", "_instance", "_resolving_lock"

    def __init__(self, factory: type[T_co] | typing.Callable[P, T_co], *args: P.args, **kwargs: P.kwargs) -> None:
        super().__init__()
        self._factory = factory
        self._args = args
        self._kwargs = kwargs
        self._override = None
        self._instance = None
        self._resolving_lock = asyncio.Lock()

    def __getattr__(self, attr_name: str) -> typing.Any:
        if attr_name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{attr_name}'")
        return AttrGetter(provider=self, attr_name=attr_name)

    async def async_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        if self._instance is not None:
            return self._instance

        async with self._resolving_lock:
            if self._instance is None:
                self._instance = await self._create_instance()
            return self._instance

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        if self._instance is None:
            self._instance = self._create_instance(sync=True)
        return self._instance

    async def _create_instance(self) -> T_co:
        return self._factory(
            *[await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
            **{k: await v.async_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
        )

    def _create_instance(self, sync: bool = False) -> T_co:
        if sync:
            return self._factory(
                *[x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
                **{k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
            )
        raise RuntimeError("Synchronous instance creation called without sync=True")

    async def tear_down(self) -> None:
        self._instance = None