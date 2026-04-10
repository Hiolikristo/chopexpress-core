def notify_driver_new_order(driver, order):

    html = f"""
    <h2>New Delivery Available</h2>
    <p>Pickup: {order['restaurant']}</p>
    <p>Dropoff: {order['customer_address']}</p>
    <p>Payout: ${order['payout']}</p>
    """

    send_email(
        driver["email"],
        "New ChopExpress Delivery Available",
        html
    )