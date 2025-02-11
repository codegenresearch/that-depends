import typing
import asyncio

from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)
P = typing.ParamSpec("P")


class Object(AbstractProvider[T_co]):
    __slots__ = "_obj", "_override"

    def __init__(self, obj: T_co, override: T_co | None = None) -> None:
        super().__init__()
        self._obj: typing.Final = obj
        self._override: T_co | None = override

    async def async_resolve(self) -> T_co:
        return self.sync_resolve()

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return self._override
        return self._obj


class LazyObject(AbstractProvider[T_co]):
    __slots__ = "_factory", "_args", "_kwargs", "_instance", "_resolving_lock", "_override"

    def __init__(self, factory: typing.Callable[P, T_co], *args: P.args, **kwargs: P.kwargs) -> None:
        super().__init__()
        self._factory: typing.Final = factory
        self._args: typing.Final = args
        self._kwargs: typing.Final = kwargs
        self._instance: T_co | None = None
        self._resolving_lock: typing.Final = asyncio.Lock()
        self._override: T_co | None = None

    async def async_resolve(self) -> T_co:
        if self._override is not None:
            return self._override

        if self._instance is not None:
            return self._instance

        async with self._resolving_lock:
            if self._instance is None:
                self._instance = self._factory(
                    *[  # type: ignore[arg-type]
                        await x.async_resolve() if isinstance(x, AbstractProvider) else x for x in self._args
                    ],
                    **{  # type: ignore[arg-type]
                        k: await v.async_resolve() if isinstance(v, AbstractProvider) else v
                        for k, v in self._kwargs.items()
                    },
                )
            return self._instance

    def sync_resolve(self) -> T_co:
        if self._override is not None:
            return self._override

        if self._instance is not None:
            return self._instance

        self._instance = self._factory(
            *[  # type: ignore[arg-type]
                x.sync_resolve() if isinstance(x, AbstractProvider) else x for x in self._args
            ],
            **{  # type: ignore[arg-type]
                k: v.sync_resolve() if isinstance(v, AbstractProvider) else v for k, v in self._kwargs.items()
            },
        )
        return self._instance

    async def tear_down(self) -> None:
        if self._instance is not None:
            self._instance = None