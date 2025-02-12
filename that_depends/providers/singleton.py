import asyncio
import typing

from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)
P = typing.ParamSpec("P")


class Singleton(AbstractProvider[T_co]):
    __slots__ = "_factory", "_args", "_kwargs", "_override", "_instance", "_resolving_lock"

    def __init__(self, factory: typing.Callable[P, T_co], *args: P.args, **kwargs: P.kwargs) -> None:
        super().__init__()
        self._factory: typing.Final[typing.Callable[P, T_co]] = factory
        self._args: typing.Final[tuple] = args
        self._kwargs: typing.Final[dict[str, typing.Any]] = kwargs
        self._instance: T_co | None = None
        self._resolving_lock: typing.Final[asyncio.Lock] = asyncio.Lock()

    async def async_resolve(self) -> T_co:
        if self._override is not None:
            return self._override  # type: ignore[return-value]

        if self._instance is not None:
            return self._instance

        async with self._resolving_lock:
            if self._instance is None:
                self._instance = await self._resolve_instance()
            return self._instance

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return self._override  # type: ignore[return-value]

        if self._instance is None:
            self._instance = self._resolve_instance_sync()
        return self._instance

    async def _resolve_instance(self) -> T_co:
        resolved_args = await asyncio.gather(
            *(x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args)
        )
        resolved_kwargs = await asyncio.gather(
            *(v.async_resolve() if isinstance(v, AbstractProvider) else v for v in self._kwargs.values())
        )
        return self._factory(*resolved_args, **dict(zip(self._kwargs.keys(), resolved_kwargs)))

    def _resolve_instance_sync(self) -> T_co:
        resolved_args = [
            x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args
        ]
        resolved_kwargs = {
            k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()
        }
        return self._factory(*resolved_args, **resolved_kwargs)

    async def tear_down(self) -> None:
        self._instance = None