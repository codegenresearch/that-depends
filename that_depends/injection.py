import functools
import inspect
import typing
import warnings

from that_depends.providers import AbstractProvider


P = typing.ParamSpec("P")
T = typing.TypeVar("T")


def inject(func: typing.Callable[P, T]) -> typing.Callable[P, T]:
    if inspect.iscoroutinefunction(func):
        return _inject_to_async(func)
    return _inject_to_sync(func)


def _inject_to_async(func: typing.Callable[P, typing.Coroutine[typing.Any, typing.Any, T]]) -> typing.Callable[P, typing.Coroutine[typing.Any, typing.Any, T]]:
    signature = inspect.signature(func)

    @functools.wraps(func)
    async def inner(*args: P.args, **kwargs: P.kwargs) -> T:
        injected = False
        for i, (name, param) in enumerate(signature.parameters.items()):
            if i < len(args) or name in kwargs or not isinstance(param.default, AbstractProvider):
                continue
            kwargs[name] = await param.default.async_resolve()
            injected = True
        if not injected:
            warnings.warn("No injection found; remove @inject decorator.", RuntimeWarning, stacklevel=1)
        return await func(*args, **kwargs)

    return inner


def _inject_to_sync(func: typing.Callable[P, T]) -> typing.Callable[P, T]:
    signature = inspect.signature(func)

    @functools.wraps(func)
    def inner(*args: P.args, **kwargs: P.kwargs) -> T:
        injected = False
        for name, param in signature.parameters.items():
            if i < len(args) or name in kwargs or not isinstance(param.default, AbstractProvider):
                continue
            if name in kwargs:
                raise RuntimeError(f"Injected arguments must not be redefined: {name=}")
            kwargs[name] = param.default.sync_resolve()
            injected = True
        if not injected:
            warnings.warn("No injection found; remove @inject decorator.", RuntimeWarning, stacklevel=1)
        return func(*args, **kwargs)

    return inner


class ClassGetItemMeta(type):
    def __getitem__(cls, provider: AbstractProvider[T]) -> T:
        if not isinstance(provider, AbstractProvider):
            raise TypeError("Expected an AbstractProvider instance")
        return provider.sync_resolve()


class Provide(metaclass=ClassGetItemMeta):
    pass