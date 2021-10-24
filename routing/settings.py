from routing.services.penalty import (calc_max_distance,
                                      calc_depot_distance,
                                      calc_demand_multiplier)

APP_NAME = 'routing'

INFINITY = 100_000_000

PENALTY_FUNCS = {
    'distancia deposito': calc_depot_distance,
    'distancia maxima': calc_max_distance,
    'demanda': calc_demand_multiplier
}
