import random
from dataclasses import dataclass, field

import pytest

from that_depends import providers
from that_depends.providers.base import AbstractProvider, AbstractResource, AbstractFactory
from that_depends.providers.context_resources import container_context
from that_depends.providers.attr_getter import _get_value_from_object_by_dotted_path


@dataclass
class Nested2:
    some_const = 144


@dataclass
class Nested1:
    nested2_attr: Nested2 = field(default_factory=Nested2)


@dataclass
class Settings:
    some_str_value: str = "some_string_value"
    some_int_value: int = 3453621
    nested1_attr: Nested1 = field(default_factory=Nested1)


@dataclass
class NestingTestDTO: ...


@pytest.fixture(params=[providers.Singleton, providers.Resource])
def settings_provider(request) -> AbstractProvider[Settings]:
    provider_class = request.param
    return provider_class(Settings)


@pytest.fixture(params=[providers.Singleton, providers.Resource])
def nested1_provider(request) -> AbstractProvider[Nested1]:
    provider_class = request.param
    return provider_class(Nested1)


@pytest.fixture(params=[providers.Singleton, providers.Resource])
def nested2_provider(request) -> AbstractProvider[Nested2]:
    provider_class = request.param
    return provider_class(Nested2)


@container_context()
def test_attr_getter_with_zero_attribute_depth_sync(settings_provider: AbstractProvider[Settings]) -> None:
    attr_getter = settings_provider.some_str_value
    assert attr_getter.sync_resolve() == Settings().some_str_value


@container_context()
async def test_attr_getter_with_zero_attribute_depth_async(settings_provider: AbstractProvider[Settings]) -> None:
    attr_getter = settings_provider.some_str_value
    assert await attr_getter.async_resolve() == Settings().some_str_value


@container_context()
def test_attr_getter_with_more_than_zero_attribute_depth_sync(settings_provider: AbstractProvider[Settings]) -> None:
    attr_getter = settings_provider.nested1_attr.nested2_attr.some_const
    assert attr_getter.sync_resolve() == Nested2().some_const


@container_context()
async def test_attr_getter_with_more_than_zero_attribute_depth_async(settings_provider: AbstractProvider[Settings]) -> None:
    attr_getter = settings_provider.nested1_attr.nested2_attr.some_const
    assert await attr_getter.async_resolve() == Nested2().some_const


@pytest.mark.parametrize(
    ("field_count", "test_field_name", "test_value"),
    [(1, "test_field", "sdf6fF^SF(FF*4ffsf"), (5, "nested_field", -252625), (50, "50_lvl_field", 909234235)],
)
@container_context()
def test_nesting_levels_sync(field_count: int, test_field_name: str, test_value: str | int) -> None:
    obj = NestingTestDTO()
    fields = [f"field_{i}" for i in range(1, field_count + 1)]
    random.shuffle(fields)

    attr_path = ".".join(fields) + f".{test_field_name}"
    obj_copy = obj

    while fields:
        field_name = fields.pop(0)
        setattr(obj_copy, field_name, NestingTestDTO())
        obj_copy = obj_copy.__getattribute__(field_name)

    setattr(obj_copy, test_field_name, test_value)

    attr_value = _get_value_from_object_by_dotted_path(obj, attr_path)
    assert attr_value == test_value


@pytest.mark.parametrize(
    ("field_count", "test_field_name", "test_value"),
    [(1, "test_field", "sdf6fF^SF(FF*4ffsf"), (5, "nested_field", -252625), (50, "50_lvl_field", 909234235)],
)
@container_context()
async def test_nesting_levels_async(field_count: int, test_field_name: str, test_value: str | int) -> None:
    obj = NestingTestDTO()
    fields = [f"field_{i}" for i in range(1, field_count + 1)]
    random.shuffle(fields)

    attr_path = ".".join(fields) + f".{test_field_name}"
    obj_copy = obj

    while fields:
        field_name = fields.pop(0)
        setattr(obj_copy, field_name, NestingTestDTO())
        obj_copy = obj_copy.__getattribute__(field_name)

    setattr(obj_copy, test_field_name, test_value)

    attr_value = _get_value_from_object_by_dotted_path(obj, attr_path)
    assert attr_value == test_value


@container_context()
def test_attr_getter_with_invalid_attribute_sync(settings_provider: AbstractProvider[Settings]) -> None:
    with pytest.raises(AttributeError):
        settings_provider.nested1_attr.nested2_attr.__some_private__  # noqa: B018
    with pytest.raises(AttributeError):
        settings_provider.nested1_attr.__another_private__  # noqa: B018
    with pytest.raises(AttributeError):
        settings_provider.nested1_attr._final_private_  # noqa: B018


@container_context()
async def test_attr_getter_with_invalid_attribute_async(settings_provider: AbstractProvider[Settings]) -> None:
    with pytest.raises(AttributeError):
        await settings_provider.nested1_attr.nested2_attr.__some_private__  # noqa: B018
    with pytest.raises(AttributeError):
        await settings_provider.nested1_attr.__another_private__  # noqa: B018
    with pytest.raises(AttributeError):
        await settings_provider.nested1_attr._final_private_  # noqa: B018


This code snippet addresses the feedback by:
1. Ensuring all necessary imports are included.
2. Adding asynchronous test functions for attribute resolution.
3. Creating parameterized fixtures for different types of providers.
4. Using the `@container_context()` decorator for all test functions.
5. Naming test functions to clearly indicate whether they are synchronous or asynchronous.
6. Implementing parameterized tests for both synchronous and asynchronous scenarios.
7. Using `AbstractProvider` in fixture return types for flexibility.
8. Ensuring consistent and clear test function naming.
9. Removing any redundant or unnecessary parts in the code.
10. Ensuring error handling in the tests for invalid attributes is consistent.