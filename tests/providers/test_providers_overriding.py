import datetime

import pytest

from tests import container


async def test_batch_providers_overriding() -> None:
    async_resource_mock = datetime.datetime.fromisoformat("2023-01-01")
    sync_resource_mock = datetime.datetime.fromisoformat("2024-01-01")
    async_factory_mock = datetime.datetime.fromisoformat("2025-01-01")
    simple_factory_mock = container.SimpleFactory(dep1="override", dep2=999)
    singleton_mock = container.SingletonFactory(dep1=False)
    object_mock = object()  # Additional mock object

    providers_for_overriding = {
        "async_resource": async_resource_mock,
        "sync_resource": sync_resource_mock,
        "simple_factory": simple_factory_mock,
        "singleton": singleton_mock,
        "async_factory": async_factory_mock,
        "object": object_mock,  # Use "object" instead of "object_provider"
    }

    with container.DIContainer.override_providers(providers_for_overriding):
        simple_factory = await container.DIContainer.simple_factory()
        dependent_factory = await container.DIContainer.dependent_factory()
        singleton = await container.DIContainer.singleton()
        async_factory = await container.DIContainer.async_factory()
        object_provider = await container.DIContainer.object()  # Use "object" instead of "object_provider"

    assert dependent_factory.simple_factory.dep1 == simple_factory_mock.dep1
    assert dependent_factory.simple_factory.dep2 == simple_factory_mock.dep2
    assert dependent_factory.sync_resource == sync_resource_mock
    assert dependent_factory.async_resource == async_resource_mock
    assert singleton is singleton_mock
    assert async_factory is async_factory_mock
    assert object_provider is object_mock  # Validate the new mock object

    assert (await container.DIContainer.async_resource()) != async_resource_mock


async def test_batch_providers_overriding_sync_resolve() -> None:
    async_resource_mock = datetime.datetime.fromisoformat("2023-01-01")
    sync_resource_mock = datetime.datetime.fromisoformat("2024-01-01")
    simple_factory_mock = container.SimpleFactory(dep1="override", dep2=999)
    singleton_mock = container.SingletonFactory(dep1=False)
    object_mock = object()  # Additional mock object

    providers_for_overriding = {
        "async_resource": async_resource_mock,
        "sync_resource": sync_resource_mock,
        "simple_factory": simple_factory_mock,
        "singleton": singleton_mock,
        "object": object_mock,  # Use "object" instead of "object_provider"
    }

    with container.DIContainer.override_providers(providers_for_overriding):
        simple_factory = container.DIContainer.simple_factory.sync_resolve()
        async_resource = await container.DIContainer.async_resource.async_resolve()
        dependent_factory = container.DIContainer.dependent_factory.sync_resolve()
        singleton = container.DIContainer.singleton.sync_resolve()
        object_provider = container.DIContainer.object.sync_resolve()  # Use "object" instead of "object_provider"

    assert dependent_factory.simple_factory.dep1 == simple_factory_mock.dep1
    assert dependent_factory.simple_factory.dep2 == simple_factory_mock.dep2
    assert dependent_factory.sync_resource == sync_resource_mock
    assert dependent_factory.async_resource == async_resource_mock
    assert singleton is singleton_mock
    assert object_provider is object_mock  # Validate the new mock object

    assert container.DIContainer.sync_resource.sync_resolve() != sync_resource_mock


def test_providers_overriding_with_context_manager() -> None:
    simple_factory_mock = container.SimpleFactory(dep1="override", dep2=999)

    with container.DIContainer.simple_factory.override_context(simple_factory_mock):
        resolved_factory = container.DIContainer.simple_factory.sync_resolve()
        assert resolved_factory is simple_factory_mock

    resolved_factory = container.DIContainer.simple_factory.sync_resolve()
    assert resolved_factory is not simple_factory_mock


