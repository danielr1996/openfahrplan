import pytest
from openfahrplan import feed


@pytest.mark.parametrize(
    "search,limit,expected",
    [
        ("Reichenschwand Rathaus",2,["de:09574:7670:1:1","de:09574:7672:0:1"]),
        ("Nürnberg Hbf",1,["de:09564:510:1:1"]),
        ("Burgfarrnbach Ost",1,["de:09563:2611:0:1"]),
        ("Deichslerstraße",1,["de:09564:335:13:1"]),
        ("Lorenzkirche",1,["de:09564:511:11:1"]),
    ],
)
def test_gtfs_find_station(search,limit,expected):
    actual = feed.gtfs_find_station(search, limit=limit)
    assert actual["stop_id"].tolist() == expected

@pytest.mark.parametrize(
    "inp,expected",
    [
        ("de:09574:7450:3:1",["de:09574:7450:2:2"]),
    ],
)
def test_gtfs_reachable_transfers(inp,expected):
    actual = feed.gtfs_reachable_transfers(inp)
    assert actual["stop_id"].tolist() == expected

@pytest.mark.parametrize(
    "inp,expected",
    [
        ("de:09574:7672:0:1",["de:09574:7672:0:2"]),
    ],
)
def test_gtfs_find_siblings(inp,expected):
    actual = feed.gtfs_find_siblings(inp)
    assert actual["stop_id"].tolist() == expected

@pytest.mark.parametrize(
    "inp,expected",
    [
        ("de:09574:7670:1:1",["de:09574:7670:2:2"]),
    ],
)
def test_gtfs_find_matching_name_stops(inp,expected):
    actual = feed.gtfs_find_matching_name_stops(inp)
    assert actual["stop_id"].tolist() == expected
