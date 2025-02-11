import asyncio
import typing

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
        self._override = None
        self._instance: T_co | None = None
        self._resolving_lock: typing.Final = asyncio.Lock()

    async def async_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        if self._instance is not None:
            return self._instance

        # Lock to prevent resolving several times
        async with self._resolving_lock:
            if self._instance is None:
                self._instance = self._factory(
                    *[await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
                    **{
                        k: await v.async_resolve() if isinstance(v, AbstractProvider) else v
                        for k, v in self._kwargs.items()
                    },
                )
        return self._instance

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        if self._instance is not None:
            return self._instance

        with self._resolving_lock:
            if self._instance is None:
                self._instance = self._factory(
                    *[x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
                    **{k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
                )
        return self._instance

    async def tear_down(self) -> None:
        if self._instance is not None:
            self._instance = None


This revised code addresses the feedback by:

1. Ensuring the initialization of `_instance` is consistent with the gold code.
2. Placing the return statement for `_instance` correctly after the lock block in `async_resolve`.
3. Formatting comments consistently and clearly.
4. Using `typing.Final` consistently, ensuring `_override` is not marked as `Final`.
5. Reviewing the overall structure of the code for readability, ensuring consistent indentation and spacing.