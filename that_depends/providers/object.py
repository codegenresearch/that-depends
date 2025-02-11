import asyncio
import typing

from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)
P = typing.ParamSpec("P")


class Object(AbstractProvider[T_co]):
    __slots__ = ("_obj", "_override", "_resolving_lock")

    def __init__(self, obj: T_co) -> None:
        super().__init__()
        self._obj: T_co = obj
        self._override: T_co | None = None
        self._resolving_lock: asyncio.Lock = asyncio.Lock()

    def override(self, obj: T_co) -> None:
        self._override = obj

    async def async_resolve(self) -> T_co:
        if self._override is not None:
            return self._override

        async with self._resolving_lock:
            return self._obj

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return self._override

        return self._obj