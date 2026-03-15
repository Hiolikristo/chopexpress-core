from backend.dispatch_service import DispatchService

service = DispatchService()

service.add_drivers(
    [
        {
            "id": "DRV-001",
            "zone": "north",
            "tier": "professional",
            "online": True,
            "current_lat": 40.10,
            "current_lng": -82.98,
        },
        {
            "id": "DRV-002",
            "zone": "central",
            "tier": "elite",
            "online": True,
            "current_lat": 39.98,
            "current_lng": -83.00,
        },
    ]
)

order = {
    "id": "ORD-1001",
    "zone": "north",
    "merchant_name": "KFC Morse Rd",
    "merchant_type": "Fast Food",
    "pickup_miles": 1.4,
    "dropoff_miles": 3.9,
    "return_buffer_miles": 1.8,
    "pickup_minutes": 4.0,
    "delivery_minutes": 14.0,
    "merchant_delay_minutes": 7.0,
    "traffic_multiplier": 1.22,
    "tip": 3.5,
    "customer_fee": 7.99,
    "batch_size": 1,
    "is_rush_hour": True,
    "is_bad_weather": False,
    "is_apartment_dropoff": True,
    "is_gated_dropoff": False,
}

result = service.create_and_dispatch_order(order)

print(result["decision"])
print(service.list_orders())
print(service.get_events())