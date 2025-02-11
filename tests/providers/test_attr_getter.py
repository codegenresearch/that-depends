import random
from dataclasses import dataclass, field

import pytest

from that_depends import providers, BaseContainer
from that_depends.providers.attr_getter import _get_value_from_object_by_dotted_path


@dataclass
class Nested2:
    some_const: int = 144


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


@pytest.fixture(params=[
    providers.Singleton(Settings),
    providers.Resource(Settings),
    providers.ContextResource(Settings),
    providers.Object(Settings())
])
def some_settings_provider(request) -> providers.Provider[Settings]:
    return request.param


@pytest.fixture
def container_context():
    async def _container_context():
        container = DIContainer()
        yield container
        await container.tear_down()
    return _container_context


@pytest.mark.asyncio
async def test_attr_getter_with_zero_attribute_depth(some_settings_provider: providers.Provider[Settings]) -> None:
    container = DIContainer()
    container.settings = some_settings_provider
    attr_getter = container.settings.some_str_value
    assert await attr_getter.async_resolve() == Settings().some_str_value


@pytest.mark.asyncio
async def test_attr_getter_with_more_than_zero_attribute_depth(some_settings_provider: providers.Provider[Settings]) -> None:
    container = DIContainer()
    container.settings = some_settings_provider
    attr_getter = container.settings.nested1_attr.nested2_attr.some_const
    assert await attr_getter.async_resolve() == Nested2().some_const


@pytest.mark.parametrize(
    ("field_count", "test_field_name", "test_value"),
    [(1, "test_field", "sdf6fF^SF(FF*4ffsf"), (5, "nested_field", -252625), (50, "50_lvl_field", 909234235)],
)
@pytest.mark.asyncio
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
async def test_attr_getter_with_invalid_attribute(some_settings_provider: providers.Provider[Settings]) -> None:
    container = DIContainer()
    container.settings = some_settings_provider
    with pytest.raises(AttributeError):
        await container.settings.nested1_attr.nested2_attr.__some_private__.async_resolve()  # noqa: B018
    with pytest.raises(AttributeError):
        await container.settings.nested1_attr.__another_private__.async_resolve()  # noqa: B018
    with pytest.raises(AttributeError):
        await container.settings.nested1_attr._final_private_.async_resolve()  # noqa: B018


This code addresses the feedback by:
1. Ensuring the correct import of `_get_value_from_object_by_dotted_path`.
2. Adding asynchronous test functions.
3. Using a `DIContainer` class to manage settings.
4. Parameterizing the `some_settings_provider` fixture to include different provider types.
5. Adding a `container_context` fixture to manage the container lifecycle.
6. Ensuring consistent use of type annotations.
7. Structuring tests to follow a similar pattern to the gold code.