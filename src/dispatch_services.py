from __future__ import annotations

from typing import Any, Dict, Optional

from src.services.email_services import EmailService
from src.services.email_templates import (
    driver_assigned_email,
    driver_offer_email,
    merchant_new_order_email,
    order_completed_email,
    order_created_email,
)


class NotificationEngine:
    def __init__(self, email_service: Optional[EmailService] = None) -> None:
        self.email_service = email_service or EmailService()

    def send_order_created(
        self,
        order: Dict[str, Any],
        customer_email: str,
    ) -> Dict[str, Any]:
        payload = order_created_email(order)
        return self.email_service.send_email(
            recipients=customer_email,
            subject=payload["subject"],
            text_content=payload["text"],
            html_content=payload["html"],
            reply_to="support@chop.express",
        )

    def send_merchant_new_order(
        self,
        order: Dict[str, Any],
        merchant_email: str,
    ) -> Dict[str, Any]:
        payload = merchant_new_order_email(order)
        return self.email_service.send_email(
            recipients=merchant_email,
            subject=payload["subject"],
            text_content=payload["text"],
            html_content=payload["html"],
            reply_to="restaurants@chop.express",
        )

    def send_driver_offer(
        self,
        order: Dict[str, Any],
        driver: Dict[str, Any],
        driver_email: str,
    ) -> Dict[str, Any]:
        payload = driver_offer_email(order, driver)
        return self.email_service.send_email(
            recipients=driver_email,
            subject=payload["subject"],
            text_content=payload["text"],
            html_content=payload["html"],
            reply_to="drivers@chop.express",
        )

    def send_driver_assigned(
        self,
        order: Dict[str, Any],
        driver: Dict[str, Any],
        customer_email: str,
    ) -> Dict[str, Any]:
        payload = driver_assigned_email(order, driver)
        return self.email_service.send_email(
            recipients=customer_email,
            subject=payload["subject"],
            text_content=payload["text"],
            html_content=payload["html"],
            reply_to="support@chop.express",
        )

    def send_order_completed(
        self,
        order: Dict[str, Any],
        customer_email: str,
    ) -> Dict[str, Any]:
        payload = order_completed_email(order)
        return self.email_service.send_email(
            recipients=customer_email,
            subject=payload["subject"],
            text_content=payload["text"],
            html_content=payload["html"],
            reply_to="support@chop.express",
        )