from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.infrastructure.email.resend_sender import ResendEmailSender


def _make_sender() -> ResendEmailSender:
    return ResendEmailSender(
        api_key="re_test_key",
        from_email="noreply@example.com",
        verify_base_url="https://app.example.com/verify",
    )


@pytest.mark.asyncio
async def test_resend_sender_calls_api_correctly() -> None:
    sender = _make_sender()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(return_value=mock_response),
    ) as mock_post:
        await sender.send_verification_email(
            "user@example.com",
            "test_token_123",
        )

    mock_post.assert_awaited_once()

    call = mock_post.call_args

    assert call.args[0] == "https://api.resend.com/emails"
    assert call.kwargs["headers"]["Authorization"] == "Bearer re_test_key"
    assert call.kwargs["json"]["to"] == ["user@example.com"]
    assert call.kwargs["json"]["from"] == "noreply@example.com"
    assert "test_token_123" in call.kwargs["json"]["html"]
    assert (
        "https://app.example.com/verify?token=test_token_123"
        in call.kwargs["json"]["html"]
    )


@pytest.mark.asyncio
async def test_resend_sender_propagates_http_error() -> None:
    sender = _make_sender()

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized",
        request=MagicMock(),
        response=MagicMock(),
    )

    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(return_value=mock_response),
    ):
        with pytest.raises(httpx.HTTPStatusError):
            await sender.send_verification_email(
                "user@example.com",
                "test_token_123",
            )


@pytest.mark.asyncio
async def test_console_sender_prints_token_in_dev(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from app.infrastructure.email.console_sender import (
        ConsoleEmailSender,
    )

    sender = ConsoleEmailSender(is_production=False)

    await sender.send_verification_email(
        "user@example.com",
        "dev_token_abc",
    )

    out = capsys.readouterr().out

    assert "VERIFICATION TOKEN FOR: user@example.com" in out
    assert "dev_token_abc" in out


@pytest.mark.asyncio
async def test_console_sender_hides_token_in_prod(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from structlog.testing import capture_logs

    from app.infrastructure.email.console_sender import (
        ConsoleEmailSender,
    )

    sender = ConsoleEmailSender(is_production=True)

    with capture_logs() as logs:
        await sender.send_verification_email(
            "user@example.com",
            "secret_token_xyz",
        )

    out = capsys.readouterr().out

    assert "VERIFICATION TOKEN" not in out
    assert "secret_token_xyz" not in out

    assert logs
    logged = logs[0]
    assert logged["event"] == "verification_email_sent"
    assert logged["token"] == "***"
