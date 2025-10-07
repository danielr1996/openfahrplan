from openfahrplan.lib.display import sort_route_names
import pytest

# from sorter import sort_list

@pytest.mark.parametrize(
    "inp,expected",
    [
        (["U3","RB 30","RB 2","RB 29","819 (VRN 980)","1","100","30"], ["1","30","100","819 (VRN 980)","RB 2","RB 29","RB 30","U3"]),
    ],
)
def test_sort_route_names(inp, expected):
    assert sort_route_names(inp)==expected
