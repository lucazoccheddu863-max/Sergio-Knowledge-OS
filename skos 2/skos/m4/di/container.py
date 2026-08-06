"""Service Container for Dependency Injection.

The Container manages the lifecycle and wiring of all components in M4.
No module should instantiate its dependencies directly.
"""
from __future__ import annotations

import inspect
import types
import typing
from enum import Enum, auto
from typing import Any, TypeVar


class Lifecycle(Enum):
    """Component lifecycle modes."""
    SINGLETON = auto()
    SCOPED = auto()
    TRANSIENT = auto()


T = TypeVar("T")


class ServiceContainer:
    """Lightweight dependency injection container."""

    def __init__(self) -> None:
        self._registrations: dict[type, tuple[type, Lifecycle]] = {}
        self._singletons: dict[type, Any] = {}
        self._scoped_instances: dict[str, dict[type, Any]] = {}

    def register(
        self,
        interface: type[T],
        implementation: type[T],
        lifecycle: Lifecycle = Lifecycle.SINGLETON,
    ) -> None:
        """Register an implementation for an interface."""
        if not issubclass(implementation, interface):
            raise ValueError(
                f"Implementation {implementation.__name__} does not implement "
                f"interface {interface.__name__}"
            )
        self._registrations[interface] = (implementation, lifecycle)

    def register_instance(
        self,
        interface: type[T],
        instance: T,
    ) -> None:
        """Register a pre-constructed instance as a singleton."""
        self._registrations[interface] = (type(instance), Lifecycle.SINGLETON)
        self._singletons[interface] = instance

    def resolve(self, interface: type[T], scope_id: str | None = None) -> T:
        """Resolve an implementation for the given interface.

        Automatically injects constructor dependencies.
        """
        if interface not in self._registrations:
            type_name = getattr(interface, "__name__", str(interface))
            raise KeyError(f"No registration found for interface: {type_name}")

        implementation, lifecycle = self._registrations[interface]

        if lifecycle == Lifecycle.SINGLETON:
            if interface not in self._singletons:
                self._singletons[interface] = self._create_instance(implementation)
            return self._singletons[interface]

        if lifecycle == Lifecycle.SCOPED:
            if scope_id is None:
                raise ValueError(
                    f"Cannot resolve scoped service {interface.__name__} without scope_id"
                )
            scope_cache = self._scoped_instances.setdefault(scope_id, {})
            if interface not in scope_cache:
                scope_cache[interface] = self._create_instance(implementation)
            return scope_cache[interface]

        return self._create_instance(implementation)

    def _create_instance(self, implementation: type[T]) -> T:
        """Create an instance with constructor injection."""
        sig = inspect.signature(implementation.__init__)
        params = list(sig.parameters.items())

        if params and params[0][0] == "self":
            params = params[1:]

        # Resolve string annotations (from __future__ import annotations)
        try:
            type_hints = typing.get_type_hints(implementation.__init__)
        except Exception:
            type_hints = {}

        # Fallback: resolve string annotations manually using eval in class globals
        for name, param in sig.parameters.items():
            if name not in type_hints and isinstance(param.annotation, str):
                try:
                    type_hints[name] = eval(param.annotation, implementation.__init__.__globals__)
                except Exception:
                    type_hints[name] = param.annotation

        kwargs: dict[str, Any] = {}
        for name, param in params:
            # Skip *args and **kwargs
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            # Use resolved type hint if available, otherwise fall back to raw annotation
            param_type = type_hints.get(name, param.annotation)

            # If no annotation at all, skip or error
            if param_type is inspect.Parameter.empty:
                if param.default is inspect.Parameter.empty:
                    raise RuntimeError(
                        f"Cannot inject parameter '{name}' in {implementation.__name__}: "
                        "missing type annotation"
                    )
                continue

            # Handle Optional[X] and Union types (typing.Optional and X | None)
            origin = getattr(param_type, "__origin__", None)
            args = getattr(param_type, "__args__", ())

            # Python 3.10+ UnionType (X | None) doesn't have __origin__
            if origin is None and hasattr(param_type, "__args__") and not hasattr(param_type, "__name__"):
                if isinstance(param_type, types.UnionType):
                    origin = types.UnionType
                    args = param_type.__args__

            if origin is not None:
                if len(args) == 2 and type(None) in args:
                    inner_type = next(a for a in args if a is not type(None))
                    try:
                        kwargs[name] = self.resolve(inner_type)
                        continue
                    except KeyError:
                        if param.default is not inspect.Parameter.empty:
                            continue
                        raise

            # Skip built-in types that are not registered (str, int, float, bool, etc.)
            if param_type in (str, int, float, bool, list, dict, set, tuple):
                if param.default is not inspect.Parameter.empty:
                    continue
                raise RuntimeError(
                    f"Cannot inject built-in parameter '{name}' in {implementation.__name__}: "
                    "no default value provided"
                )

            try:
                kwargs[name] = self.resolve(param_type)
            except KeyError:
                if param.default is not inspect.Parameter.empty:
                    continue
                raise

        return implementation(**kwargs)

    def create_scope(self, scope_id: str) -> "ScopedContainer":
        """Create a scoped container for dependency resolution."""
        return ScopedContainer(self, scope_id)

    def dispose(self) -> None:
        """Dispose all singleton instances that support disposal."""
        for instance in self._singletons.values():
            if hasattr(instance, "dispose") and callable(getattr(instance, "dispose")):
                instance.dispose()
        self._singletons.clear()
        self._scoped_instances.clear()


class ScopedContainer:
    """A scoped view of the ServiceContainer."""

    def __init__(self, parent: ServiceContainer, scope_id: str) -> None:
        self._parent = parent
        self._scope_id = scope_id

    def resolve(self, interface: type[T]) -> T:
        """Resolve a service within this scope."""
        return self._parent.resolve(interface, scope_id=self._scope_id)

    def __enter__(self) -> "ScopedContainer":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up scoped instances when exiting the context."""
        if self._scope_id in self._parent._scoped_instances:
            for instance in self._parent._scoped_instances[self._scope_id].values():
                if hasattr(instance, "dispose") and callable(getattr(instance, "dispose")):
                    instance.dispose()
            del self._parent._scoped_instances[self._scope_id]
