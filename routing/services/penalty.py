# import for annotation to work on the IDE but avoid cyclic imports error
# https://stackoverflow.com/a/39757388
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from routing.entities.location import Location
    from routing.services.locations import LocationsService

import math


def calc_max_route(locations_service: LocationsService, **kwargs):
    max_route = 0
    visited_nodes = []
    to_visit_nodes = len(locations_service.locations)

    depot_index = locations_service.get_depot_index()
    depot_name = locations_service.get_name_from_index(depot_index)
    current_node = depot_name

    while to_visit_nodes > 0:
        visited_nodes.append(current_node)
        exit_routes = locations_service.distance_map[current_node]
        next_node = max(
            exit_routes, key=lambda next: exit_routes[next]
            if not next == depot_name and next not in visited_nodes else -1)
        max_route += exit_routes[next_node]
        current_node = next_node
        to_visit_nodes -= 1

    exit_routes = locations_service.distance_map[current_node]
    max_route += exit_routes[depot_name]

    return max_route


def calc_demand_multiplier(locations_service: LocationsService, location, **kwargs):
    max_route = calc_max_route(locations_service)
    magnitude = round(math.log(max_route, 10))
    penalty_param = 10**magnitude
    return penalty_param * location.demand


def calc_max_distance(locations_service: LocationsService, **kwargs):
    max_distance = 0
    for destinies in locations_service.distance_map.values():
        for name, distance in destinies.items():
            service_time = locations_service.get_location_from_name(name).service_time
            distance = distance + service_time
            if distance > max_distance:
                max_distance = distance
    return 2 * max_distance


def calc_depot_distance(locations_service: LocationsService, location: Location, **kwargs):
    depot = locations_service.get_depot()
    return 2 * location.distance_to(depot.name) + location.service_time + depot.service_time + 60 * 24
