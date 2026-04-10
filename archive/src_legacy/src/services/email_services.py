from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Iterable, List, Optional


def _load_env_file(env_path: str = ".env") -> None:
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


_load_env_file()


@dataclass
class EmailConfig:
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str = "ChopExpress"
    use_tls: bool = True

    @classmethod
    def from_env(cls) -> "EmailConfig":
        smtp_host = os.getenv("SMTP_HOST", "smtp.zoho.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        smtp_from_email = os.getenv("SMTP_FROM_EMAIL", smtp_username)
        smtp_from_name = os.getenv("SMTP_FROM_NAME", "ChopExpress")
        use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "on"}

        missing = [
            name
            for name, value in {
                "SMTP_USERNAME": smtp_username,
                "SMTP_PASSWORD": smtp_password,
                "SMTP_FROM_EMAIL": smtp_from_email,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"Missing required SMTP environment variables: {', '.join(missing)}")

        return cls(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            smtp_from_email=smtp_from_email,
            smtp_from_name=smtp_from_name,
            use_tls=use_tls,
        )


class EmailService:
    def __init__(self, config: Optional[EmailConfig] = None) -> None:
        self.config = config or EmailConfig.from_env()

    @staticmethod
    def _normalize_recipients(recipients: Iterable[str] | str) -> List[str]:
        if isinstance(recipients, str):
            recipients = [recipients]
        normalized = [r.strip() for r in recipients if r and r.strip()]
        if not normalized:
            raise ValueError("At least one recipient email is required.")
        return normalized

    def send_email(
        self,
        recipients: Iterable[str] | str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        to_list = self._normalize_recipients(recipients)

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.config.smtp_from_name} <{self.config.smtp_from_email}>"
        message["To"] = ", ".join(to_list)
        if reply_to:
            message["Reply-To"] = reply_to

        message.attach(MIMEText(text_content, "plain", "utf-8"))
        if html_content:
            message.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=30) as server:
            if self.config.use_tls:
                server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            server.sendmail(self.config.smtp_from_email, to_list, message.as_string())

        return {
            "status": "sent",
            "subject": subject,
            "recipients": to_list,
            "from": self.config.smtp_from_email,
        }