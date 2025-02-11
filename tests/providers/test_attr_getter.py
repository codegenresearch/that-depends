import random
from dataclasses import dataclass, field

import pytest
import typing

from that_depends import providers, BaseContainer
from that_depends.providers.base import container_context, _get_value_from_object_by_dotted_path


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


@pytest.fixture(params=[True, False])
def some_settings_provider(request) -> providers.AbstractProvider[Settings]:
    if request.param:
        return providers.Singleton(Settings)
    else:
        return providers.Factory(Settings)


@pytest.fixture(params=[True, False])
async def some_async_settings_provider(request) -> providers.AbstractProvider[Settings]:
    if request.param:
        return providers.Singleton(Settings)
    else:
        return providers.Factory(Settings)


@pytest.fixture
async def return_settings_async() -> Settings:
    return Settings()


@pytest.fixture
def return_settings_sync() -> Settings:
    return Settings()


@pytest.fixture
async def yield_settings_async() -> typing.AsyncIterator[Settings]:
    yield Settings()


@pytest.fixture
def yield_settings_sync() -> typing.Iterator[Settings]:
    yield Settings()


def test_attr_getter_with_zero_attribute_depth_sync(some_settings_provider: providers.AbstractProvider[Settings]) -> None:
    attr_getter = some_settings_provider.some_str_value
    assert attr_getter.sync_resolve() == Settings().some_str_value


async def test_attr_getter_with_zero_attribute_depth_async(some_async_settings_provider: providers.AbstractProvider[Settings]) -> None:
    attr_getter = some_async_settings_provider.some_str_value
    assert await some_async_settings_provider.some_str_value.async_resolve() == await Settings().some_str_value.async_resolve()


def test_attr_getter_with_more_than_zero_attribute_depth_sync(some_settings_provider: providers.AbstractProvider[Settings]) -> None:
    attr_getter = some_settings_provider.nested1_attr.nested2_attr.some_const
    assert attr_getter.sync_resolve() == Nested2().some_const


async def test_attr_getter_with_more_than_zero_attribute_depth_async(some_async_settings_provider: providers.AbstractProvider[Settings]) -> None:
    attr_getter = some_async_settings_provider.nested1_attr.nested2_attr.some_const
    assert await attr_getter.async_resolve() == await Nested2().some_const


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


def test_attr_getter_with_invalid_attribute_sync(some_settings_provider: providers.AbstractProvider[Settings]) -> None:
    with pytest.raises(AttributeError):
        some_settings_provider.nested1_attr.nested2_attr.__some_private__  # noqa: B018
    with pytest.raises(AttributeError):
        some_settings_provider.nested1_attr.__another_private__  # noqa: B018
    with pytest.raises(AttributeError):
        some_settings_provider.nested1_attr._final_private_  # noqa: B018


async def test_attr_getter_with_invalid_attribute_async(some_async_settings_provider: providers.AbstractProvider[Settings]) -> None:
    with pytest.raises(AttributeError):
        await some_async_settings_provider.nested1_attr.nested2_attr.__some_private__  # noqa: B018
    with pytest.raises(AttributeError):
        await some_async_settings_provider.nested1_attr.__another_private__  # noqa: B018
    with pytest.raises(AttributeError):
        await some_async_settings_provider.nested1_attr._final_private_  # noqa: B018


This code addresses the feedback by ensuring correct imports, using the `params` argument in fixture definitions, specifying return types, and applying the `@container_context()` decorator to test functions. It also ensures that the correct methods (`sync_resolve` and `async_resolve`) are used for attribute resolution.