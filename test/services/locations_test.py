import pytest
from routing.services.locations import LocationsService
from routing.entities.location import Location, TimeWindow


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
                location.add_distance_to_another_location(destiny_info[0], 1)
        locations.append(location)

    locations_service = LocationsService(locations=locations)
    return locations_info, locations_service


def test_num_locations():
    locations_info, locations_service = get_locations_service()
    assert locations_service.get_num_locations() == len(locations_info)


def test_get_depot_index():
    locations_info, locations_service = get_locations_service()
    depot_index = None
    for index, location_info in enumerate(locations_info):
        if location_info[2]:
            depot_index = index
            break
    assert locations_service.get_depot_index() == depot_index


def test_get_name_from_index():
    locations_info, locations_service = get_locations_service()
    for index, location_info in enumerate(locations_info):
        assert locations_service.get_name_from_index(index) == location_info[0]


def test_get_name_from_index_exception_from_invalid_index():
    locations_info, locations_service = get_locations_service()
    with pytest.raises(IndexError):
        locations_service.get_name_from_index(len(locations_info))


def test_distance_by_index_same_index():
    locations_info, locations_service = get_locations_service()
    for index, location_info in enumerate(locations_info):
        assert locations_service.get_distance_by_index({location_info[1][0]}, index, index) == 0


def test_distance_by_index_same_vehicle_type():
    _, locations_service = get_locations_service()
    assert locations_service.get_distance_by_index({'truck'}, 1, 2) == 1
    assert locations_service.get_distance_by_index({'truck'}, 2, 1) == 1
    assert locations_service.get_distance_by_index({'truck'}, 0, 1) == 1
    assert locations_service.get_distance_by_index({'truck'}, 0, 2) == 1


def test_distance_by_index_invalid_vehicle_type():
    _, locations_service = get_locations_service()
    assert locations_service.get_distance_by_index({'car'}, 1, 2) == LocationsService.infinity
    assert locations_service.get_distance_by_index({'car'}, 2, 1) == LocationsService.infinity


def test_get_location_forbidden_time_window_by_index():
    _, locations_service = get_locations_service()
    assert locations_service.get_location_forbidden_time_window_by_index(
        1)['start'] == [0 * 60, (20 * 60) + 1]
    assert locations_service.get_location_forbidden_time_window_by_index(
        1)['end'] == [(8 * 60) - 1, 24 * 60]
    assert locations_service.get_location_forbidden_time_window_by_index(2)['start'] == []
    assert locations_service.get_location_forbidden_time_window_by_index(2)['end'] == []


def test_get_demand_by_index():
    _, locations_service = get_locations_service()
    assert locations_service.get_demand_by_index(0) == 0
    assert locations_service.get_demand_by_index(1) == 2
