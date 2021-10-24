# import for annotation to work on the IDE but avoid cyclic imports error
# https://stackoverflow.com/a/39757388
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from routing.entities.location import Location


def has_accessibility(vehicle_type, location: Location):
    """
        Vehicle_type is a set with vehicles tipes,
        location accessibility is a set with accessibilities
        Vehicle is accessible to location if the intersect of the sets are not empty
    """
    return bool(vehicle_type.intersection(location.accessibility))
