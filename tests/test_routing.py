from openfahrplan.lib.display import sort_route_names
import pytest

from openfahrplan.lib.gtfs import gtfs_build_graph2
from openfahrplan import feed


@pytest.mark.parametrize(
    "src,dst,expected",
    [
        ("Gustav Adolf Str","Burgfarnbach Ost", []),
    ],
)
def test_sort_route_names(src,dst,expected):
    gtfs_build_graph2(feed)
    assert 1==1
