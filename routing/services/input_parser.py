from math import ceil
from routing.entities.location import Location, TimeWindow
from routing.entities.vehicle import ShortBreak, Vehicle, LunchTimeWindow
from routing.entities.system_entities import SystemEntities
from routing.entities.exception import InvalidPenaltyTypeError
from routing.settings import PENALTY_FUNCS


class LocationParser:
    def __init__(self):
        pass

    def parse(self, input_json):
        time_windows = []
        for time_window in input_json['time_windows']:
            start_time_window = ceil(time_window['start'])
            end_time_window = ceil(time_window['end'])
            time_windows.append(TimeWindow(start_time_window, end_time_window))
        coordinates = input_json.get('coordinates', {'latitude': 0, 'longitude': 0})
        coordinates = (coordinates['latitude'], coordinates['longitude'])
        location = Location(name=input_json['name'],
                            is_depot=input_json.get('is_depot', False),
                            accessibility=input_json['accessibility'],
                            demand=ceil(input_json.get('demand', 0)),
                            service_time=ceil(input_json['service_time']),
                            time_windows=time_windows,
                            high_priority=input_json.get('high_priority', False),
                            coordinates=coordinates)
        for distance_location in input_json['distances']:
            distance_value = ceil(distance_location['distance'])
            location.add_distance_to_another_location(distance_location['name'], distance_value)
        return location


class VehicleParser:
    @ classmethod
    def parse(cls, input_json):
        input_lunch_time_window = input_json.get('lunch_time_window')
        lunch_time_window = None
        if input_lunch_time_window:
            lunch_minimum_start = ceil(input_lunch_time_window['minimum_start'])
            lunch_maximum_start = ceil(input_lunch_time_window['maximum_start'])
            lunch_duration = ceil(input_lunch_time_window['duration'])
            lunch_time_window = LunchTimeWindow(lunch_minimum_start, lunch_maximum_start, lunch_duration)

        input_short_break = input_json.get('short_break')
        short_break = None
        if input_short_break:
            short_break_frequency = input_short_break['frequency']
            short_break_duration = ceil(input_short_break['duration'])
            short_break = ShortBreak(short_break_frequency, short_break_duration)

        journey = ceil(input_json['journey'])
        max_load_weight = ceil(input_json['max_load_weight'])

        return Vehicle(
            name=input_json['name'],
            types=input_json['types'],
            max_load_weight=max_load_weight,
            journey=journey,
            lunch_time_window=lunch_time_window,
            short_break=short_break)


class InputParser:
    default_penalty = 'distancia deposito'

    def __init__(self, input_json):
        self.input = input_json

    def parse(self) -> SystemEntities:
        locations = list()
        vehicles = list()
        search_time_limit = ceil(self.input.get('search_time_limit', 3))
        for vehicle in self.input['vehicles']:
            vehicles.append(VehicleParser.parse(vehicle))
        for location in self.input['locations']:
            locations.append(LocationParser().parse(location))
        penalty_type_input = self.input.get('drop_penalty_type', None)
        penalty_type = self.get_penalty_type(penalty_type_input)
        max_reload = ceil(self.input.get('max_reload', 0))
        return SystemEntities(locations=locations,
                              vehicles=vehicles,
                              max_reload=max_reload,
                              penalty_type=penalty_type,
                              search_time_limit=search_time_limit)

    def get_penalty_type(self, penalty_type_input):
        if penalty_type_input is None:
            return PENALTY_FUNCS[self.default_penalty]
        penalty_type = PENALTY_FUNCS.get(penalty_type_input.lower(), None)
        if penalty_type is None:
            raise InvalidPenaltyTypeError(penalty_type_input)
        return penalty_type
