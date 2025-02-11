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

        selected_key: typing.Final = self._selector()
        if selected_key not in self._providers:
            msg = f"No provider matches {selected_key}"
            raise RuntimeError(msg)
        return await self._providers[selected_key].async_resolve()

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        selected_key: typing.Final = self._selector()
        if selected_key not in self._providers:
            msg = f"No provider matches {selected_key}"
            raise RuntimeError(msg)
        return self._providers[selected_key].sync_resolve()


### Changes Made:
1. **Added `_override` Attribute**: Added the `_override` attribute and initialized it in the constructor.
2. **Implemented Override Logic**: Added checks for `_override` in both `async_resolve` and `sync_resolve` methods.
3. **Used `typing.cast`**: Used `typing.cast` to ensure the return type is correctly inferred when returning `_override`.
4. **Removed Unnecessary Comments**: Removed the comment block that was causing the `SyntaxError`.

This should address the syntax error and align the code more closely with the expected structure and functionality.