import pytest
from routing.services.vehicles import VehiclesService
from routing.entities.vehicle import Vehicle


def get_vechicles_service():
    vehicles_info = [
        ('test_truck', 3, 'truck'),
        ('test_car', 0, 'car')
    ]
    vehicles = []
    for vehicle_info in vehicles_info:
        vehicle = Vehicle(*vehicle_info)
        vehicles.append(vehicle)
    vehicles_service = VehiclesService(vehicles)
    return vehicles_info, vehicles_service


def test_get_name_from_index():
    vehicles_info, vehicles_service = get_vechicles_service()
    for index, vehicle_info in enumerate(vehicles_info):
        assert vehicles_service.get_name_from_index(index) == vehicle_info[0]


def test_num_vehicles():
    vehicles_info, vehicles_service = get_vechicles_service()
    assert vehicles_service.get_num_vehicles() == len(vehicles_info)


def test_get_vehicle_max_load_weight_by_index():
    vehicles_info, vehicles_service = get_vechicles_service()
    assert vehicles_service.get_vehicle_max_load_weight_by_index(0) == 3
    assert vehicles_service.get_vehicle_max_load_weight_by_index(1) == 0


def test_get_vehicles_max_load_weights():
    vehicles_info, vehicles_service = get_vechicles_service()
    assert vehicles_service.get_vehicles_max_load_weights() == [3, 0]
