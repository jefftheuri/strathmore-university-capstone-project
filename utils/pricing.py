"""
utils/pricing.py

SureRide fare calculation engine.

Pricing structure:
  - Base fare:    KES 150
  - Per km rate:  KES 35
  - Minimum fare: KES 250
  - Surge (1.5×): Friday & Saturday nights, 22:00 – 03:00
"""
from datetime import datetime
from dataclasses import dataclass


BASE_FARE    = 150      # KES
PER_KM_RATE  = 35       # KES per km
MIN_FARE     = 250      # KES
SURGE_FACTOR = 1.5
BOOKING_FEE  = 50       # KES platform fee (transparent, always shown)


@dataclass
class FareBreakdown:
    distance_km:     float
    base_fare:       int        # KES 150
    distance_charge: int        # distance_km × 35
    booking_fee:     int        # KES 50
    subtotal:        int        # before surge
    surge_applied:   bool
    surge_factor:    float      # 1.0 or 1.5
    total_kes:       int        # final amount to pay
    currency:        str = "KES"

    def summary_lines(self) -> list[str]:
        lines = [
            f"📏 Distance:        {self.distance_km} km",
            f"🚦 Base fare:       KES {self.base_fare}",
            f"🛣️  Distance charge: KES {self.distance_charge}",
            f"🏷️  Booking fee:     KES {self.booking_fee}",
        ]
        if self.surge_applied:
            lines.append(f"⚡ Surge (×{self.surge_factor}):    applied (peak hours)")
        lines.append(f"─────────────────────────────")
        lines.append(f"💳 Total:           KES {self.total_kes}")
        return lines

    def receipt_text(self) -> str:
        return "\n".join(self.summary_lines())


def is_surge_active(dt: datetime | None = None) -> bool:
    """
    Return True if surge pricing is currently active.
    Surge applies Friday (weekday=4) and Saturday (weekday=5) nights
    between 22:00 and 03:00 (next day).
    """
    now = dt or datetime.now()
    hour = now.hour
    weekday = now.weekday()   # 0=Mon … 6=Sun

    is_late_night = hour >= 22 or hour < 3
    is_weekend_night = weekday in (4, 5)    # Fri or Sat night
    # Also include Sunday early morning (hour < 3, weekday=6)
    is_sunday_early = weekday == 6 and hour < 3

    return is_late_night and (is_weekend_night or is_sunday_early)


def calculate_fare(distance_km: float, dt: datetime | None = None) -> FareBreakdown:
    """
    Calculate the full fare for a trip of *distance_km* kilometres.

    Args:
        distance_km: Road distance in km (from road_distance_km()).
        dt:          Reference datetime (defaults to now). Used for surge check.

    Returns:
        A FareBreakdown dataclass with all components and the final total.
    """
    distance_charge = round(distance_km * PER_KM_RATE)
    subtotal = BASE_FARE + distance_charge + BOOKING_FEE
    # Apply minimum fare before surge
    subtotal = max(subtotal, MIN_FARE + BOOKING_FEE)

    surge = is_surge_active(dt)
    factor = SURGE_FACTOR if surge else 1.0
    # Surge applies to the base + distance component only, not the booking fee
    surge_base = round((BASE_FARE + distance_charge) * factor)
    total = max(surge_base + BOOKING_FEE, MIN_FARE + BOOKING_FEE)

    return FareBreakdown(
        distance_km=distance_km,
        base_fare=BASE_FARE,
        distance_charge=distance_charge,
        booking_fee=BOOKING_FEE,
        subtotal=subtotal,
        surge_applied=surge,
        surge_factor=factor,
        total_kes=total,
    )
