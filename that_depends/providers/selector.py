import typing
import asyncio

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

        selected_key: str = self._selector()
        if selected_key not in self._providers:
            msg = f"No provider matches {selected_key}"
            raise RuntimeError(msg)
        return await self._providers[selected_key].async_resolve()

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        selected_key: str = self._selector()
        if selected_key not in self._providers:
            msg = f"No provider matches {selected_key}"
            raise RuntimeError(msg)
        return self._providers[selected_key].sync_resolve()

    def __getattr__(self, attr_name: str) -> typing.Any:
        selected_key: str = self._selector()
        if selected_key in self._providers:
            provider = self._providers[selected_key]
            return getattr(provider, attr_name)

        msg = f"'{type(self)}' object has no attribute '{attr_name}'"
        raise AttributeError(msg)


### Changes Made:
1. **Override Handling**: Ensured that `_override` is initialized to `None` in the constructor.
2. **Final Attributes**: Confirmed that `_selector` and `_providers` are marked as `Final`.
3. **Consistency in Method Implementation**: Ensured that `async_resolve` and `sync_resolve` methods are consistent and properly handle the `_override` attribute.
4. **Error Handling**: Kept the error messages clear and consistent with the previous implementation.

This should address the feedback and make the code syntactically correct and closer to the expected standard.