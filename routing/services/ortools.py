import functools
from typing import List, Dict
from ortools.constraint_solver import pywrapcp
from routing.services.locations import LocationsService
from routing.entities.vehicle import Vehicle
from routing.services.vehicles import (
    VehiclesService,
    Break,
    BreakType)
from routing.entities.routing_solution import (
    RouteStep,
    RoutingSolution,
    RoutingSolutionStatus,
    VehicleBreakSolution,
    VehicleRoutingSolution)


class ORToolsService:
    def __init__(self,
                 vehicles_service: VehiclesService,
                 locations_service: LocationsService):
        self.vehicles_service = vehicles_service
        self.locations_service = locations_service
        self.index_manager = None
        self.routing_model = None

        self.get_index_manager()
        self.get_routing_model()

    def get_index_manager(self):
        if self.index_manager is None:
            self.index_manager = pywrapcp.RoutingIndexManager(
                self.locations_service.get_num_locations(),
                self.vehicles_service.get_num_vehicles(),
                self.locations_service.get_depot_index())
        return self.index_manager

    def get_routing_model(self):
        if self.routing_model is None:
            self.routing_model = pywrapcp.RoutingModel(self.index_manager)
        return self.routing_model

    def get_starting_node_index(self, vehicle_index):
        return self.routing_model.Start(vehicle_index)

    def set_allowed_vehicles_to_nodes(self):
        for location_node, location in enumerate(self.locations_service.locations):
            location_index = self.index_manager.NodeToIndex(location_node)
            allowed_vehicles = self.vehicles_service.get_allowed_vehicles_to_location(location)
            self.routing_model.SetAllowedVehiclesForIndex(allowed_vehicles, location_index)

    def set_vehicle_distance_transit_callback(self, vehicle_index, vehicle: Vehicle, distance_callback):
        vehicle_types = vehicle.types
        distance_with_type = functools.partial(distance_callback, vehicle_types)
        transit_callback_index = self.routing_model.RegisterTransitCallback(distance_with_type)
        self.routing_model.SetArcCostEvaluatorOfVehicle(transit_callback_index, vehicle_index)
        return transit_callback_index

    def setup_vehicle_distance_transit_cost(self, distance_callback):
        transit_callback_indices = []
        for vehicle_index, vehicle in enumerate(self.vehicles_service.vehicles):
            transit_callback_index = self.set_vehicle_distance_transit_callback(
                vehicle_index, vehicle, distance_callback)
            transit_callback_indices.append(transit_callback_index)
        return transit_callback_indices

    def setup_transit_dimension(self, slack, vehicle_max_distance, cumul_to_zero, dimension_name, callback_indices):
        self.routing_model.AddDimensionWithVehicleTransits(
            callback_indices,
            slack,  # slack
            vehicle_max_distance,  # vehicle maximum distance
            cumul_to_zero,  # start cumul to zero
            dimension_name)
        dimension = self.routing_model.GetDimensionOrDie(dimension_name)
        return dimension

    def setup_forbidden_time_window_constraints(self, dimension_name):
        """Set time windows when the nodes must not be visited.
           The only way to consider multiple delivering time windows for a location
           in OR Tools is excluding forbidden time windows from possible solutions."""
        dimension = self.routing_model.GetDimensionOrDie(dimension_name)
        for location_node, location in enumerate(self.locations_service.locations):
            if location.is_depot:
                continue
            location_index = self.index_manager.NodeToIndex(location_node)
            forbidden_time_window = self.locations_service.get_location_forbidden_time_window(location)
            self.routing_model.solver().AddConstraint(self.routing_model.solver().NotMemberCt(dimension.CumulVar(
                location_index), forbidden_time_window['start'], forbidden_time_window['end']))

    def setup_depot_time_var_to_minimize(self, dimension_name):
        depot_index = self.locations_service.get_depot_index()
        depot_location = self.locations_service.get_location_from_index(depot_index)
        dimension = self.routing_model.GetDimensionOrDie(dimension_name)
        for vehicle_index in range(self.vehicles_service.get_num_vehicles()):
            vehicle_start_node = self.routing_model.Start(vehicle_index)
            vehicle_end_node = self.routing_model.End(vehicle_index)
            depot_start_time_window = depot_location.get_time_windows_start()
            depot_end_time_window = depot_location.get_time_windows_end()
            dimension.CumulVar(vehicle_start_node).SetRange(
                depot_start_time_window[0],
                depot_end_time_window[0])
            dimension.CumulVar(vehicle_end_node).SetRange(
                depot_start_time_window[0],
                depot_end_time_window[0])
            self.routing_model.AddVariableMinimizedByFinalizer(
                dimension.CumulVar(vehicle_start_node))
            self.routing_model.AddVariableMinimizedByFinalizer(
                dimension.CumulVar(vehicle_end_node))

    def setup_max_load_weight_constraints(self, callback):
        vehicle_max_load_weights = self.vehicles_service.get_vehicles_max_load_weights()
        max_load_weight = max(vehicle_max_load_weights)
        demand_callback_index = self.routing_model.RegisterUnaryTransitCallback(callback)
        dimension_name = 'load_weight'
        self.routing_model.AddDimensionWithVehicleCapacity(
            demand_callback_index, max_load_weight, vehicle_max_load_weights, True, dimension_name)

    def setup_dropping_penalties(self):
        for location_node, location in enumerate(self.locations_service.locations):
            if not self.locations_service.has_penalty(location):
                continue
            location_index = self.index_manager.NodeToIndex(location_node)
            penalty = self.locations_service.get_drop_penalty(location)
            self.routing_model.AddDisjunction([location_index], penalty)

    def set_max_vehicle_journey(self, distance_dimension_name):
        """
            Sets journey of vehicle inside routing model.
            We assume lunch break or any other break is a time considered to the journey.
            OR Tools works with the max time used, including breaks.
        """
        distance_dimension = self.routing_model.GetDimensionOrDie(distance_dimension_name)
        for vehicle_index, vehicle in enumerate(self.vehicles_service.vehicles):
            vehicle_journey = vehicle.journey
            distance_dimension.SetSpanUpperBoundForVehicle(vehicle_journey, vehicle_index)

    def set_vehicle_breaks(self, distance_dimension_name):
        distance_dimension = self.routing_model.GetDimensionOrDie(distance_dimension_name)
        service_times = self.get_service_times_from_model_variables()
        for vehicle_index, vehicle in enumerate(self.vehicles_service.vehicles):
            lunch_break = self.set_vehicle_lunch_break(vehicle_index, vehicle)
            short_breaks = self.set_vehicle_short_breaks(vehicle_index, vehicle)
            vehicle_breaks = lunch_break + short_breaks
            if not vehicle_breaks:
                continue
            distance_dimension.SetBreakIntervalsOfVehicle(vehicle_breaks, vehicle_index, service_times.values())

    def set_vehicle_lunch_break(self, vehicle_index, vehicle) -> List:
        if vehicle.lunch_time_window is None:
            return []
        lunch_break = self.vehicles_service.add_new_break_to_vehicle(vehicle_index,
                                                                     BreakType.LUNCH,
                                                                     vehicle.lunch_time_window.minimum_start,
                                                                     vehicle.lunch_time_window.maximum_start,
                                                                     vehicle.lunch_time_window.duration)
        lunch_interval = self.break_interval(lunch_break, optional=False)
        return [lunch_interval]

    def set_vehicle_short_breaks(self, vehicle_index, vehicle: Vehicle) -> List:
        """Allows vehicle to take breaks inside its journey.
           OR Tools expects deterministic time windows when break must occur.
           We calculate the number of times vehicle must take a break based on frequency.
           Break times are estimated based on the number of breaks and frequency.
           1h time window when break may occur is used to increase probability of break happenning on expected time.

        Returns:
            List[OR Tools FixedDurationIntervalVar]
        """
        if vehicle.short_break is None:
            return []
        depot_node = self.locations_service.get_depot()
        depot_start_time = min(depot_node.get_time_windows_start())
        depot_end_time = max(depot_node.get_time_windows_end())
        max_journey_possible = depot_end_time - depot_start_time
        num_breaks = max_journey_possible // vehicle.short_break.frequency
        short_intervals = []
        for break_index in range(num_breaks):
            break_time = depot_start_time + (break_index + 1) * vehicle.short_break.frequency
            short_break = self.vehicles_service.add_new_break_to_vehicle(vehicle_index,
                                                                         BreakType.SHORT,
                                                                         break_time - 30,
                                                                         break_time + 30,
                                                                         vehicle.short_break.duration)
            short_interval = self.break_interval(short_break, optional=False)
            short_intervals.append(short_interval)
        return short_intervals

    def get_service_times_from_model_variables(self):
        service_times = {}
        for index in range(self.routing_model.Size()):
            node = self.index_manager.IndexToNode(index)
            location = self.locations_service.get_location_from_index(node)
            service_times[index] = location.service_time
        return service_times

    def break_interval(self, break_: Break, optional: bool):
        return self.routing_model.solver().FixedDurationIntervalVar(
            break_.minimum_start,  # minimum start time
            break_.maximum_start,  # maximum start time
            break_.duration,  # duration of break
            optional,  # if optional break
            f'{break_._id}')

    def get_node_cumul_var_bounds(self, solution, dimension, index):
        return (solution.Min(dimension.CumulVar(index)),
                solution.Max(dimension.CumulVar(index)))

    def get_node_slack_var_bounds(self, solution, dimension, index):
        return (solution.Min(dimension.SlackVar(index)),
                solution.Max(dimension.SlackVar(index)))

    def get_node_accumulated_value(self, solution, dimension, index):
        return solution.Max(dimension.CumulVar(index))

    def calculate_arrival_departure_time(self, solution, dimension, index, next_index, vehicle_types):
        arrival_time = solution.Min(dimension.CumulVar(index))
        node = self.index_manager.IndexToNode(index)
        next_node = self.index_manager.IndexToNode(next_index)
        departure_time = solution.Min(dimension.CumulVar(
            next_index)) - self.locations_service.get_distance_by_index(vehicle_types, node, next_node)
        return (arrival_time, departure_time)

    def calculate_demand(self, solution, dimension, index):
        demand = self.get_node_accumulated_value(solution, dimension, index)
        return demand

    def set_route_steps_load(self, vehicle_route: List[RouteStep]):
        total_demand = vehicle_route[-1].demand
        current_load = 0
        for route_step in vehicle_route:
            accumulated_demand = route_step.demand
            route_step.arrival_load = current_load
            departure_load = total_demand - accumulated_demand
            route_step.departure_load = departure_load
            current_load = departure_load

    def route_indexes(self, solution, vehicle_index):
        current_index = self.get_starting_node_index(vehicle_index)
        while not self.routing_model.IsEnd(current_index):
            next_index = solution.Value(
                self.routing_model.NextVar(current_index))
            yield current_index, next_index
            current_index = next_index
        yield current_index, next_index

    def get_vehicle_route(self, solution, vehicle_index, time_dimension, max_load_weight_dimension):
        vehicle_route = []
        current_index = self.get_starting_node_index(vehicle_index)
        vehicle = self.vehicles_service.vehicles[vehicle_index]
        vehicle_types = vehicle.types

        for current_index, next_index in self.route_indexes(solution, vehicle_index):
            arrival_time, departure_time = self.calculate_arrival_departure_time(
                solution, time_dimension, current_index, next_index, vehicle_types)
            location_node = self.index_manager.IndexToNode(current_index)
            location = self.locations_service.get_location_from_index(location_node)
            # demand only gets added to the cumul var on the next hop
            demand = self.calculate_demand(solution, max_load_weight_dimension, next_index)
            route_step = RouteStep(location, arrival_time, departure_time, demand)
            vehicle_route.append(route_step)

        self.set_route_steps_load(vehicle_route)
        return vehicle_route

    def get_vehicle_route_start_time(self, time_dimension, solution, vehicle_index):
        start_index = self.routing_model.Start(vehicle_index)
        return solution.Min(time_dimension.CumulVar(start_index))

    def get_vehicle_route_end_time(self, time_dimension, solution, vehicle_index):
        end_index = self.routing_model.End(vehicle_index)
        return solution.Min(time_dimension.CumulVar(end_index))

    def break_was_performed(self, break_):
        return break_.PerformedValue()

    def is_break_from_vehicle(self, vehicle_index, break_):
        expected_vehicle_breaks = self.vehicles_service.get_vehicle_breaks_from_index(vehicle_index)
        expected_vehicle_beaks_ids = expected_vehicle_breaks.get_breaks_ids()
        break_name = break_.Var().Name()
        # TODO: expected_vehicle_beaks_ids could be a hash table (set) and this would be O(1)?
        for break_id in expected_vehicle_beaks_ids:
            if break_name == break_id:
                return True
        return False

    def get_vehicle_break_type(self, vehicle_index, break_name) -> BreakType:
        vehicle_breaks = self.vehicles_service.get_vehicle_breaks_from_index(vehicle_index)
        break_type = vehicle_breaks.get_type_from_id(break_name)
        return break_type

    def get_vehicle_breaks_solution(self, distance_dimension,
                                    solution, vehicle_index) -> Dict[str, VehicleBreakSolution]:
        vehicle_start_time = self.get_vehicle_route_start_time(distance_dimension, solution, vehicle_index)
        vehicle_end_time = self.get_vehicle_route_end_time(distance_dimension, solution, vehicle_index)
        intervals = solution.IntervalVarContainer()
        vehicle_breaks = {}

        for interval in range(intervals.Size()):
            break_ = intervals.Element(interval)
            break_name = break_.Var().Name()
            if not self.break_was_performed(break_) or not self.is_break_from_vehicle(vehicle_index, break_):
                continue
            break_type = self.get_vehicle_break_type(vehicle_index, break_name)
            break_start = int(break_.StartValue())
            if break_start < vehicle_start_time or break_start >= vehicle_end_time:
                continue
            break_duration = int(break_.DurationValue())
            vehicle_breaks[break_name] = VehicleBreakSolution(break_start, break_duration, break_type)
        return vehicle_breaks

    def get_vehicle_lunch_break_from_solution(self, distance_dimension, solution, vehicle_index):
        vehicle_breaks = self.get_vehicle_breaks_solution(distance_dimension, solution, vehicle_index)
        for vehicle_break in vehicle_breaks.items():
            if vehicle_break[1].type != BreakType.LUNCH:
                continue
            return vehicle_break

    def get_vehicle_short_breaks_from_solution(self, distance_dimension, solution, vehicle_index):
        vehicle_breaks = self.get_vehicle_breaks_solution(distance_dimension, solution, vehicle_index)
        lunch_break_name = None
        for vehicle_break in vehicle_breaks.items():
            if vehicle_break[1].type == BreakType.LUNCH:
                lunch_break_name = vehicle_break[0]
        if lunch_break_name is not None:
            del vehicle_breaks[lunch_break_name]
        return vehicle_breaks.values()

    def parse_solution(self, solution) -> RoutingSolution:
        routing_solution = RoutingSolution(self.locations_service)
        if not solution:
            routing_solution.set_status(RoutingSolutionStatus.FAILED,
                                        'Solution not found')
            return routing_solution
        distance_dimension = self.routing_model.GetDimensionOrDie('distance')
        load_weight_dimension = self.routing_model.GetDimensionOrDie('load_weight')
        routing_solution.set_status(RoutingSolutionStatus.SUCCESS, 'Solution found')
        routing_solution.objective_cost = solution.ObjectiveValue()
        for vehicle_index in range(self.vehicles_service.get_num_vehicles()):
            vehicle = self.vehicles_service.get_vehicle_from_index(vehicle_index)
            vehicle_routing_solution = VehicleRoutingSolution(vehicle)
            vehicle_route = self.get_vehicle_route(
                solution, vehicle_index, distance_dimension, load_weight_dimension)
            vehicle_routing_solution.vehicle_route = vehicle_route
            vehicle_short_breaks = self.get_vehicle_short_breaks_from_solution(
                distance_dimension, solution, vehicle_index)
            vehicle_lunch_break = self.get_vehicle_lunch_break_from_solution(
                distance_dimension, solution, vehicle_index)
            if vehicle_lunch_break is not None:
                vehicle_routing_solution.vehicle_lunch_break = vehicle_lunch_break[1]
            vehicle_routing_solution.vehicle_short_breaks = vehicle_short_breaks
            routing_solution.add_vehicle_routing_solution(vehicle_routing_solution)
        return routing_solution
