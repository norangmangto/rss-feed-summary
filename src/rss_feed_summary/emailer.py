from typing import List, Dict
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os


def render_email(items: List[Dict], subject: str, template_dir: str = "templates") -> str:
    env = Environment(
        loader=FileSystemLoader(template_dir), autoescape=select_autoescape(["html", "xml"])
    )
    tmpl = env.get_template("email.html.j2")
    return tmpl.render(items=items, subject=subject)

def render_text(items: List[Dict], subject: str) -> str:
    lines = [subject, ""]
    for item in items:
        title = item.get("title", "")
        link = item.get("link", "")
        summary = item.get("summary", "")
        source = item.get("source", "")
        published = item.get("published", "")
        lines.append(f"• {title}")
        if source or published:
            lines.append(f"  {source} {published}".strip())
        lines.append(f"  {link}")
        if summary:
            lines.append(f"  {summary}")
        lines.append("")
    return "\n".join(lines)


def send_email(
    html_body: str,
    smtp_host: str,
    smtp_port: int,
    username: str | None,
    password: str | None,
    mail_from: str,
    mail_to: List[str],
    subject: str,
    use_tls: bool = True,
    text_body: str | None = None,
):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = ", ".join(mail_to)

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if use_tls:
            server.starttls()
        if username and password:
            server.login(username, password)
        server.sendmail(mail_from, mail_to, msg.as_string())