import pytest
from routing.services.penalty import calc_depot_distance
from routing.services.locations import LocationsService
from routing.entities.location import Location
from routing.entities.location import TimeWindow


def get_locations_service():
    locations_info = [
        ('test_loc_deposit', ['truck', 'car'], [TimeWindow(0 * 60, 24 * 60)], 0, 0, True),
        ('test_loc_A', ['truck'], [TimeWindow(8 * 60, 20 * 60)], 2, 10, False),
        ('test_loc_B', ['truck'], [TimeWindow(0 * 60, 24 * 60)], 1, 0, False),
        ('test_loc_C', ['car'], [TimeWindow(0 * 60, 24 * 60)], 0, 10, False)
    ]
    locations = []

    for location_info in locations_info:
        location = Location(*location_info)
        for destiny_info in locations_info:
            if destiny_info is not location_info:
                location.add_distance_to_another_location(destiny_info[0], 2)
        locations.append(location)

    locations_service = LocationsService(locations=locations)
    return locations_info, locations_service


def test_calc_depot_distance():
    locations_info, locations_service = get_locations_service()
    location = locations_service.locations[1]

    depot_penalty = calc_depot_distance(locations_service, location)
    assert depot_penalty == 2 * 2 + 10 + 24 * 60
