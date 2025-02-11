import asyncio
import typing

from that_depends.providers import AttrGetter
from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)
P = typing.ParamSpec("P")


class Singleton(AbstractProvider[T_co]):
    __slots__ = "_factory", "_args", "_kwargs", "_override", "_instance", "_resolving_lock"

    def __init__(self, factory: type[T_co] | typing.Callable[P, T_co], *args: P.args, **kwargs: P.kwargs) -> None:
        super().__init__()
        self._factory: typing.Final = factory
        self._args: typing.Final = args
        self._kwargs: typing.Final = kwargs
        self._override: T_co | None = None
        self._instance: T_co | None = None
        self._resolving_lock: typing.Final = asyncio.Lock()

    def __getattr__(self, attr_name: str) -> typing.Any:
        if attr_name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{attr_name}'")
        return AttrGetter(provider=self, attr_name=attr_name)

    async def async_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        if self._instance is not None:
            return self._instance

        # lock to prevent resolving several times
        async with self._resolving_lock:
            if self._instance is None:
                self._instance = await self._create_instance(async_=True)
            return self._instance

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        if self._instance is None:
            self._instance = self._create_instance(async_=False)
        return self._instance

    async def _create_instance(self, async_: bool) -> T_co:
        if async_:
            return self._factory(
                *[
                    await x.async_resolve() if isinstance(x, AbstractProvider) else x
                    for x in self._args
                ],
                **{
                    k: await v.async_resolve() if isinstance(v, AbstractProvider) else v
                    for k, v in self._kwargs.items()
                },
            )
        else:
            return self._factory(
                *[
                    x.sync_resolve() if isinstance(x, AbstractProvider) else x
                    for x in self._args
                ],
                **{
                    k: v.sync_resolve() if isinstance(v, AbstractProvider) else v
                    for k, v in self._kwargs.items()
                },
            )

    async def tear_down(self) -> None:
        if self._instance is not None:
            self._instance = None


### Key Changes:
1. **Reintroduced `_override` Attribute**: Added the `_override` attribute back to the class and its initialization in the constructor.
2. **Instance Creation Logic**: Ensured the instance creation logic is directly within the lock context in the `async_resolve` method.
3. **Return Statements**: Positioned the return statements correctly after the instance is created.
4. **Type Casting**: Used `typing.cast` when returning the `_override` attribute.
5. **Comment Style**: Changed the comment in the `async_resolve` method to be in lowercase.
6. **Formatting**: Adjusted the formatting of list and dictionary comprehensions for consistency and readability.