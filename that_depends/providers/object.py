import typing
import logging

from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)
P = typing.ParamSpec("P")

logger = logging.getLogger(__name__)


class Object(AbstractProvider[T_co]):
    __slots__ = ("_obj",)

    def __init__(self, obj: T_co) -> None:
        super().__init__()
        self._obj: typing.Final = obj
        logger.debug(f"Object provider initialized with object: {obj}")

    async def async_resolve(self) -> T_co:
        logger.debug(f"Async resolving object: {self._obj}")
        return self._obj

    def sync_resolve(self) -> T_co:
        logger.debug(f"Sync resolving object: {self._obj}")
        return self._obj