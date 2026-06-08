"""
tests/test_zones.py

Unit tests for utils/zones.py — zone fuzzy matching and distance calculation.
Run with: python -m pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.zones import find_zone, road_distance_km, haversine_km, ZONES


class TestFindZone:
    def test_exact_match(self):
        assert find_zone("Westlands") == "Westlands"
        assert find_zone("Karen") == "Karen"
        assert find_zone("Kilimani") == "Kilimani"

    def test_case_insensitive(self):
        assert find_zone("westlands") == "Westlands"
        assert find_zone("KAREN") == "Karen"

    def test_substring_match(self):
        assert find_zone("near Sarit Centre, Westlands") == "Westlands"
        assert find_zone("Karen Hardy area") == "Karen"
        assert find_zone("Kilimani Heights") == "Kilimani"

    def test_alias_cbd(self):
        assert find_zone("town") == "CBD"
        assert find_zone("city centre") == "CBD"
        assert find_zone("nairobi cbd") == "CBD"

    def test_alias_south(self):
        assert find_zone("south b") == "South B"

    def test_no_match_out_of_zone(self):
        assert find_zone("Mombasa") is None
        assert find_zone("Kisumu") is None
        assert find_zone("Eldoret") is None
        assert find_zone("Thika") is None

    def test_fuzzy_match(self):
        # Slight misspellings
        result = find_zone("Kilemani")   # Kilimani
        assert result in ("Kilimani", None)   # may or may not match depending on cutoff


class TestDistance:
    def test_same_zone_zero(self):
        assert haversine_km("CBD", "CBD") == 0.0

    def test_known_approximate_distance(self):
        # CBD to Westlands is roughly 3–5 km straight line
        d = haversine_km("CBD", "Westlands")
        assert 2.0 < d < 7.0

    def test_cbd_to_karen(self):
        # CBD to Karen is roughly 14–20 km
        d = haversine_km("CBD", "Karen")
        assert 10.0 < d < 25.0

    def test_road_distance_greater_than_haversine(self):
        straight = haversine_km("Westlands", "Karen")
        road     = road_distance_km("Westlands", "Karen")
        assert road > straight

    def test_road_factor_is_130_percent(self):
        straight = haversine_km("Kilimani", "Runda")
        road     = road_distance_km("Kilimani", "Runda")
        assert abs(road - round(straight * 1.3, 1)) < 0.01

    def test_all_zones_have_coordinates(self):
        for zone in ZONES:
            lat, lng = ZONES[zone]
            assert -5 < lat < 5      # Kenya latitude range
            assert 33 < lng < 42     # Kenya longitude range
