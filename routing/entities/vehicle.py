from typing import List, Set
import json


class LunchTimeWindow:
    def __init__(self, minimum_start, maximum_start, duration) -> None:
        self.minimum_start = minimum_start
        self.maximum_start = maximum_start
        self.duration = duration

    def __repr__(self):
        ret = {
            'minimum_start': self.minimum_start,
            'maximum_start': self.maximum_start,
            'duration': self.duration
        }
        return json.dumps(ret)


class ShortBreak:
    def __init__(self, frequency, duration):
        self.frequency = frequency
        self.duration = duration

    def __repr__(self):
        ret = {
            'frequency': self.frequency,
            'duration': self.duration
        }
        return json.dumps(ret)


class Vehicle:
    def __init__(self,
                 name: str,
                 max_load_weight: int,
                 types: List[str],
                 journey: int = 480,
                 lunch_time_window: LunchTimeWindow = None,
                 short_break: ShortBreak = None):
        self.name = name
        self.types: Set[str] = set(types)
        self.max_load_weight = max_load_weight
        self.journey = journey
        self.lunch_time_window = lunch_time_window
        self.short_break = short_break

    def __repr__(self):
        ret = {
            'name': self.name,
            'types': sorted(list(self.types)),
            'max_load_weight': self.max_load_weight,
            'journey': self.journey,
            'lunch_time_window': None if self.lunch_time_window is None else json.loads(repr(self.lunch_time_window)),
            'short_break': None if self.short_break is None else json.loads(repr(self.short_break))
        }
        return json.dumps(ret)

    def __str__(self):  # pragma: no cover
        ret = f'{self.name}: {self.types} ({self.max_load_weight})'
        return ret
