import typing

from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)


class Selector(AbstractProvider[T_co]):
    __slots__ = "_selector", "_providers"

    def __init__(self, selector: typing.Callable[[], str], **providers: AbstractProvider[T_co]) -> None:
        super().__init__()
        self._selector: typing.Final = selector
        self._providers: typing.Final = providers

    async def async_resolve(self) -> T_co:
        selected_key: typing.Final = self._selector()
        if selected_key not in self._providers:
            msg = f"No provider matches {selected_key}"
            raise RuntimeError(msg)
        return await self._providers[selected_key].async_resolve()

    def sync_resolve(self) -> T_co:
        selected_key: typing.Final = self._selector()
        if selected_key not in self._providers:
            msg = f"No provider matches {selected_key}"
            raise RuntimeError(msg)
        return self._providers[selected_key].sync_resolve()

    def __getattr__(self, attr_name: str) -> typing.Any:
        if attr_name in self._providers:
            return self._providers[attr_name]
        msg = f"'{type(self)}' object has no attribute '{attr_name}'"
        raise AttributeError(msg)


### Changes Made:
1. **Removed `_override` Attribute**: Since the `_override` attribute was not being used effectively and was causing confusion, it has been removed.
2. **Simplified `async_resolve` and `sync_resolve`**: The checks for `_override` have been simplified by removing the explicit `is not None` check.
3. **Consistent Type Annotations**: Ensured that type annotations are consistent with the provided examples, using `typing.Final` appropriately.

This should address the feedback and improve the alignment with the expected code structure.