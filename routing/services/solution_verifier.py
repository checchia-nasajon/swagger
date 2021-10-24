from routing.entities.exception import InvalidSolutionError
from routing.services.exception import ExceptionBuilder
from routing.entities.system_entities import SystemEntities
from routing.entities.routing_solution import RoutingSolution, RouteStep, RoutingSolutionStatus, VehicleRoutingSolution
from routing.services.utils import has_accessibility
from typing import Iterator


class SolutionVerifier:
    def __init__(self, system_entities: SystemEntities, routing_solution: RoutingSolution) -> None:
        self.system_entities = system_entities
        self.routing_solution = routing_solution
        self.exception_builder = ExceptionBuilder(InvalidSolutionError, ' ')

    def route_steps(self) -> Iterator[RouteStep]:
        for vehicle_routing_solution in self.routing_solution.routes_plan:
            for route_step in vehicle_routing_solution.vehicle_route:
                yield route_step

    def is_inside_time_window(self, arrival_time, time_window):
        if arrival_time >= time_window.start and arrival_time <= time_window.end:
            return True
        return False

    def verify_time_window_constraint(self, route_step: RouteStep):
        location = route_step.location
        time_windows = location.time_windows
        arrival_time = route_step.arrival_time
        for time_window in time_windows:
            if self.is_inside_time_window(arrival_time, time_window):
                break
        else:
            self.exception_builder.add_message(f'Invalid timing at {location.name}.')

    def verify_unload_constraint(self, route_step: RouteStep):
        unload = route_step.arrival_load - route_step.departure_load
        if unload != route_step.location.demand and route_step.location.demand >= 0:
            self.exception_builder.add_message(f'Invalid unload at {route_step.location.name}.')

    def verify_priorities_constraint(self):
        high_priority_locations = [
            location.name for location in self.routing_solution.locations if location.high_priority]
        visited_locations = set()
        for route_step in self.route_steps():
            visited_locations.add(route_step.location.name)
        for location in high_priority_locations:
            if location not in visited_locations:
                self.exception_builder.add_message(f'Priority location {location} not delivered.')

    def verify_double_visit(self):
        visited_locations_set = set()
        visited_locations_list = list()
        for route_step in self.route_steps():
            if route_step.location.is_depot:
                continue
            visited_locations_set.add(route_step.location)
            visited_locations_list.append(route_step.location)
        if len(visited_locations_list) != len(visited_locations_set):
            self.exception_builder.add_message('Solution has double visit.')

    def verify_vehicle_load_constraint(self, vehicle_routing_solution: VehicleRoutingSolution):
        vehicle = vehicle_routing_solution.vehicle
        max_load = vehicle.max_load_weight
        departure_load = vehicle_routing_solution.vehicle_route[0].departure_load
        if departure_load > max_load:
            self.exception_builder.add_message(f'Vehicle {vehicle.name} departure load is above maximum.')

    def verify_accessibility_constraint(self, vehicle_routing_solution: VehicleRoutingSolution):
        vehicle = vehicle_routing_solution.vehicle
        for route_step in vehicle_routing_solution.vehicle_route:
            location = route_step.location
            if not has_accessibility(vehicle.types, location):
                self.exception_builder.add_message(f'Vehicle {vehicle.name} '
                                                   f'types {vehicle.types} has no accessibility '
                                                   f'to location {location.name}.')

    def verify_solution(self):
        self.verify_priorities_constraint()
        self.verify_double_visit()
        for vehicle_routing_solution in self.routing_solution.routes_plan:
            self.verify_vehicle_load_constraint(vehicle_routing_solution)
            self.verify_accessibility_constraint(vehicle_routing_solution)
        for route_step in self.route_steps():
            if route_step.location.is_depot:
                continue
            self.verify_time_window_constraint(route_step)
            self.verify_unload_constraint(route_step)
        if self.exception_builder.has_exception():
            self.routing_solution.status = RoutingSolutionStatus.VERIFICATION_FAILED
            self.routing_solution.message = self.exception_builder.get_exception_message()
