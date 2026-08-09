# Security Checklist — M4.11 / v0.4.0

## Authentication
- [x] API key authentication implemented (`AuthPort` + `APIKeyAuthAdapter`)
- [x] Bearer token format supported
- [x] Anonymous access allowed when auth is disabled
- [x] Principal identification and role assignment

## Authorization
- [x] RBAC implemented (`AuthorizationPort` + `RBACAuthorizationAdapter`)
- [x] Wildcard pattern matching for actions and resources
- [x] Admin routes protected with dedicated admin role
- [x] Graceful degradation when authorization is disabled

## Rate Limiting
- [x] Sliding-window rate limiter implemented (`RateLimitPort` + `InMemoryRateLimitAdapter`)
- [x] Per-resource configuration overrides
- [x] HTTP 429 responses with quota headers
- [x] Independent tracking per client

## Audit Logging
- [x] Structured JSON audit logging (`AuditPort` + `StructuredAuditAdapter`)
- [x] All endpoints emit audit events
- [x] Events include timestamp, principal, action, resource, status

## API Security
- [x] Unified error schema (no information leakage)
- [x] Request validation with Pydantic
- [x] Correlation IDs (`request_id`) in all error responses
- [x] Health endpoint does not expose sensitive data

## Transport
- [ ] TLS/HTTPS (deployment responsibility)
- [ ] CORS configuration (deployment responsibility)

## Dependencies
- [x] No external HTTP libraries (stdlib only)
- [x] Minimal dependency footprint
- [x] All dependencies pinned in `pyproject.toml`

## Testing
- [x] 41 security-specific tests PASS
- [x] Authentication bypass tests
- [x] Authorization denial tests
- [x] Rate limit enforcement tests
- [x] Audit event generation tests
- [x] Full regression: 238/238 PASS
