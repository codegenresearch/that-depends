import random
from dataclasses import dataclass, field

import pytest

from that_depends import providers
from that_depends.providers.attr_getter import AttrGetter, _get_value_from_object_by_dotted_path


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
    _override: typing.Any = None

    def override(self, mock: object) -> None:
        self._override = mock

    def sync_resolve(self) -> "NestingTestDTO":
        if self._override:
            return self._override
        return self


@pytest.fixture
def some_settings_provider() -> providers.Singleton[Settings]:
    return providers.Singleton(Settings)


def test_attr_getter_with_zero_attribute_depth(some_settings_provider: providers.Singleton[Settings]) -> None:
    attr_getter = AttrGetter(provider=some_settings_provider, attr_name="some_str_value")
    assert attr_getter.sync_resolve() == Settings().some_str_value


def test_attr_getter_with_more_than_zero_attribute_depth(some_settings_provider: providers.Singleton[Settings]) -> None:
    attr_getter = AttrGetter(provider=some_settings_provider, attr_name="nested1_attr.nested2_attr.some_const")
    assert attr_getter.sync_resolve() == Nested2().some_const


@pytest.mark.parametrize(
    ("field_count", "test_field_name", "test_value"),
    [(1, "test_field", "sdf6fF^SF(FF*4ffsf"), (5, "nested_field", -252625), (50, "50_lvl_field", 909234235)],
)
def test_nesting_levels(field_count: int, test_field_name: str, test_value: str | int) -> None:
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


def test_attr_getter_with_invalid_attribute(some_settings_provider: providers.Singleton[Settings]) -> None:
    with pytest.raises(AttributeError):
        AttrGetter(provider=some_settings_provider.nested1_attr.nested2_attr, attr_name="__some_private__").sync_resolve()  # noqa: B018
    with pytest.raises(AttributeError):
        AttrGetter(provider=some_settings_provider.nested1_attr, attr_name="__another_private__").sync_resolve()  # noqa: B018
    with pytest.raises(AttributeError):
        AttrGetter(provider=some_settings_provider.nested1_attr, attr_name="_final_private_").sync_resolve()  # noqa: B018