from math import sqrt

def distance(loc1, loc2):
    # Example implementation assuming loc1 and loc2 are (x, y) tuples
    return sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2)

class EconomicMilesEngine:

    def calculate_economic_miles(self, driver_loc, pickup_loc, drop_loc):
        driver_to_pickup = distance(driver_loc, pickup_loc)
        pickup_to_drop = distance(pickup_loc, drop_loc)

        reposition = self.estimate_return(drop_loc)

        economic_miles = driver_to_pickup + pickup_to_drop + reposition

        return {
            "driver_to_pickup": driver_to_pickup,
            "pickup_to_drop": pickup_to_drop,
            "reposition": reposition,
            "economic_miles": economic_miles
        }