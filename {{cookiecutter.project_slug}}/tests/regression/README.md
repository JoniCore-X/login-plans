# Regression Test Strategy

## Critical scenarios

| Scenario | Expected behavior |
|---|---|
| User registration | HTTP 201 |
| Email normalization | Email is normalized |
| Duplicate registration | HTTP 409 |
| Password exposure | Password is never returned |
| Password hash exposure | Password hash is never returned |
| Invalid email | HTTP 422 |

## Rule

Any modification that can affect an existing critical scenario
must preserve the corresponding regression test.

## Expansion

As the system grows, add regression coverage for:

- authentication
- login
- logout
- sessions
- refresh tokens
- authorization
- plan creation
- plan updates
- plan retrieval
- plan versioning
- concurrent modifications
- security-sensitive flows
