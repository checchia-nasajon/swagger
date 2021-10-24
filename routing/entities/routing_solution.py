
from enum import Enum, auto
from dataclasses import dataclass
from routing.entities.location import Location
from routing.entities.vehicle import Vehicle
from routing.services.locations import LocationsService
from typing import List


@dataclass
class RouteStep:
    location: Location
    arrival_time: int
    departure_time: int
    demand: float
    arrival_load: float = None
    departure_load: float = None

    def to_json(self):
        return {
            'location': self.location.name,
            'demand': self.demand,
            'arrival_time': self.arrival_time,
            'departure_time': self.departure_time,
        }


class RoutingSolutionStatus(Enum):
    SUCCESS = auto()
    FAILED = auto()
    VERIFICATION_FAILED = auto()


class VehicleBreakSolution:
    def __init__(self, break_start, break_duration, break_type) -> None:
        self.break_start = break_start
        self.break_duration = break_duration
        self.type = break_type

    def to_json(self):
        return {'break_type': self.type,
                'break_start': self.break_start,
                'break_duration': self.break_duration}


class VehicleRoutingSolution:
    def __init__(self, vehicle: Vehicle) -> None:
        self.vehicle = vehicle
        self.vehicle_route: List[RouteStep] = []
        self.vehicle_lunch_break: VehicleBreakSolution = None
        self.vehicle_short_breaks = {}

    def add_route_step(self, route_step: RouteStep):
        self.vehicle_route.append(route_step)

    def route_distance(self):
        return self.vehicle_route[-1].departure_time - self.vehicle_route[0].arrival_time

    def to_json(self):
        return {
            'vehicle': self.vehicle.name,
            'route_distance': self.route_distance(),
            'lunch_break': None if self.vehicle_lunch_break is None else self.vehicle_lunch_break.to_json(),
            'short_breaks': [short_break.to_json() for short_break in self.vehicle_short_breaks],
            'vehicle_route': [vehicle_step.to_json() for vehicle_step in self.vehicle_route]

        }


class RoutingSolution:
    def __init__(self, locations_service: LocationsService) -> None:
        self.objective_cost = None
        self.locations: List[Location] = locations_service.locations
        self.routes_plan: List[VehicleRoutingSolution] = []

    def set_status(self, status: RoutingSolutionStatus, message: str):
        self.status = status
        self.message = message
        return self

    def add_vehicle_routing_solution(self, vehicle_routing_solution: VehicleRoutingSolution):
        self.routes_plan.append(vehicle_routing_solution)
        return self

    def get_dropped_locations(self):
        visited_locations = set()
        available_locations = set(location.name for location in self.locations)
        for vehicle_routing_solution in self.routes_plan:
            for route_step in vehicle_routing_solution.vehicle_route:
                visited_locations.add(route_step.location.name)
        return list(available_locations.difference(visited_locations))

    def to_json(self):
        return {
            'status': self.status.name,
            'message': self.message,
            'objective_cost': self.objective_cost,
            'dropped_locations': self.get_dropped_locations(),
            'solution': [vehicle_routing_solution.to_json() for vehicle_routing_solution in self.routes_plan]
        }
