import httpx
import pytest


@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.asyncio
async def test_invalid_email_error_contract_remains_stable(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "Strong-regression-password-123!",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert "error" in body
    assert body["error"]["code"] == "INVALID_EMAIL"
