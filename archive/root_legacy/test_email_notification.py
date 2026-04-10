from src.services.email_services import EmailService


def main() -> None:
    service = EmailService()
    result = service.send_email(
        recipients=["info@chop.express"],
        subject="ChopExpress SMTP test",
        text_content="SMTP test successful. Your ChopExpress Zoho mail pipeline is active.",
        html_content="""
        <h2>SMTP test successful</h2>
        <p>Your ChopExpress Zoho mail pipeline is active.</p>
        """,
        reply_to="support@chop.express",
    )
    print(result)


if __name__ == "__main__":
    main()