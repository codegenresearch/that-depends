import typing

from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)
P = typing.ParamSpec("P")


class Object(AbstractProvider[T_co]):
    __slots__ = ("_obj", "_override")

    def __init__(self, obj: T_co) -> None:
        super().__init__()
        self._obj: T_co = obj
        self._override: T_co | None = None

    def set_override(self, override: T_co) -> None:
        self._override = override

    async def async_resolve(self) -> T_co:
        return self.sync_resolve()

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)
        return self._obj