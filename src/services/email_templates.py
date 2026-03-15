from __future__ import annotations

from typing import Any, Dict


def _wrap_html(title: str, body_html: str) -> str:
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
</head>
<body style="font-family: Arial, Helvetica, sans-serif; background:#f7f7f7; margin:0; padding:24px;">
  <div style="max-width:640px; margin:0 auto; background:#ffffff; border-radius:12px; padding:32px; border:1px solid #e5e7eb;">
    <h2 style="margin-top:0; color:#111827;">{title}</h2>
    <div style="color:#374151; line-height:1.6;">
      {body_html}
    </div>
    <hr style="border:none; border-top:1px solid #e5e7eb; margin:24px 0;" />
    <p style="font-size:12px; color:#6b7280; margin:0;">
      ChopExpress automated notification
    </p>
  </div>
</body>
</html>
"""


def order_created_email(order: Dict[str, Any]) -> Dict[str, str]:
    order_id = order.get("order_id", "UNKNOWN")
    customer_name = order.get("customer_name", "Customer")
    merchant_name = order.get("merchant_name", "Merchant")
    dropoff = order.get("dropoff_address", "N/A")

    subject = f"Order created: {order_id}"
    text = (
        f"Hello {customer_name},\n\n"
        f"Your order {order_id} has been created.\n"
        f"Merchant: {merchant_name}\n"
        f"Dropoff: {dropoff}\n\n"
        f"Thank you for choosing ChopExpress."
    )
    html = _wrap_html(
        "Your order has been created",
        f"""
        <p>Hello {customer_name},</p>
        <p>Your order <strong>{order_id}</strong> has been created.</p>
        <ul>
          <li><strong>Merchant:</strong> {merchant_name}</li>
          <li><strong>Dropoff:</strong> {dropoff}</li>
        </ul>
        <p>Thank you for choosing ChopExpress.</p>
        """,
    )
    return {"subject": subject, "text": text, "html": html}


def merchant_new_order_email(order: Dict[str, Any]) -> Dict[str, str]:
    order_id = order.get("order_id", "UNKNOWN")
    merchant_name = order.get("merchant_name", "Merchant")
    items = order.get("items", [])

    items_text = "\n".join(f"- {item}" for item in items) if items else "- Order items unavailable"
    items_html = "".join(f"<li>{item}</li>" for item in items) if items else "<li>Order items unavailable</li>"

    subject = f"New incoming order: {order_id}"
    text = (
        f"{merchant_name},\n\n"
        f"A new order has been placed.\n"
        f"Order ID: {order_id}\n"
        f"Items:\n{items_text}\n"
    )
    html = _wrap_html(
        "New incoming order",
        f"""
        <p>{merchant_name},</p>
        <p>A new order has been placed.</p>
        <p><strong>Order ID:</strong> {order_id}</p>
        <p><strong>Items:</strong></p>
        <ul>{items_html}</ul>
        """,
    )
    return {"subject": subject, "text": text, "html": html}


def driver_offer_email(order: Dict[str, Any], driver: Dict[str, Any]) -> Dict[str, str]:
    order_id = order.get("order_id", "UNKNOWN")
    driver_name = driver.get("name", "Driver")
    pickup = order.get("pickup_address", "N/A")
    dropoff = order.get("dropoff_address", "N/A")
    payout = order.get("estimated_payout", "N/A")

    subject = f"New delivery offer: {order_id}"
    text = (
        f"Hello {driver_name},\n\n"
        f"You have a new delivery offer.\n"
        f"Order ID: {order_id}\n"
        f"Pickup: {pickup}\n"
        f"Dropoff: {dropoff}\n"
        f"Estimated payout: {payout}\n"
    )
    html = _wrap_html(
        "New delivery offer",
        f"""
        <p>Hello {driver_name},</p>
        <p>You have a new delivery offer.</p>
        <ul>
          <li><strong>Order ID:</strong> {order_id}</li>
          <li><strong>Pickup:</strong> {pickup}</li>
          <li><strong>Dropoff:</strong> {dropoff}</li>
          <li><strong>Estimated payout:</strong> {payout}</li>
        </ul>
        """,
    )
    return {"subject": subject, "text": text, "html": html}


def driver_assigned_email(order: Dict[str, Any], driver: Dict[str, Any]) -> Dict[str, str]:
    order_id = order.get("order_id", "UNKNOWN")
    customer_name = order.get("customer_name", "Customer")
    driver_name = driver.get("name", "Driver")
    vehicle = driver.get("vehicle", "Vehicle details unavailable")

    subject = f"Driver assigned: {order_id}"
    text = (
        f"Hello {customer_name},\n\n"
        f"A driver has been assigned to your order.\n"
        f"Order ID: {order_id}\n"
        f"Driver: {driver_name}\n"
        f"Vehicle: {vehicle}\n"
    )
    html = _wrap_html(
        "A driver has been assigned",
        f"""
        <p>Hello {customer_name},</p>
        <p>A driver has been assigned to your order.</p>
        <ul>
          <li><strong>Order ID:</strong> {order_id}</li>
          <li><strong>Driver:</strong> {driver_name}</li>
          <li><strong>Vehicle:</strong> {vehicle}</li>
        </ul>
        """,
    )
    return {"subject": subject, "text": text, "html": html}


def order_completed_email(order: Dict[str, Any]) -> Dict[str, str]:
    order_id = order.get("order_id", "UNKNOWN")
    customer_name = order.get("customer_name", "Customer")
    delivered_at = order.get("delivered_at", "N/A")

    subject = f"Order completed: {order_id}"
    text = (
        f"Hello {customer_name},\n\n"
        f"Your order has been delivered.\n"
        f"Order ID: {order_id}\n"
        f"Delivered at: {delivered_at}\n\n"
        f"Thank you for using ChopExpress."
    )
    html = _wrap_html(
        "Your order was delivered",
        f"""
        <p>Hello {customer_name},</p>
        <p>Your order has been delivered.</p>
        <ul>
          <li><strong>Order ID:</strong> {order_id}</li>
          <li><strong>Delivered at:</strong> {delivered_at}</li>
        </ul>
        <p>Thank you for using ChopExpress.</p>
        """,
    )
    return {"subject": subject, "text": text, "html": html}