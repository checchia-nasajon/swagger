import pytest
from routing.entities.location import Location


def test_location_add_and_get_distance():
    accessibility = {'pytest_accessibility1', 'pytest_accessibility1'}
    location = Location(name='pytest_name', accessibility=accessibility, time_windows=[], demand=1, service_time=0)
    location.add_distance_to_another_location('pytest_destiny', 100)
    assert location.distance_to('pytest_destiny') == 100


def test_location_get_undefined_distance():
    accessibility = {'pytest_accessibility1', 'pytest_accessibility1'}
    location = Location(name='pytest_name', accessibility=accessibility, time_windows=[], demand=1, service_time=0)
    location.add_distance_to_another_location('pytest_destiny', 100)
    with pytest.raises(KeyError):
        location.distance_to('undefined') == 100
