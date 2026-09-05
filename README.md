# Login Plans

Sistema avanzado de autenticación y gestión de planes construido con Python.

## Arquitectura

El proyecto evolucionará progresivamente hacia una arquitectura basada en:

- Clean Architecture
- Domain-Driven Design
- CQRS
- Domain Events
- Event-Driven Architecture
- PostgreSQL
- Redis
- Observabilidad
- Testing
- Seguridad avanzada

## Testing Strategy

The project uses multiple testing layers:

- Unit tests
- Application tests
- Infrastructure integration tests
- API tests
- Architecture tests
- Regression tests
- Coverage analysis
- Mutation testing

Critical existing behavior is protected by regression tests.

A change is not considered complete if it:

1. breaks existing tests;
2. violates architectural boundaries;
3. decreases enforced coverage;
4. breaks critical regression scenarios.
