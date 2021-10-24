import json
from typing import List, Set, Tuple, Dict


class TimeWindow:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __repr__(self):
        ret = {'start': self.start, 'end': self.end}
        return json.dumps(ret)


class Location:
    def __init__(self,
                 name: str,
                 accessibility: Set or List,
                 time_windows: List[TimeWindow],
                 demand: int,
                 service_time: int,
                 is_depot: bool = False,
                 high_priority: bool = False,
                 coordinates: Tuple[int, int] = None,
                 is_clone: bool = False):
        self.name = name
        self.distance_map: Dict = {name: 0}
        self.is_depot = is_depot
        self.is_clone = is_clone
        self.accessibility: Set[str] = set(accessibility)
        self.time_windows = time_windows
        self.demand = demand
        self.service_time = service_time
        self.high_priority = high_priority
        self.coordinates = coordinates if coordinates is not None else (0, 0)

    def distance_to(self, location_name):
        return self.distance_map[location_name]

    def add_distance_to_another_location(self, location_name, distance):
        self.distance_map[location_name] = distance

    def get_time_windows_start(self):
        time_windows_start = [time_window.start for time_window in self.time_windows]
        return time_windows_start

    def get_time_windows_end(self):
        time_windows_end = [time_window.end for time_window in self.time_windows]
        return time_windows_end

    def shallow_copy(self):
        location_copy = Location(name=self.name,
                                 accessibility=self.accessibility,
                                 time_windows=self.time_windows,
                                 demand=self.demand,
                                 service_time=self.service_time,
                                 is_depot=self.is_depot,
                                 is_clone=True,
                                 high_priority=self.high_priority,
                                 coordinates=self.coordinates)
        location_copy.distance_map = self.distance_map
        return location_copy

    def __repr__(self):
        ret = {
            'name': self.name,
            'is_depot': self.is_depot,
            'demand': self.demand,
            'service_time': self.service_time,
            'time_windows': [json.loads(repr(time_window)) for time_window in self.time_windows],
            'distances': [{'name': name, 'distance': distance} for name, distance in self.distance_map.items()],
            'accessibility': list(self.accessibility)
        }
        return json.dumps(ret)

    def __str__(self):  # pragma: no cover
        is_depot = '(Depot)' if self.is_depot else ''
        time_window = ' '.join([f'{w.start}:{w.end}' for w in self.time_windows])
        return (f'{self.name}{is_depot} - {self.demand} - {self.service_time} - '
                f'{" ".join(self.accessibility)} - {time_window}')
