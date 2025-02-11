import typing
import asyncio

from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)


class Selector(AbstractProvider[T_co]):
    __slots__ = "_selector", "_providers", "_resolved_provider"

    def __init__(self, selector: typing.Callable[[], str], **providers: AbstractProvider[T_co]) -> None:
        super().__init__()
        self._selector: typing.Final = selector
        self._providers: typing.Final = providers
        self._resolved_provider: T_co | None = None

    async def async_resolve(self) -> T_co:
        selected_key: typing.Final = self._selector()
        if selected_key not in self._providers:
            msg = f"No provider matches {selected_key}"
            raise RuntimeError(msg)
        self._resolved_provider = await self._providers[selected_key].async_resolve()
        return self._resolved_provider

    def sync_resolve(self) -> T_co:
        selected_key: typing.Final = self._selector()
        if selected_key not in self._providers:
            msg = f"No provider matches {selected_key}"
            raise RuntimeError(msg)
        self._resolved_provider = self._providers[selected_key].sync_resolve()
        return self._resolved_provider

    def __getattr__(self, attr_name: str) -> typing.Any:
        if self._resolved_provider is not None:
            return getattr(self._resolved_provider, attr_name)
        msg = f"'{type(self)}' object has no attribute '{attr_name}'"
        raise AttributeError(msg)