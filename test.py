import yaml
from routing.app import routing
from routing_plot import plot_route_to_figure

with open('./test/input_settings/real_example_coords.yaml') as file:
    yaml_data = yaml.safe_load(file)

solution = routing(yaml_data)
plot_route_to_figure(solution)
