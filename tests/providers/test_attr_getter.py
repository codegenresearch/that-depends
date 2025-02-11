import random
from dataclasses import dataclass, field

import pytest

from that_depends import providers, BaseContainer
from that_depends.providers.base import _get_value_from_object_by_dotted_path
from that_depends.providers.context_resources import container_context


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
class NestingTestDTO:
    _override: object = None

    def override(self, mock: object) -> None:
        self._override = mock

    def reset_override(self) -> None:
        self._override = None

    def __getattr__(self, attr_name: str) -> providers.AttrGetter:
        if attr_name.startswith("_"):
            msg = f"'{type(self)}' object has no attribute '{attr_name}'"
            raise AttributeError(msg)
        return providers.AttrGetter(provider=self, attr_name=attr_name)


class DIContainer(BaseContainer):
    settings: Settings = providers.Singleton(Settings).cast


@pytest.fixture
def sync_settings_provider() -> providers.Provider[Settings]:
    return providers.Singleton(Settings)


@pytest.fixture
async def async_settings_provider() -> providers.Provider[Settings]:
    return providers.Singleton(Settings)


@pytest.mark.asyncio
@container_context()
async def test_attr_getter_with_zero_attribute_depth_sync(sync_settings_provider: providers.Provider[Settings]) -> None:
    container = DIContainer()
    container.settings = sync_settings_provider
    attr_getter = container.settings.some_str_value
    assert attr_getter.sync_resolve() == Settings().some_str_value


@pytest.mark.asyncio
@container_context()
async def test_attr_getter_with_zero_attribute_depth_async(async_settings_provider: providers.Provider[Settings]) -> None:
    container = DIContainer()
    container.settings = async_settings_provider
    attr_getter = container.settings.some_str_value
    assert await attr_getter.async_resolve() == Settings().some_str_value


@pytest.mark.asyncio
@container_context()
async def test_attr_getter_with_more_than_zero_attribute_depth_sync(sync_settings_provider: providers.Provider[Settings]) -> None:
    container = DIContainer()
    container.settings = sync_settings_provider
    attr_getter = container.settings.nested1_attr.nested2_attr.some_const
    assert attr_getter.sync_resolve() == Nested2().some_const


@pytest.mark.asyncio
@container_context()
async def test_attr_getter_with_more_than_zero_attribute_depth_async(async_settings_provider: providers.Provider[Settings]) -> None:
    container = DIContainer()
    container.settings = async_settings_provider
    attr_getter = container.settings.nested1_attr.nested2_attr.some_const
    assert await attr_getter.async_resolve() == Nested2().some_const


@pytest.mark.parametrize(
    ("field_count", "test_field_name", "test_value"),
    [(1, "test_field", "sdf6fF^SF(FF*4ffsf"), (5, "nested_field", -252625), (50, "50_lvl_field", 909234235)],
)
@pytest.mark.asyncio
@container_context()
async def test_nesting_levels(field_count: int, test_field_name: str, test_value: str | int) -> None:
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


@pytest.mark.asyncio
@container_context()
async def test_attr_getter_with_invalid_attribute_sync(sync_settings_provider: providers.Provider[Settings]) -> None:
    container = DIContainer()
    container.settings = sync_settings_provider
    with pytest.raises(AttributeError):
        container.settings.nested1_attr.nested2_attr.__some_private__  # noqa: B018
    with pytest.raises(AttributeError):
        container.settings.nested1_attr.__another_private__  # noqa: B018
    with pytest.raises(AttributeError):
        container.settings.nested1_attr._final_private_  # noqa: B018


@pytest.mark.asyncio
@container_context()
async def test_attr_getter_with_invalid_attribute_async(async_settings_provider: providers.Provider[Settings]) -> None:
    container = DIContainer()
    container.settings = async_settings_provider
    with pytest.raises(AttributeError):
        container.settings.nested1_attr.nested2_attr.__some_private__  # noqa: B018
    with pytest.raises(AttributeError):
        container.settings.nested1_attr.__another_private__  # noqa: B018
    with pytest.raises(AttributeError):
        container.settings.nested1_attr._final_private_  # noqa: B018


This code addresses the feedback by:
1. Correcting the import of `_get_value_from_object_by_dotted_path` from `that_depends.providers.base`.
2. Importing `container_context` from `that_depends.providers.context_resources`.
3. Removing type annotations from the `some_const` attribute in the `Nested2` class.
4. Splitting the `some_settings_provider` fixture into `sync_settings_provider` and `async_settings_provider`.
5. Using the `@container_context()` decorator for test functions to manage the container lifecycle.
6. Naming test functions to clearly indicate whether they are synchronous or asynchronous.
7. Ensuring error handling in tests accesses attributes directly.
8. Using consistent and appropriate type annotations throughout the code.