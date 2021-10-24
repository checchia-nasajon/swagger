import json
from routing.services.input_parser import InputParser


def test_input_parser_locations(routing_yaml):
    input_parser = InputParser(routing_yaml)
    internal_representation = input_parser.parse()
    locations = json.loads(repr(internal_representation.locations))
    for location in locations:
        # accessibility is a set in the internal representation, but we retrieve it as a list and order is not garanted
        location['accessibility'] = set(location['accessibility'])

    for location in routing_yaml['locations']:
        # accessibility is a set in the internal representation, but we retrieve it as a list and order is not garanted
        location['accessibility'] = set(location['accessibility'])
        # distance to self is zero
        name = location['name']
        self_loc = {'name': name, 'distance': 0}
        location['distances'].insert(0, self_loc)
        # depot defaults to false
        if location.get('is_depot') is None:
            location['is_depot'] = False
    assert locations == routing_yaml['locations']


def test_input_parser_locationsvehicles(routing_yaml):
    input_parser = InputParser(routing_yaml)
    internal_representation = input_parser.parse()
    vehicles = json.loads(repr(internal_representation.vehicles))
    assert vehicles == routing_yaml['vehicles']
