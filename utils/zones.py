"""
utils/zones.py

Defines the SureRide pilot zones (affluent Nairobi neighbourhoods),
provides fuzzy zone-name matching, and Haversine distance calculation.
"""
import math
import difflib
from typing import Optional

# ── Pilot zone definitions ────────────────────────────────────────────────────
# Each entry: "Zone Name" -> (latitude, longitude) centroid
ZONES: dict[str, tuple[float, float]] = {
    "CBD":          (-1.2864, 36.8172),
    "Westlands":    (-1.2676, 36.8072),
    "Parklands":    (-1.2620, 36.8250),
    "Gigiri":       (-1.2292, 36.8042),
    "Runda":        (-1.2145, 36.8213),
    "Muthaiga":     (-1.2560, 36.8378),
    "Ridgeways":    (-1.2180, 36.8422),
    "Rosslyn":      (-1.2270, 36.7980),
    "Spring Valley":(-1.2580, 36.7900),
    "Loresho":      (-1.2630, 36.7780),
    "Kilimani":     (-1.2924, 36.7835),
    "Kileleshwa":   (-1.2870, 36.7748),
    "Lavington":    (-1.2890, 36.7668),
    "Riverside":    (-1.2760, 36.7950),
    "Upperhill":    (-1.2990, 36.8146),
    "Karen":        (-1.3380, 36.7120),
    "Langata":      (-1.3285, 36.7400),
    "South B":      (-1.3105, 36.8310),
    "South C":      (-1.3200, 36.8260),
}

# Aliases — common alternate spellings / abbreviations mapped to canonical names
_ALIASES: dict[str, str] = {
    "central business district": "CBD",
    "nairobi cbd":  "CBD",
    "town":         "CBD",
    "city centre":  "CBD",
    "city center":  "CBD",
    "west lands":   "Westlands",
    "park lands":   "Parklands",
    "south b":      "South B",
    "south c":      "South C",
    "south b/c":    "South B",
    "upper hill":   "Upperhill",
    "spring vly":   "Spring Valley",
    "riverside drive": "Riverside",
}

ZONE_NAMES = list(ZONES.keys())


def find_zone(user_text: str, cutoff: float = 0.65) -> Optional[str]:
    """
    Fuzzy-match *user_text* to a valid SureRide pilot zone name.

    Steps:
      1. Check alias dictionary (exact, case-insensitive).
      2. Check if any zone name is a substring of user_text.
      3. Run difflib closest-match against all zone names.

    Args:
        user_text: Raw string from user (e.g. "near Sarit Centre, Westlands").
        cutoff:    Minimum similarity ratio for difflib match (0–1).

    Returns:
        Canonical zone name (e.g. "Westlands"), or None if no match found.
    """
    text_lower = user_text.lower().strip()

    # 1. Alias lookup
    if text_lower in _ALIASES:
        return _ALIASES[text_lower]

    # 2. Substring check (e.g. "Westlands, near Sarit" → "Westlands")
    for zone in ZONE_NAMES:
        if zone.lower() in text_lower:
            return zone

    # 3. Difflib fuzzy match against zone names
    matches = difflib.get_close_matches(
        text_lower,
        [z.lower() for z in ZONE_NAMES],
        n=1,
        cutoff=cutoff,
    )
    if matches:
        # Map back to canonical casing
        matched_lower = matches[0]
        for zone in ZONE_NAMES:
            if zone.lower() == matched_lower:
                return zone

    return None


def haversine_km(zone_a: str, zone_b: str) -> float:
    """
    Return the straight-line distance in km between two zone centroids
    using the Haversine formula.
    """
    lat1, lon1 = ZONES[zone_a]
    lat2, lon2 = ZONES[zone_b]

    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def road_distance_km(zone_a: str, zone_b: str) -> float:
    """
    Estimate road distance by applying a 1.3× tortuosity factor to the
    straight-line Haversine distance. Returns km rounded to 1 decimal.
    """
    straight = haversine_km(zone_a, zone_b)
    return round(straight * 1.3, 1)


def zone_list_text() -> str:
    """Return a formatted string listing all valid pilot zones."""
    return ", ".join(ZONE_NAMES)
