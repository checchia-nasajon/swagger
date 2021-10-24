import functools
import numpy
from matplotlib import pyplot
from matplotlib import patches


def discrete_cmap(N, base_cmap=None):
    base = pyplot.cm.get_cmap(base_cmap)
    color_list = base(numpy.linspace(0, 1, N))
    cmap_name = base.name + str(N)
    return base.from_list(cmap_name, color_list, N)


def get_depot_from_locations(locations):
    for index, location in enumerate(locations):
        if location.is_depot:
            depot = location
            return depot


def plot_depot(ax1, locations):
    depot = get_depot_from_locations(locations)
    ax1.annotate(
        '{depot}'.format(depot=depot.name),
        xy=(depot.coordinates[1], depot.coordinates[0]),
        xytext=(depot.coordinates[1]+50, depot.coordinates[0]+50),
        xycoords='data',
        textcoords='offset points',
        arrowprops=dict(
            arrowstyle='->',
            connectionstyle='angle3,angleA=90,angleB=0',
            shrinkA=0.05),
    )


def plot_vehicle_routes(routes_plan, ax1):
    num_vehicles = len(routes_plan)
    cmap = discrete_cmap(num_vehicles + 2, 'nipy_spectral')
    legend_handles = []
    locations_plots = []
    for vehicle_index in range(num_vehicles):
        vehicle_solution = routes_plan[vehicle_index]
        vehicle_route = vehicle_solution.vehicle_route
        coordinates = zip(*[(route_step.location.coordinates[0], route_step.location.coordinates[1])
                            for route_step in vehicle_route])
        latitudes, longitudes = coordinates
        latitudes = numpy.array(latitudes)
        longitudes = numpy.array(longitudes)

        for route_step in vehicle_route:
            location = route_step.location
            location_plot, = ax1.plot(
                location.coordinates[1],
                location.coordinates[0],
                'o', mfc=cmap(vehicle_index + 1),
                label=location.name, markeredgecolor='#0E3A70')
            locations_plots.append(location_plot)
        ax1.quiver(
            longitudes[:-1],
            latitudes[:-1],
            longitudes[1:] - longitudes[:-1],
            latitudes[1:] - latitudes[:-1],
            scale_units='xy',
            angles='xy',
            scale=1,
            color=cmap(vehicle_index + 1),
            width=0.005)
        legend_handles.append(
            patches.Patch(
                color=cmap(vehicle_index + 1),
                label=vehicle_solution.vehicle))
    ax1.legend(handles=legend_handles)
    return locations_plots


def update_annotation(annotation, location_plot, index):
    posx, posy = [location_plot.get_xdata()[index], location_plot.get_ydata()[index]]
    annotation.xy = (posx, posy)
    text = f'{location_plot.get_label()}'
    annotation.set_text(text)
    annotation.get_bbox_patch().set_alpha(0.4)


def hover(ax1, annotation, fig, locations_plots, event):
    visibility = annotation.get_visible()
    if event.inaxes == ax1:
        for location_plot in locations_plots:
            cont, ind = location_plot.contains(event)
            if cont:
                update_annotation(annotation, location_plot, ind['ind'][0])
                annotation.set_visible(True)
                fig.canvas.draw_idle()
            else:
                if visibility:
                    annotation.set_visible(False)
                    fig.canvas.draw_idle()


def plot_route_to_figure(solution):
    fig = pyplot.figure()
    ax = fig.add_subplot(111)
    # Plot all the nodes as black dots.
    location_longitudes, location_latitudes = zip(
        *[(location.coordinates[1], location.coordinates[0]) for location in solution.locations])
    ax.plot(location_longitudes, location_latitudes, 'k.')

    annotation = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                             bbox=dict(boxstyle="round", fc="w"),
                             arrowprops=dict(arrowstyle="->"))
    annotation.set_visible(False)

    plot_depot(ax, solution.locations)
    # plot the routes as arrows
    locations_plots = plot_vehicle_routes(solution.routes_plan, ax)
    pyplot.draw()
    pyplot.savefig('./gitignore_route_plot.png', format='png')
    fig.canvas.mpl_connect("motion_notify_event", functools.partial(hover, ax, annotation, fig, locations_plots))
    pyplot.show()
