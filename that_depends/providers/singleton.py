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
        self._factory: typing.Final = factory
        self._args: typing.Final = args
        self._kwargs: typing.Final = kwargs
        self._override = None
        self._instance: T_co | None = None
        self._resolving_lock: typing.Final = asyncio.Lock()

    def __getattr__(self, attr_name: str) -> typing.Any:
        if attr_name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{attr_name}'")
        return AttrGetter(provider=self, attr_name=attr_name)

    async def async_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        async with self._resolving_lock:
            if self._instance is None:
                resolved_args = [
                    await x.async_resolve() if isinstance(x, AbstractProvider) else x
                    for x in self._args
                ]
                resolved_kwargs = {
                    k: await v.async_resolve() if isinstance(v, AbstractProvider) else v
                    for k, v in self._kwargs.items()
                }
                self._instance = self._factory(*resolved_args, **resolved_kwargs)
            return self._instance

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        if self._instance is None:
            resolved_args = [
                x.sync_resolve() if isinstance(x, AbstractProvider) else x
                for x in self._args
            ]
            resolved_kwargs = {
                k: v.sync_resolve() if isinstance(v, AbstractProvider) else v
                for k, v in self._kwargs.items()
            }
            self._instance = self._factory(*resolved_args, **resolved_kwargs)
        return self._instance

    async def tear_down(self) -> None:
        self._instance = None