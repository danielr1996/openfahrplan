import numpy as np

from openfahrplan.lib.display import sort_route_names, zoom_from_bounds
import pytest
from openfahrplan import feed

@pytest.mark.parametrize(
    "inp,expected",
    [
        (["U3","RB 30","RB 2","RB 29","819 (VRN 980)","1","100","30"], ["1","30","100","819 (VRN 980)","RB 2","RB 29","RB 30","U3"]),
    ],
)
def test_sort_route_names(inp, expected):
    assert sort_route_names(inp)==expected

def test_zoom_from_bounds():
    zoom, center = zoom_from_bounds(feed.stops)
    assert np.isclose(zoom,7,atol=0.1)
    assert np.isclose(center["lat"],49.648876412452594)
    assert np.isclose(center["lon"],11.211199666403003)
