import pytest
from openfahrplan import feed
from openfahrplan.lib.gtfs import gtfs_find_station, gtfs_reachable_transfers, gtfs_find_siblings, \
    gtfs_find_matching_name_stops


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
    actual = gtfs_find_station(feed, search, limit=limit)
    print(actual)
    assert actual["stop_id"].tolist() == expected

@pytest.mark.parametrize(
    "inp,expected",
    [
        ("de:09574:7450:3:1",["de:09574:7450:2:2"]),
    ],
)
def test_gtfs_reachable_transfers(inp,expected):
    actual = gtfs_reachable_transfers(feed,inp)
    assert actual["stop_id"].tolist() == expected

@pytest.mark.parametrize(
    "inp,expected",
    [
        ("de:09574:7672:0:1",["de:09574:7672:0:2"]),
    ],
)
def test_gtfs_find_siblings(inp,expected):
    actual = gtfs_find_siblings(feed,inp)
    assert actual["stop_id"].tolist() == expected

@pytest.mark.parametrize(
    "inp,expected",
    [
        ("de:09574:7670:1:1",["de:09574:7670:2:2"]),
    ],
)
def test_gtfs_find_matching_name_stops(inp,expected):
    actual = gtfs_find_matching_name_stops(feed,inp)
    assert actual["stop_id"].tolist() == expected

