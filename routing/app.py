from routing.entities.exception import InvalidSolutionError
from routing.services.logging import logger
from routing.services.locations import LocationsService
from routing.services.vehicles import VehiclesService
from routing.services.routing import RoutingService
from routing.services.ortools import ORToolsService
from routing.services.input_parser import InputParser
from routing.services.solution_verifier import SolutionVerifier


def routing(input_json):
    input_parser = InputParser(input_json=input_json)
    system_entities = input_parser.parse()
    locations_service = LocationsService(system_entities.locations,
                                         system_entities.penalty_type,
                                         system_entities.max_reload)
    vehicles_service = VehiclesService(system_entities.vehicles)
    ortools_service = ORToolsService(vehicles_service, locations_service)
    routing_service = RoutingService(locations_service, vehicles_service,
                                     ortools_service,
                                     system_entities.search_time_limit)
    routing_service.start()
    # routing_service.print_solution()
    solution = routing_service.get_solution()
    solution_verifier = SolutionVerifier(system_entities, solution)
    # verify solution changes the solution status and message if needed.
    solution_verifier.verify_solution()
    return solution
