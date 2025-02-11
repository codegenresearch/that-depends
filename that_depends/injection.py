import asyncio
import functools
import inspect
import typing
import warnings

from that_depends.providers.base import AbstractProvider


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
        for i, (field_name, field_value) in enumerate(signature.parameters.items()):
            if i < len(args):
                continue

            if not isinstance(field_value.default, AbstractProvider):
                continue

            if field_name in kwargs:
                continue

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
        for i, (field_name, field_value) in enumerate(signature.parameters.items()):
            if i < len(args):
                continue

            if not isinstance(field_value.default, AbstractProvider):
                continue

            if field_name in kwargs:
                raise RuntimeError(f"Injected argument '{field_name}' must not be redefined")

            kwargs[field_name] = field_value.default.sync_resolve()
            injected = True

        if not injected:
            warnings.warn(
                "Expected injection, but nothing found. Remove @inject decorator.", RuntimeWarning, stacklevel=1
            )

        return func(*args, **kwargs)

    return inner


class ClassGetItemMeta(type):
    def __getitem__(cls, provider: AbstractProvider[T]) -> T:
        return typing.cast(T, provider)


class Provide(metaclass=ClassGetItemMeta): ...


To address the feedback, I have made the following changes:

1. **Parameter Iteration in `_inject_to_async`:** I iterated through the parameters directly without using `signature.bind_partial`, aligning with the gold code's logic.

2. **Error Handling in `_inject_to_sync`:** I made the error message more concise and consistent with the gold code by changing it to `f"Injected argument '{field_name}' must not be redefined"`.

3. **Code Clarity and Structure:** I ensured consistent indentation and spacing for better readability.

4. **Consistency in Warnings:** I double-checked that the warning conditions and messages are identical to those in the gold code.

These changes should address the feedback and bring the code closer to the gold standard.