# Sergio Knowledge OS — Architecture

## Overview
SKOS follows Clean Architecture with explicit dependency direction:

```
Application Layer (services)
  - ImportOrchestrator, AIService
Domain Layer (models, value objects)
  - ConfigScope, ConfigPath, SecretRef
  - ChatMessage, ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResult
  - DomainEvent
Infrastructure Layer (adapters)
  - HierarchicalConfigAdapter, EnvSecretManagerAdapter
  - InMemoryEventBus
  - OpenAIAdapter, GeminiAdapter, KimiAdapter, ClaudeAdapter, OllamaAdapter
  - AIProviderRegistry
Ports (abstract interfaces)
  - ConfigurationPort, SecretManagerPort, EventBusPort, AIProviderPort
DI Container
  - ServiceContainer
```

## Dependency Rules
1. Domain knows nothing about infrastructure or application
2. Application knows domain and ports, never concrete adapters
3. Infrastructure implements ports, can use any external library
4. DI Container wires everything at startup

## AI Provider Abstraction
All providers implement AIProviderPort:
- chat(request: ChatRequest) -> ChatResponse
- embed(request: EmbeddingRequest) -> EmbeddingResult
- health_check() -> bool
- list_models() -> list[str]

Adapters use urllib.request (stdlib) — zero external HTTP dependencies.
