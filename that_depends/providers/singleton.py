import asyncio
import typing
from operator import attrgetter
from functools import partial
from collections.abc import Hashable

from that_depends.providers.base import AbstractProvider
from that_depends.providers import AttrGetter


T_co = typing.TypeVar("T_co", covariant=True)
P = typing.ParamSpec("P")


class Singleton(AbstractProvider[T_co]):
    __slots__ = "_factory", "_args", "_kwargs", "_override", "_instances", "_resolving_lock"

    _instances: typing.Dict[Hashable, 'Singleton'] = {}

    def __init__(self, factory: type[T_co] | typing.Callable[P, T_co], *args: P.args, **kwargs: P.kwargs) -> None:
        super().__init__()
        self._factory: typing.Final = factory
        self._args: typing.Final = args
        self._kwargs: typing.Final = kwargs
        self._override = None
        self._resolving_lock: typing.Final = asyncio.Lock()

    def __getattr__(self, attr_name: str) -> typing.Any:
        if attr_name.startswith("_"):
            msg = f"'{type(self)}' object has no attribute '{attr_name}'"
            raise AttributeError(msg)
        return AttrGetter(provider=self, attr_name=attr_name)

    def _get_instance_key(self) -> Hashable:
        return hash((self._factory, self._args, tuple(sorted(self._kwargs.items()))))

    async def async_resolve(self) -> T_co:
        key = self._get_instance_key()
        if self._override is not None:
            return typing.cast(T_co, self._override)

        if key in self._instances:
            return self._instances[key]

        # lock to prevent resolving several times
        async with self._resolving_lock:
            if key not in self._instances:
                instance = self._factory(
                    *[
                        await x.async_resolve() if isinstance(x, AbstractProvider) else x
                        for x in self._args
                    ],
                    **{
                        k: await v.async_resolve() if isinstance(v, AbstractProvider) else v
                        for k, v in self._kwargs.items()
                    },
                )
                self._instances[key] = instance
            return self._instances[key]

    def sync_resolve(self) -> T_co:
        key = self._get_instance_key()
        if self._override is not None:
            return typing.cast(T_co, self._override)

        if key in self._instances:
            return self._instances[key]

        if key not in self._instances:
            instance = self._factory(
                *[
                    x.sync_resolve() if isinstance(x, AbstractProvider) else x
                    for x in self._args
                ],
                **{
                    k: v.sync_resolve() if isinstance(v, AbstractProvider) else v
                    for k, v in self._kwargs.items()
                },
            )
            self._instances[key] = instance
        return self._instances[key]

    async def tear_down(self) -> None:
        key = self._get_instance_key()
        if key in self._instances:
            del self._instances[key]


This code addresses the feedback by:
1. Adding the `_override` attribute and checking it in both `async_resolve` and `sync_resolve`.
2. Using `typing.cast` when returning `_override`.
3. Ensuring comments are consistent in style and capitalization.
4. Formatting list and dictionary comprehensions for better readability.
5. Implementing a mechanism to store and retrieve instances based on initialization parameters to ensure the singleton pattern behaves as expected.