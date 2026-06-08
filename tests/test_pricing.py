"""
tests/test_pricing.py

Unit tests for utils/pricing.py — fare calculation and surge logic.
Run with: python -m pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from utils.pricing import calculate_fare, is_surge_active, BASE_FARE, PER_KM_RATE, BOOKING_FEE, MIN_FARE


class TestSurge:
    def _dt(self, weekday, hour):
        """Create a datetime with given weekday (0=Mon) and hour."""
        # Find a concrete date with the required weekday
        from datetime import timedelta
        base = datetime(2026, 6, 1)   # A Monday
        delta = (weekday - base.weekday()) % 7
        d = base + timedelta(days=delta)
        return d.replace(hour=hour, minute=0, second=0)

    def test_friday_night_surge(self):
        assert is_surge_active(self._dt(4, 23)) is True   # Friday 23:00

    def test_saturday_night_surge(self):
        assert is_surge_active(self._dt(5, 22)) is True   # Saturday 22:00

    def test_saturday_early_morning_surge(self):
        assert is_surge_active(self._dt(5, 1)) is True    # Saturday 01:00

    def test_sunday_early_surge(self):
        assert is_surge_active(self._dt(6, 2)) is True    # Sunday 02:00

    def test_monday_no_surge(self):
        assert is_surge_active(self._dt(0, 23)) is False  # Monday night

    def test_friday_afternoon_no_surge(self):
        assert is_surge_active(self._dt(4, 15)) is False  # Friday 15:00

    def test_wednesday_midnight_no_surge(self):
        assert is_surge_active(self._dt(2, 0)) is False   # Wednesday midnight


class TestFare:
    def test_minimum_fare_applied(self):
        """Very short trip should hit the minimum fare floor."""
        fare = calculate_fare(0.5)
        assert fare.total_kes >= MIN_FARE + BOOKING_FEE

    def test_formula_normal(self):
        """10 km trip at normal hours."""
        dt = datetime(2026, 6, 1, 14, 0)   # Monday 14:00
        fare = calculate_fare(10.0, dt)
        expected_base = BASE_FARE + int(10 * PER_KM_RATE) + BOOKING_FEE
        assert fare.total_kes == expected_base
        assert fare.surge_applied is False

    def test_formula_surge(self):
        """10 km trip during surge hours — should cost more."""
        dt_normal = datetime(2026, 6, 1, 14, 0)   # Monday 14:00
        dt_surge  = datetime(2026, 6, 5, 23, 0)   # Friday 23:00
        fare_normal = calculate_fare(10.0, dt_normal)
        fare_surge  = calculate_fare(10.0, dt_surge)
        assert fare_surge.total_kes > fare_normal.total_kes
        assert fare_surge.surge_applied is True

    def test_booking_fee_included(self):
        dt   = datetime(2026, 6, 1, 10, 0)
        fare = calculate_fare(5.0, dt)
        assert fare.booking_fee == BOOKING_FEE

    def test_westlands_to_karen_range(self):
        """Westlands→Karen ≈ 10–14 km road → expect KES 500–700."""
        dt   = datetime(2026, 6, 1, 10, 0)
        fare = calculate_fare(12.0, dt)
        assert 400 < fare.total_kes < 800

    def test_fare_breakdown_fields(self):
        dt   = datetime(2026, 6, 1, 10, 0)
        fare = calculate_fare(8.0, dt)
        assert fare.distance_km   == 8.0
        assert fare.base_fare     == BASE_FARE
        assert fare.distance_charge == int(8 * PER_KM_RATE)
        assert fare.booking_fee   == BOOKING_FEE
        assert fare.currency      == "KES"
