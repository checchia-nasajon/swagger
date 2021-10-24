from routing.entities.location import Location, TimeWindow
from routing.entities.vehicle import Vehicle
from routing.entities.system_entities import SystemEntities
from routing.entities.routing_solution import RouteStep, RoutingSolution, RoutingSolutionStatus, VehicleRoutingSolution
from routing.services.locations import LocationsService
from routing.services.solution_verifier import SolutionVerifier

location_demand = 5
service_time = 10
travel_time = 5


def get_system_entities():
    locations_info = [
        ('test_loc_deposit', ['truck', 'car'], [
         TimeWindow(0 * 60, 24 * 60)], location_demand, service_time, True),
        ('test_loc_A', ['truck'], [TimeWindow(8 * 60, 20 * 60)],
         location_demand, service_time, False),
        ('test_loc_B', ['truck'], [TimeWindow(0 * 60, 24 * 60)],
         location_demand, service_time, False),
        ('test_loc_C', ['car'], [TimeWindow(0 * 60, 24 * 60)],
         location_demand, service_time, False)
    ]
    locations = []

    for location_info in locations_info:
        location = Location(*location_info)
        for destiny_info in locations_info:
            if destiny_info is not location_info:
                location.add_distance_to_another_location(destiny_info[0], travel_time)
        locations.append(location)
    vehicles = [
        Vehicle(name='truck', max_load_weight=10, types=['truck']),
        Vehicle(name='car', max_load_weight=10, types=['car'])
    ]
    system_entities = SystemEntities(locations=locations, vehicles=vehicles,
                                     max_reload=0, penalty_type='distancia deposito',
                                     search_time_limit=15)
    return system_entities


def get_solution():
    system_entities = get_system_entities()
    locations = system_entities.locations
    locations_service = LocationsService(locations)
    vehicles = system_entities.vehicles
    routing_solution = RoutingSolution(locations_service=locations_service)
    vehicle_routing_solution = VehicleRoutingSolution(vehicles[0])

    arrival_time = 8 * 60
    departure_time = arrival_time + service_time
    arrival_load = 2 * location_demand
    departure_load = arrival_load - location_demand
    route_step = RouteStep(location=locations[1],
                           arrival_time=arrival_time,
                           departure_time=departure_time,
                           demand=location_demand,
                           arrival_load=arrival_load,
                           departure_load=departure_load)
    vehicle_routing_solution.add_route_step(route_step)

    arrival_time = departure_time + travel_time
    departure_time = arrival_time + service_time
    arrival_load = departure_load
    departure_load = arrival_load - location_demand
    route_step = RouteStep(location=locations[2],
                           arrival_time=arrival_time,
                           departure_time=arrival_time + service_time,
                           demand=location_demand,
                           arrival_load=arrival_load,
                           departure_load=arrival_load - location_demand)
    vehicle_routing_solution.add_route_step(route_step)
    routing_solution.add_vehicle_routing_solution(vehicle_routing_solution)

    vehicle_routing_solution = VehicleRoutingSolution(vehicles[1])

    arrival_time = 0 * 60
    departure_time = arrival_time + service_time
    arrival_load = 2 * location_demand
    departure_load = arrival_load - location_demand
    route_step = RouteStep(location=locations[0],
                           arrival_time=arrival_time,
                           departure_time=departure_time,
                           demand=location_demand,
                           arrival_load=arrival_load,
                           departure_load=departure_load)
    vehicle_routing_solution.add_route_step(route_step)

    arrival_time = departure_time + travel_time
    departure_time = arrival_time + service_time
    arrival_load = departure_load
    departure_load = arrival_load - location_demand
    route_step = RouteStep(location=locations[3],
                           arrival_time=arrival_time,
                           departure_time=arrival_time + service_time,
                           demand=location_demand,
                           arrival_load=arrival_load,
                           departure_load=arrival_load - location_demand)
    vehicle_routing_solution.add_route_step(route_step)
    routing_solution.add_vehicle_routing_solution(vehicle_routing_solution)
    routing_solution.status = RoutingSolutionStatus.SUCCESS
    return routing_solution


def test_verify_solution():
    system_entities = get_system_entities()
    routing_solution = get_solution()
    solution_verifier = SolutionVerifier(system_entities, routing_solution)
    solution_verifier.verify_solution()
    assert routing_solution.status == RoutingSolutionStatus.SUCCESS


def test_verify_time_window_constraint():
    system_entities = get_system_entities()
    routing_solution = get_solution()
    route_step = routing_solution.routes_plan[1].vehicle_route[1]
    route_step.arrival_time = -10
    solution_verifier = SolutionVerifier(system_entities, routing_solution)
    solution_verifier.verify_solution()
    assert routing_solution.status == RoutingSolutionStatus.VERIFICATION_FAILED
    assert routing_solution.message == f'Invalid timing at {route_step.location.name}.'


def test_verify_unload_constraint():
    system_entities = get_system_entities()
    routing_solution = get_solution()
    route_step = routing_solution.routes_plan[1].vehicle_route[1]
    route_step.departure_load = -10
    solution_verifier = SolutionVerifier(system_entities, routing_solution)
    solution_verifier.verify_solution()
    assert routing_solution.status == RoutingSolutionStatus.VERIFICATION_FAILED
    assert routing_solution.message == f'Invalid unload at {route_step.location.name}.'


def test_vehicle_load_constraint():
    system_entities = get_system_entities()
    routing_solution = get_solution()
    route_plan = routing_solution.routes_plan[1]
    route_step = route_plan.vehicle_route[0]
    route_step.departure_load = 999999
    solution_verifier = SolutionVerifier(system_entities, routing_solution)
    solution_verifier.verify_solution()
    assert routing_solution.status == RoutingSolutionStatus.VERIFICATION_FAILED
    assert routing_solution.message == f'Vehicle {route_plan.vehicle.name} departure load is above maximum.'


def test_double_visit():
    system_entities = get_system_entities()
    routing_solution = get_solution()
    route_plan = routing_solution.routes_plan[1]
    route_step = route_plan.vehicle_route[1]
    route_plan.add_route_step(route_step)
    solution_verifier = SolutionVerifier(system_entities, routing_solution)
    solution_verifier.verify_solution()
    assert routing_solution.status == RoutingSolutionStatus.VERIFICATION_FAILED
    assert routing_solution.message == 'Solution has double visit.'


def test_accessibility_constraint():
    system_entities = get_system_entities()
    routing_solution = get_solution()
    route_plan = routing_solution.routes_plan[1]
    location = route_plan.vehicle_route[1].location
    vehicle = route_plan.vehicle
    location.accessibility = set()
    solution_verifier = SolutionVerifier(system_entities, routing_solution)
    solution_verifier.verify_solution()
    assert routing_solution.status == RoutingSolutionStatus.VERIFICATION_FAILED
    assert routing_solution.message == (f'Vehicle {vehicle.name} '
                                        f'types {vehicle.types} has no accessibility '
                                        f'to location {location.name}.')
