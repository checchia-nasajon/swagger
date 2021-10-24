import uuid

from routing.entities.location import Location
from routing.entities.vehicle import Vehicle
from routing.services.utils import has_accessibility
from enum import Enum, auto
from typing import List, Dict


class BreakType(Enum):
    LUNCH = auto()
    SHORT = auto()


class Break:
    def __init__(self, break_type: BreakType, minimum_start, maximum_start, duration, vehicle_name):
        self.type = break_type
        self.minimum_start = minimum_start
        self.maximum_start = maximum_start
        self.duration = duration
        self._id = self.generate_id(vehicle_name)

    def get_break_id(self):
        return self._id

    def generate_id(self, vehicle_name):
        return f'{vehicle_name}-{self.type}-{str(uuid.uuid4())}'


class VehicleBreaks:
    def __init__(self):
        self.breaks: Dict[str, Break] = {}

    def add_break(self, break_: Break):
        self.breaks[break_.get_break_id()] = break_

    def add_new_break(self, break_type: BreakType,
                      minimum_start, maximum_start,
                      duration, vehicle_name) -> Break:
        break_ = Break(break_type, minimum_start, maximum_start, duration, vehicle_name)
        self.add_break(break_)
        return break_

    def get_lunch_break(self) -> Break:
        for break_ in self.breaks.values():
            if break_.type == BreakType.LUNCH:
                return break_

    def get_breaks_ids(self):
        return self.breaks.keys()

    def get_break_from_id(self, _id):
        return self.breaks[_id]

    def get_type_from_id(self, _id) -> BreakType:
        break_ = self.breaks[_id]
        return break_.type


class VehiclesService:
    def __init__(self, vehicles: List[Vehicle]):
        self.vehicles = vehicles
        self.vehicles_breaks: List[VehicleBreaks] = [VehicleBreaks() for _ in self.vehicles]

    def get_name_from_index(self, index):
        return self.vehicles[index].name

    def get_vehicle_from_index(self, index) -> Vehicle:
        return self.vehicles[index]

    def get_num_vehicles(self):
        return len(self.vehicles)

    def get_allowed_vehicles_to_location(self, location: Location):
        allowed_vehicles = []
        for vehicle_index, vehicle in enumerate(self.vehicles):
            vehicle_types = vehicle.types
            if has_accessibility(vehicle_types, location.accessibility):
                allowed_vehicles.append(vehicle_index)
        return allowed_vehicles

    def get_vehicles_max_load_weights(self):
        return [vehicle.max_load_weight for vehicle in self.vehicles]

    def get_vehicle_max_load_weight_by_index(self, index):
        return self.vehicles[index].max_load_weight

    def get_vehicle_breaks_from_index(self, vehicle_index):
        return self.vehicles_breaks[vehicle_index]

    def add_break_to_vehicle_index(self, vehicle_index, break_: Break):
        self.vehicles_breaks[vehicle_index].add_break(break_)

    def add_new_break_to_vehicle(self, vehicle_index, break_type: BreakType, minimum_start, maximum_start, duration):
        vehicle = self.get_vehicle_from_index(vehicle_index)
        vehicle_breaks = self.vehicles_breaks[vehicle_index]
        break_ = vehicle_breaks.add_new_break(break_type,
                                              minimum_start,
                                              maximum_start,
                                              duration,
                                              vehicle.name)
        return break_
