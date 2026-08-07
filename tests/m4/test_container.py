"""Tests for the Service Container and Dependency Injection."""
import pytest
from skos.m4.di.container import Lifecycle, ServiceContainer


class IConfigPort:
    def get(self, key: str) -> str:
        raise NotImplementedError


class ISecretPort:
    def get(self, key: str) -> str:
        raise NotImplementedError


class MockConfigAdapter(IConfigPort):
    def __init__(self, prefix: str = "mock") -> None:
        self.prefix = prefix
    def get(self, key: str) -> str:
        return f"{self.prefix}:{key}"


class MockSecretAdapter(ISecretPort):
    def __init__(self, config: IConfigPort | None = None) -> None:
        self.config = config
    def get(self, key: str) -> str:
        if self.config:
            return f"secret:{self.config.get(key)}"
        return f"secret:{key}"


class ServiceWithMultipleDeps:
    def __init__(self, config: IConfigPort, secret: ISecretPort) -> None:
        self.config = config
        self.secret = secret


class ServiceWithOptionalDep:
    def __init__(self, config: IConfigPort, secret: ISecretPort | None = None) -> None:
        self.config = config
        self.secret = secret


class TestServiceContainer:
    def test_register_and_resolve(self) -> None:
        container = ServiceContainer()
        container.register(IConfigPort, MockConfigAdapter)
        instance = container.resolve(IConfigPort)
        assert isinstance(instance, MockConfigAdapter)
        assert instance.get("test") == "mock:test"

    def test_singleton_lifecycle(self) -> None:
        container = ServiceContainer()
        container.register(IConfigPort, MockConfigAdapter, Lifecycle.SINGLETON)
        instance1 = container.resolve(IConfigPort)
        instance2 = container.resolve(IConfigPort)
        assert instance1 is instance2

    def test_transient_lifecycle(self) -> None:
        container = ServiceContainer()
        container.register(IConfigPort, MockConfigAdapter, Lifecycle.TRANSIENT)
        instance1 = container.resolve(IConfigPort)
        instance2 = container.resolve(IConfigPort)
        assert instance1 is not instance2

    def test_scoped_lifecycle(self) -> None:
        container = ServiceContainer()
        container.register(IConfigPort, MockConfigAdapter, Lifecycle.SCOPED)
        instance1 = container.resolve(IConfigPort, scope_id="scope-a")
        instance2 = container.resolve(IConfigPort, scope_id="scope-a")
        instance3 = container.resolve(IConfigPort, scope_id="scope-b")
        assert instance1 is instance2
        assert instance1 is not instance3

    def test_constructor_injection(self) -> None:
        container = ServiceContainer()
        container.register(IConfigPort, MockConfigAdapter)
        container.register(ISecretPort, MockSecretAdapter)
        container.register(ServiceWithMultipleDeps, ServiceWithMultipleDeps)
        service = container.resolve(ServiceWithMultipleDeps)
        assert isinstance(service.config, MockConfigAdapter)
        assert isinstance(service.secret, MockSecretAdapter)
        assert service.secret.get("test") == "secret:mock:test"

    def test_optional_dependency(self) -> None:
        container = ServiceContainer()
        container.register(IConfigPort, MockConfigAdapter)
        container.register(ISecretPort, MockSecretAdapter)
        container.register(ServiceWithOptionalDep, ServiceWithOptionalDep)
        service = container.resolve(ServiceWithOptionalDep)
        assert service.config is not None
        assert service.secret is not None

    def test_optional_dependency_missing(self) -> None:
        container = ServiceContainer()
        container.register(IConfigPort, MockConfigAdapter)
        container.register(ServiceWithOptionalDep, ServiceWithOptionalDep)
        service = container.resolve(ServiceWithOptionalDep)
        assert service.config is not None
        assert service.secret is None

    def test_register_instance(self) -> None:
        container = ServiceContainer()
        custom_adapter = MockConfigAdapter(prefix="custom")
        container.register_instance(IConfigPort, custom_adapter)
        instance = container.resolve(IConfigPort)
        assert instance is custom_adapter
        assert instance.get("test") == "custom:test"

    def test_unregistered_interface_raises(self) -> None:
        container = ServiceContainer()
        with pytest.raises(KeyError):
            container.resolve(IConfigPort)

    def test_invalid_implementation_raises(self) -> None:
        container = ServiceContainer()
        with pytest.raises(ValueError):
            container.register(IConfigPort, MockSecretAdapter)

    def test_dispose_clears_singletons(self) -> None:
        container = ServiceContainer()
        container.register(IConfigPort, MockConfigAdapter, Lifecycle.SINGLETON)
        instance1 = container.resolve(IConfigPort)
        container.dispose()
        instance2 = container.resolve(IConfigPort)
        assert instance1 is not instance2


class TestScopedContainer:
    def test_scope_context_manager(self) -> None:
        container = ServiceContainer()
        container.register(IConfigPort, MockConfigAdapter, Lifecycle.SCOPED)
        with container.create_scope("request-1") as scoped:
            instance = scoped.resolve(IConfigPort)
            assert isinstance(instance, MockConfigAdapter)

    def test_scope_cleanup(self) -> None:
        container = ServiceContainer()
        container.register(IConfigPort, MockConfigAdapter, Lifecycle.SCOPED)
        with container.create_scope("request-1") as scoped:
            instance1 = scoped.resolve(IConfigPort)
            instance2 = container.resolve(IConfigPort, scope_id="request-1")
            assert instance1 is instance2
