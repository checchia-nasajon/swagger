import json
from routing.entities.location import Location
from routing.entities.vehicle import Vehicle
from typing import List


class SystemEntities:
    def __init__(self, locations: List[Location], vehicles: List[Vehicle],
                 max_reload, penalty_type, search_time_limit):
        self.locations = locations
        self.vehicles = vehicles
        self.max_reload = max_reload
        self.penalty_type = penalty_type
        self.search_time_limit = search_time_limit

    def __repr__(self):
        ret = {
            'locations': [json.loads(repr(location)) for location in self.locations],
            'vehicles': [json.loads(repr(vehicle)) for vehicle in self.vehicles],
            'max_reload': self.max_reload,
            'penalty_type': self.penalty_type.__name__,
            'search_time_limit': self.search_time_limit
        }
        return json.dumps(ret)

    def __str__(self):  # pragma: no cover
        ret = ('Locations: {locations}\n'
               'Vehicles: {vehicles}')
        locations = []
        for location in self.locations:
            locations.append(str(location))
        locations = '\n\t' + '\n\t'.join(locations)
        vehicles = []
        for vehicle in self.vehicles:
            vehicles.append(str(vehicle))
        vehicles = '\n\t' + '\n\t'.join(vehicles)
        return ret.format(locations=locations, vehicles=vehicles)
