# Sergio Knowledge OS — Architecture

## Overview
SKOS follows Clean Architecture with explicit dependency direction:

```
┌─────────────────────────────────────────┐
│  Application Layer (services)           │
│  - ImportOrchestrator                   │
│  - (M4.2+) RAGService                   │
├─────────────────────────────────────────┤
│  Domain Layer (models, value objects)   │
│  - ConfigScope, ConfigPath, SecretRef   │
│  - DomainEvent                          │
├─────────────────────────────────────────┤
│  Infrastructure Layer (adapters)        │
│  - HierarchicalConfigAdapter            │
│  - EnvSecretManagerAdapter              │
│  - InMemoryEventBus                     │
│  - (M4.3+) EmbeddingAdapter             │
│  - (M4.4+) VectorStoreAdapter           │
├─────────────────────────────────────────┤
│  Ports (abstract interfaces)            │
│  - ConfigurationPort                    │
│  - SecretManagerPort                    │
│  - EventBusPort                         │
│  - (M4+) AIEmbeddingPort                │
│  - (M4+) VectorStorePort                │
├─────────────────────────────────────────┤
│  DI Container                           │
│  - ServiceContainer (singleton/scope/   │
│    transient lifecycles)                │
└─────────────────────────────────────────┘
```

## Dependency Rules
1. **Domain** knows nothing about infrastructure or application
2. **Application** knows domain and ports, never concrete adapters
3. **Infrastructure** implements ports, can use any external library
4. **DI Container** wires everything at startup

## Module Structure
```
skos/
├── m2/              # Frozen import engine
├── m3/              # Frozen database layer
└── m4/
    ├── di/          # Dependency injection
    ├── domain/      # Value objects, entities
    ├── infrastructure/
    │   ├── adapters/   # Concrete implementations
    │   └── ports/      # Abstract interfaces
    └── application/
        └── services/   # Use cases / orchestrators
```

## Event-Driven Communication
The `EventBusPort` decouples components:
- `import.started` → triggers indexing
- `import.completed` → triggers embedding generation
- `import.failed` → triggers alerting

## Configuration Hierarchy
```
system (defaults)
  └── tenant
       └── workspace
            └── project
                 └── user
```
Each level can override parent values. Environment variables (`SKOS_M4_*`) override system defaults.
