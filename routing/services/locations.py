import intervals
from typing import List
from routing.entities.location import Location
from routing.entities.exception import LocationNameError
from routing.settings import INFINITY
from routing.services.utils import has_accessibility


class LocationsService:
    infinity = INFINITY

    def __init__(self, locations: List[Location], penalty_strategy=None, num_depot_copies=0):
        self.locations = locations
        self.set_depot_index()
        self.add_depot_copies(num_depot_copies)
        self.build_distance_map()
        self.set_depot_index()
        self.penalty_strategy = penalty_strategy

    def set_depot_index(self):
        for index, location in enumerate(self.locations):
            if location.is_depot:
                self.depot_index = index
                return

    def get_depot(self):
        depot_index = self.get_depot_index()
        depot = self.get_location_from_index(depot_index)
        return depot

    def add_depot_copies(self, num_depot_copies):
        depot = self.get_depot()
        for i in range(num_depot_copies):
            depot_copy = depot.shallow_copy()
            # depot_copy.add_distance_to_another_location('Deposito', self.infinity)
            self.locations.append(depot_copy)
        # depot.service_time = 0

    def set_refill_depots_demand(self, refill_depot_demand):
        for location in self.locations:
            if location.is_depot and location.is_clone:
                location.demand = -refill_depot_demand

    def get_refill_depots_nodes(self):
        refill_depots_nodes = []
        for location_node, location in enumerate(self.locations):
            if location.demand < 0:
                refill_depots_nodes.append(location_node)
        return refill_depots_nodes

    def build_distance_map(self):
        self.distance_map = {
            location.name: location.distance_map for location in self.locations
        }

    def get_location_from_index(self, index):
        return self.locations[index]

    def get_location_from_name(self, name):
        for location in self.locations:
            if location.name == name:
                return location
        else:
            raise LocationNameError(name)

    def get_name_from_index(self, index):
        return self.get_location_from_index(index).name

    def get_distance_by_index(self, vehicle_types, from_index, to_index):
        from_name = self.get_name_from_index(from_index)
        to_name = self.get_name_from_index(to_index)
        to_location = self.get_location_from_index(to_index)
        from_location = self.get_location_from_index(from_index)
        if has_accessibility(vehicle_types, to_location) and has_accessibility(vehicle_types, from_location):
            distance = self.distance_map[from_name].get(to_name, self.infinity)
        else:
            distance = self.infinity
        return distance

    def has_penalty(self, location: Location):
        """ Check if the location has a penalty if it is dropped.
            - The cloned deposit can be dropped without any penalty
        Returns:
            Bool: True if location has penalty, false otherwise
        """
        return not (location.is_depot and not location.is_clone)

    def get_drop_penalty(self, location: Location):
        penalty = 0
        if location.high_priority:
            penalty = self.infinity
        elif not location.is_depot:
            penalty = self.penalty_strategy(self, location=location)
        return penalty

    def get_drop_penalty_by_index(self, location_index):
        location = self.get_location_from_index(location_index)
        return self.get_drop_penalty(location)

    def get_service_time_by_index(self, from_index):
        from_location = self.get_location_from_index(from_index)
        return from_location.service_time

    def get_demand_by_index(self, index):
        location = self.get_location_from_index(index)
        return location.demand

    def get_location_forbidden_time_window(self, location):
        allowed_intervals = intervals.empty()
        for time_window in location.time_windows:
            start = time_window.start
            end = time_window.end
            allowed_interval = intervals.closed(start, end)
            allowed_intervals = allowed_intervals | allowed_interval
        full_day_interval = intervals.closed(0, 24 * 60)
        forbidden_intervals = full_day_interval - allowed_intervals
        forbidden_start = []
        forbidden_end = []
        for interval in forbidden_intervals:
            start_modifier = 0 if interval.left else 1
            end_modifier = 0 if interval.right else -1
            if not interval.is_empty():
                forbidden_start.append(interval.lower + start_modifier)
                forbidden_end.append(interval.upper + end_modifier)
        return {'start': forbidden_start, 'end': forbidden_end}

    def get_location_forbidden_time_window_by_index(self, index):
        location = self.get_location_from_index(index)
        time_windows = self.get_location_forbidden_time_window(location)
        return time_windows

    def get_depot_index(self):
        return self.depot_index

    def get_num_locations(self):
        return len(self.locations)

    def get_service_times(self):
        service_times = {}
        for location in self.locations:
            service_times[location.name] = location.service_time
        return service_times
