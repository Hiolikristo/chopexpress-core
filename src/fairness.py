def calculate_driver_pay(distance_miles, trip_minutes, wait_pickup, wait_dropoff):

    DISTANCE_RATE = 1.00
    TIME_RATE = 0.30
    MIN_PAY = 5.00

    WAIT_RATE = 0.30
    WAIT_CAP = 3.00

    RETURN_BUFFER_RATE = 0.40

    distance_pay = distance_miles * DISTANCE_RATE
    time_pay = trip_minutes * TIME_RATE

    dominant_pay = max(distance_pay, time_pay)
    base_pay = max(dominant_pay, MIN_PAY)

    pickup_wait_pay = min(wait_pickup * WAIT_RATE, WAIT_CAP)
    drop_wait_pay = min(wait_dropoff * WAIT_RATE, WAIT_CAP)

    return_buffer = distance_miles * RETURN_BUFFER_RATE

    final_pay = base_pay + pickup_wait_pay + drop_wait_pay + return_buffer

    return {
        "distance_pay": distance_pay,
        "time_pay": time_pay,
        "dominant_pay": dominant_pay,
        "base_pay": base_pay,
        "pickup_wait_pay": pickup_wait_pay,
        "drop_wait_pay": drop_wait_pay,
        "return_buffer": return_buffer,
        "final_pay": final_pay
    }