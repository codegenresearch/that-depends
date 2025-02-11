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
        if self._override:
            return typing.cast(T_co, self._override)

        selected_key: typing.Final = self._selector()
        if selected_key not in self._providers:
            msg = f"No provider matches {selected_key}"
            raise RuntimeError(msg)
        return await self._providers[selected_key].async_resolve()

    def sync_resolve(self) -> T_co:
        if self._override:
            return typing.cast(T_co, self._override)

        selected_key: typing.Final = self._selector()
        if selected_key not in self._providers:
            msg = f"No provider matches {selected_key}"
            raise RuntimeError(msg)
        return self._providers[selected_key].sync_resolve()

    def __getattr__(self, attr_name: str) -> typing.Any:
        if attr_name in self._providers:
            return self._providers[attr_name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{attr_name}'")


### Changes Made:
1. **Removed the Comment**: Removed the comment detailing the changes made to avoid syntax errors.
2. **Initialized `_override`**: Added the initialization of `_override` in the `__init__` method to ensure it is defined before being accessed.
3. **Included `_override` in `__slots__`**: Ensured that `_override` is included in the `__slots__` declaration for memory efficiency.
4. **Consistent Error Messaging**: Used `msg` for the error message to maintain consistency.