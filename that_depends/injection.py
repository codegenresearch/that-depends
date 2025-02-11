import functools
import inspect
import typing
import warnings

from that_depends.providers import AbstractProvider, Object, Singleton


P = typing.ParamSpec("P")
T = typing.TypeVar("T")


def inject(
    func: typing.Callable[P, T],
) -> typing.Callable[P, T]:
    if inspect.iscoroutinefunction(func):
        return typing.cast(typing.Callable[P, T], _inject_to_async(func))

    return _inject_to_sync(func)


def _inject_to_async(
    func: typing.Callable[P, typing.Coroutine[typing.Any, typing.Any, T]],
) -> typing.Callable[P, typing.Coroutine[typing.Any, typing.Any, T]]:
    signature = inspect.signature(func)

    @functools.wraps(func)
    async def inner(*args: P.args, **kwargs: P.kwargs) -> T:
        injected = False
        bound_args = signature.bind_partial(*args, **kwargs)
        for field_name, field_value in signature.parameters.items():
            if field_name in bound_args.arguments:
                continue

            if isinstance(field_value.default, AbstractProvider):
                kwargs[field_name] = await field_value.default.async_resolve()
                injected = True

        if not injected:
            warnings.warn(
                "Expected injection, but nothing found. Remove @inject decorator.", RuntimeWarning, stacklevel=1
            )
        return await func(*args, **kwargs)

    return inner


def _inject_to_sync(
    func: typing.Callable[P, T],
) -> typing.Callable[P, T]:
    signature: typing.Final = inspect.signature(func)

    @functools.wraps(func)
    def inner(*args: P.args, **kwargs: P.kwargs) -> T:
        injected = False
        bound_args = signature.bind_partial(*args, **kwargs)
        for field_name, field_value in signature.parameters.items():
            if field_name in bound_args.arguments:
                continue

            if isinstance(field_value.default, AbstractProvider):
                if inspect.iscoroutinefunction(field_value.default.async_resolve):
                    raise RuntimeError(f"AsyncResource cannot be resolved synchronously. {field_name=}")
                kwargs[field_name] = field_value.default.sync_resolve()
                injected = True
            elif field_name in kwargs:
                raise RuntimeError(f"Injected argument '{field_name}' is redefined.")

        if not injected:
            warnings.warn(
                "Expected injection, but nothing found. Remove @inject decorator.", RuntimeWarning, stacklevel=1
            )

        return func(*args, **kwargs)

    return inner


class ClassGetItemMeta(type):
    def __getitem__(cls, provider: AbstractProvider[T]) -> AbstractProvider[T]:
        return provider


class Provide(metaclass=ClassGetItemMeta):
    ...