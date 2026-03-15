def apply_driver_migration(drivers, pressure_map):

    hot_zones = []

    for zone, data in pressure_map.items():

        if data.get("is_hot_zone", False):
            hot_zones.append(zone)

    if not hot_zones:
        return drivers

    updated_drivers = []

    for driver in drivers:

        driver_copy = dict(driver)

        zone = driver_copy.get("zone")
        busy = driver_copy.get("is_busy", False)
        flexible = driver_copy.get("is_flexible", True)

        if not busy and flexible and zone not in hot_zones:

            driver_copy["previous_zone"] = zone
            driver_copy["zone"] = hot_zones[0]
            driver_copy["migrated"] = True

        else:

            driver_copy["migrated"] = False

        updated_drivers.append(driver_copy)

    return updated_drivers