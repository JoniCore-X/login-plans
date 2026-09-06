import httpx
import pytest


@pytest.mark.asyncio
async def test_response_includes_trace_id(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "trace@example.com",
            "password": "Strong-password-123!",
        },
    )

    assert "X-Trace-ID" in response.headers

    trace_id = response.headers["X-Trace-ID"]

    assert len(trace_id) == 32
    assert trace_id != "0" * 32


@pytest.mark.asyncio
async def test_trace_id_correlates_with_request_id(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "trace2@example.com",
            "password": "Strong-password-123!",
        },
        headers={"X-Request-ID": "correlation-check"},
    )

    assert response.headers["X-Request-ID"] == "correlation-check"
    assert "X-Trace-ID" in response.headers
