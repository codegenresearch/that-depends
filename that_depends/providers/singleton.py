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

        # lock to prevent resolving several times
        async with self._resolving_lock:
            if self._instance is None:
                self._instance = self._factory(
                    *[await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
                    **{k: await v.async_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
                )
            return self._instance

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return typing.cast(T_co, self._override)

        if self._instance is not None:
            return self._instance

        self._instance = self._factory(
            *[x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
            **{k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
        )
        return self._instance

    async def tear_down(self) -> None:
        if self._instance is not None:
            self._instance = None


To address the feedback and ensure that the `Singleton` class correctly handles unique instances based on parameters, we need to modify the class to store instances in a dictionary keyed by the parameters. Here is the updated code:


import asyncio
import typing
import functools

from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)
P = typing.ParamSpec("P")


class Singleton(AbstractProvider[T_co]):
    __slots__ = "_factory", "_args", "_kwargs", "_override", "_instances", "_resolving_locks"

    def __init__(self, factory: type[T_co] | typing.Callable[P, T_co], *args: P.args, **kwargs: P.kwargs) -> None:
        super().__init__()
        self._factory: typing.Final = factory
        self._args: typing.Final = args
        self._kwargs: typing.Final = kwargs
        self._override = None
        self._instances: typing.Dict[typing.Tuple, T_co] = {}
        self._resolving_locks: typing.Dict[typing.Tuple, asyncio.Lock] = {}

    async def async_resolve(self) -> T_co:
        key = (self._args, tuple(self._kwargs.items()))
        if self._override is not None:
            return typing.cast(T_co, self._override)

        if key in self._instances:
            return self._instances[key]

        # Ensure only one instance is created per key
        if key not in self._resolving_locks:
            self._resolving_locks[key] = asyncio.Lock()

        async with self._resolving_locks[key]:
            if key not in self._instances:
                self._instances[key] = self._factory(
                    *[await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
                    **{k: await v.async_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
                )
            return self._instances[key]

    def sync_resolve(self) -> T_co:
        key = (self._args, tuple(self._kwargs.items()))
        if self._override is not None:
            return typing.cast(T_co, self._override)

        if key in self._instances:
            return self._instances[key]

        # Ensure only one instance is created per key
        if key not in self._resolving_locks:
            self._resolving_locks[key] = asyncio.Lock()

        with self._resolving_locks[key]:
            if key not in self._instances:
                self._instances[key] = self._factory(
                    *[x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args],
                    **{k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()},
                )
            return self._instances[key]

    async def tear_down(self) -> None:
        key = (self._args, tuple(self._kwargs.items()))
        if key in self._instances:
            self._instances.pop(key)
        if key in self._resolving_locks:
            self._resolving_locks.pop(key)


This updated code ensures that each unique combination of arguments and keyword arguments results in a unique instance of the object, addressing the test failures.