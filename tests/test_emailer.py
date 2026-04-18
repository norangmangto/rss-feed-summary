import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from rss_feed_summary.emailer import render_email, render_text, send_email

TEMPLATE_DIR = str(Path(__file__).parent.parent / "templates")

SAMPLE_ITEMS = [
    {
        "title": "Test Article",
        "link": "https://example.com/article",
        "published": "Mon, 01 Jan 2024",
        "source": "Example Blog",
        "summary": "This is a short summary.",
        "thumbnail": "https://example.com/thumb.jpg",
    }
]


# --- render_email ---

def test_render_email_contains_subject():
    html = render_email(SAMPLE_ITEMS, "My Subject", template_dir=TEMPLATE_DIR)
    assert "My Subject" in html


def test_render_email_contains_title():
    html = render_email(SAMPLE_ITEMS, "Subject", template_dir=TEMPLATE_DIR)
    assert "Test Article" in html


def test_render_email_contains_link():
    html = render_email(SAMPLE_ITEMS, "Subject", template_dir=TEMPLATE_DIR)
    assert "https://example.com/article" in html


def test_render_email_contains_thumbnail():
    html = render_email(SAMPLE_ITEMS, "Subject", template_dir=TEMPLATE_DIR)
    assert "https://example.com/thumb.jpg" in html


def test_render_email_no_thumbnail_omits_img():
    items = [{**SAMPLE_ITEMS[0], "thumbnail": ""}]
    html = render_email(items, "Subject", template_dir=TEMPLATE_DIR)
    assert "<img" not in html


def test_render_email_empty_items():
    html = render_email([], "Empty", template_dir=TEMPLATE_DIR)
    assert "Empty" in html


# --- render_text ---

def test_render_text_contains_title():
    text = render_text(SAMPLE_ITEMS, "Subject")
    assert "Test Article" in text


def test_render_text_contains_link():
    text = render_text(SAMPLE_ITEMS, "Subject")
    assert "https://example.com/article" in text


def test_render_text_contains_summary():
    text = render_text(SAMPLE_ITEMS, "Subject")
    assert "This is a short summary." in text


def test_render_text_contains_subject():
    text = render_text(SAMPLE_ITEMS, "My Daily Digest")
    assert "My Daily Digest" in text


def test_render_text_empty_items():
    text = render_text([], "Subject")
    assert "Subject" in text


# --- send_email ---

def test_send_email_calls_sendmail():
    with patch("rss_feed_summary.emailer.smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_server
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_email(
            html_body="<p>Hello</p>",
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            mail_from="from@example.com",
            mail_to=["to@example.com"],
            subject="Test",
            use_tls=True,
        )

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pass")
        mock_server.sendmail.assert_called_once()


def test_send_email_skips_login_without_credentials():
    with patch("rss_feed_summary.emailer.smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_server
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_email(
            html_body="<p>Hello</p>",
            smtp_host="smtp.example.com",
            smtp_port=25,
            username=None,
            password=None,
            mail_from="from@example.com",
            mail_to=["to@example.com"],
            subject="Test",
            use_tls=False,
        )

        mock_server.login.assert_not_called()
        mock_server.starttls.assert_not_called()


def test_send_email_attaches_plain_text():
    import email as email_lib

    with patch("rss_feed_summary.emailer.smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_server
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_email(
            html_body="<p>Hello</p>",
            smtp_host="smtp.example.com",
            smtp_port=587,
            username=None,
            password=None,
            mail_from="from@example.com",
            mail_to=["to@example.com"],
            subject="Test",
            use_tls=False,
            text_body="Hello plain",
        )

        raw_message = mock_server.sendmail.call_args[0][2]
        parsed = email_lib.message_from_string(raw_message)
        plain_parts = [
            part.get_payload(decode=True).decode()
            for part in parsed.walk()
            if part.get_content_type() == "text/plain"
        ]
        assert any("Hello plain" in p for p in plain_parts)
