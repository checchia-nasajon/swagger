from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from routing.services.logging import log_exception
from routing.services.locations import LocationsService
from routing.services.vehicles import VehiclesService
from routing.services.ortools import ORToolsService
from routing.entities.routing_solution import RoutingSolution, RoutingSolutionStatus


class RoutingService:
    def __init__(self, locations_service: LocationsService,
                 vehicles_service: VehiclesService,
                 solver_service: ORToolsService,
                 search_time_limit: int):
        self.locations_service = locations_service
        self.vehicles_service = vehicles_service
        self.solver_service = solver_service
        self.search_time_limit = search_time_limit
        self.index_manager = solver_service.get_index_manager()
        self.routing_model = solver_service.get_routing_model()
        self.solution = None
        self.setup_model()

    def distance_callback(self, vehicle_type, from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        # ortools suppress the exception, we're at least logging it
        try:
            from_node = self.index_manager.IndexToNode(from_index)
            to_node = self.index_manager.IndexToNode(to_index)
            distance = self.locations_service.get_distance_by_index(vehicle_type, from_node, to_node)
            service_time = self.locations_service.get_service_time_by_index(from_node)
            return service_time + distance
        except Exception as e:
            log_exception('distance_callback', locals(), e)

    def demand_callback(self, location_index):
        location_node = self.index_manager.IndexToNode(location_index)
        demand = self.locations_service.get_demand_by_index(location_node)
        return demand

    def setup_model(self):
        vehicle_max_load_weights = self.vehicles_service.get_vehicles_max_load_weights()
        self.locations_service.set_refill_depots_demand(max(vehicle_max_load_weights))
        # self.solver_service.set_allowed_vehicles_to_nodes()
        transit_callback_indices = self.solver_service.setup_vehicle_distance_transit_cost(self.distance_callback)
        distance_slack = 90
        vehicle_max_distance = 10_000
        distance_dimension_name = 'distance'
        self.solver_service.setup_transit_dimension(callback_indices=transit_callback_indices,
                                                    slack=distance_slack,
                                                    vehicle_max_distance=vehicle_max_distance,
                                                    cumul_to_zero=False,
                                                    dimension_name=distance_dimension_name)
        self.solver_service.set_max_vehicle_journey(distance_dimension_name)
        self.solver_service.set_vehicle_breaks(distance_dimension_name)
        # dimension = self.routing_model.GetDimensionOrDie(distance_dimension_name)
        # dimension.SetGlobalSpanCostCoefficient(1000)
        self.solver_service.setup_forbidden_time_window_constraints(distance_dimension_name)
        self.solver_service.setup_depot_time_var_to_minimize(distance_dimension_name)
        self.solver_service.setup_max_load_weight_constraints(self.demand_callback)
        self.solver_service.setup_dropping_penalties()

    def get_search_parameters(self):
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_ARC)
        search_parameters.time_limit.seconds = self.search_time_limit
        # search_parameters.solution_limit = 1
        # search_parameters.log_search = True
        return search_parameters

    def solve_problem(self, search_parameters):
        solution = self.routing_model.SolveWithParameters(search_parameters)
        return solution

    def start(self):
        self.solution = self.solve_problem(self.get_search_parameters())

    def get_solution(self) -> RoutingSolution:
        solution = self.solver_service.parse_solution(self.solution)
        return solution

    def print_solution(self):
        solution = self.get_solution()
        if solution.status == RoutingSolutionStatus.FAILED:
            print(solution.message)
            return
        print(f"objective_cost: {solution.objective_cost}\n")
        for route_plan in solution.routes_plan:
            plan_output = f'Route for vehicle {route_plan.vehicle}:'
            plan_output += ''.join([
                (f"\n\t{route_step.location.name}: "
                 f"arrival at {route_step.arrival_time} "
                 f"with load {route_step.arrival_load} "
                 f"and departure at {route_step.departure_time} "
                 f"with load {route_step.departure_load}")
                for route_step in route_plan.vehicle_route
            ]) + '\n'
            plan_output += f'Distance of the route: {route_plan.route_distance()}\n'
            if route_plan.vehicle_lunch_break:
                lunch_break_start = route_plan.vehicle_lunch_break.break_start
                lunch_break_duration = route_plan.vehicle_lunch_break.break_duration
                plan_output += f'Lunch break: start at {lunch_break_start} and takes {lunch_break_duration}\n'
            if route_plan.vehicle_short_breaks:
                plan_output += ''.join([
                    (f"Short break: "
                     f"start at {short_break.break_start} "
                     f"and takes {short_break.break_duration}\n")
                    for short_break in route_plan.vehicle_short_breaks
                ])
            print(plan_output)
        dropped = solution.get_dropped_locations()
        print(f'Dropped locations: {dropped}')
