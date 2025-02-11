import typing

from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)


class Selector(AbstractProvider[T_co]):
    __slots__ = "_selector", "_providers", "_override"

    def __init__(self, selector: typing.Callable[[], str], **providers: AbstractProvider[T_co]) -> None:
        super().__init__()
        self._selector: typing.Final = selector
        self._providers: typing.Final = providers
        self._override = None

    async def async_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        selected_key = self._selector()
        provider = self._providers.get(selected_key)
        if provider is None:
            raise RuntimeError(f"No provider matches {selected_key}")
        return await provider.async_resolve()

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        selected_key = self._selector()
        provider = self._providers.get(selected_key)
        if provider is None:
            raise RuntimeError(f"No provider matches {selected_key}")
        return provider.sync_resolve()

    def __getattr__(self, attr_name: str) -> typing.Any:
        if attr_name in self._providers:
            return self._providers[attr_name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{attr_name}'")