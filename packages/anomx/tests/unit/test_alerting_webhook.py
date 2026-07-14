"""Unit tests for webhook alerter."""

from unittest.mock import MagicMock, patch

from anomx.alerting.webhook import WebhookAlerter
from anomx.config.models import WebhookAlertingSettings


def test_webhook_alerter_posts_json_payload() -> None:
    settings = WebhookAlertingSettings(enabled=True, url="https://example.com/hook")
    alerter = WebhookAlerter(settings)
    response = MagicMock()
    response.status_code = 200
    response.raise_for_status = MagicMock()

    with patch("anomx.alerting.webhook.httpx.post", return_value=response) as post:
        alerter.send({"alert_id": "abc", "summary": "test alert"})

    post.assert_called_once()
    assert post.call_args.kwargs["json"]["alert_id"] == "abc"


def test_webhook_alerter_disabled_is_noop() -> None:
    settings = WebhookAlertingSettings(enabled=False, url="https://example.com/hook")
    alerter = WebhookAlerter(settings)

    with patch("anomx.alerting.webhook.httpx.post") as post:
        alerter.send({"alert_id": "abc"})

    post.assert_not_called()