def test_providers_overriding_fail_with_unknown_provider() -> None:
    unknown_provider_name = "unknown_provider_name"
    match = f"Provider with name {unknown_provider_name!r} not found"

    with pytest.raises(RuntimeError, match=match):
        with container.DIContainer.override_providers({unknown_provider_name: None}):
            pass  # pragma: no cover


async def test_providers_overriding() -> None:
    async_resource_mock = datetime.datetime.fromisoformat("2023-01-01")
    sync_resource_mock = datetime.datetime.fromisoformat("2024-01-01")
    async_factory_mock = datetime.datetime.fromisoformat("2025-01-01")
    simple_factory_mock = container.SimpleFactory(dep1="override", dep2=999)
    singleton_mock = container.SingletonFactory(dep1=False)
    object_mock = object()  # Additional mock object

    container.DIContainer.async_resource.override(async_resource_mock)
    container.DIContainer.sync_resource.override(sync_resource_mock)
    container.DIContainer.simple_factory.override(simple_factory_mock)
    container.DIContainer.singleton.override(singleton_mock)
    container.DIContainer.async_factory.override(async_factory_mock)
    container.DIContainer.object.override(object_mock)  # Use "object" instead of "object_provider"

    simple_factory = await container.DIContainer.simple_factory()
    dependent_factory = await container.DIContainer.dependent_factory()
    singleton = await container.DIContainer.singleton()
    async_factory = await container.DIContainer.async_factory()
    object_provider = await container.DIContainer.object()  # Use "object" instead of "object_provider"

    assert dependent_factory.simple_factory.dep1 == simple_factory_mock.dep1
    assert dependent_factory.simple_factory.dep2 == simple_factory_mock.dep2
    assert dependent_factory.sync_resource == sync_resource_mock
    assert dependent_factory.async_resource == async_resource_mock
    assert singleton is singleton_mock
    assert async_factory is async_factory_mock
    assert object_provider is object_mock  # Validate the new mock object

    container.DIContainer.reset_override()
    assert (await container.DIContainer.async_resource()) != async_resource_mock


async def test_providers_overriding_sync_resolve() -> None:
    async_resource_mock = datetime.datetime.fromisoformat("2023-01-01")
    sync_resource_mock = datetime.datetime.fromisoformat("2024-01-01")
    simple_factory_mock = container.SimpleFactory(dep1="override", dep2=999)
    singleton_mock = container.SingletonFactory(dep1=False)
    object_mock = object()  # Additional mock object

    container.DIContainer.async_resource.override(async_resource_mock)
    container.DIContainer.sync_resource.override(sync_resource_mock)
    container.DIContainer.simple_factory.override(simple_factory_mock)
    container.DIContainer.singleton.override(singleton_mock)
    container.DIContainer.async_factory.override(async_factory_mock)
    container.DIContainer.object.override(object_mock)  # Use "object" instead of "object_provider"

    simple_factory = container.DIContainer.simple_factory.sync_resolve()
    async_resource = await container.DIContainer.async_resource.async_resolve()
    dependent_factory = container.DIContainer.dependent_factory.sync_resolve()
    singleton = container.DIContainer.singleton.sync_resolve()
    object_provider = container.DIContainer.object.sync_resolve()  # Use "object" instead of "object_provider"

    assert dependent_factory.simple_factory.dep1 == simple_factory_mock.dep1
    assert dependent_factory.simple_factory.dep2 == simple_factory_mock.dep2
    assert dependent_factory.sync_resource == sync_resource_mock
    assert dependent_factory.async_resource == async_resource_mock
    assert singleton is singleton_mock
    assert object_provider is object_mock  # Validate the new mock object

    container.DIContainer.reset_override()
    assert container.DIContainer.sync_resource.sync_resolve() != sync_resource_mock


This code snippet addresses the feedback by ensuring that the provider names in the `providers_for_overriding` dictionary match those expected by the `DIContainer`. It also updates the method calls for resolving providers to use the correct names and ensures that the assertions are consistent with the expected behavior.