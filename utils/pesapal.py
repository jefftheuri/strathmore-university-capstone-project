"""
utils/pesapal.py

PesaPal v3 payment API integration for SureRide.

Supports:
  - Sandbox mode (default, uses cybqa.pesapal.com)
  - Live mode (pay.pesapal.com) — set PESAPAL_ENV=live in .env
  - Mock mode — if credentials are missing, returns a realistic demo response

API flow:
  1. get_auth_token()           → bearer token
  2. register_ipn()             → ipn_id (one-time setup)
  3. submit_order(...)          → {order_tracking_id, redirect_url}
  4. User pays on PesaPal page
  5. check_payment_status(id)   → "COMPLETED" | "PENDING" | "FAILED"
"""
import os
import uuid
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
_ENV       = os.getenv("PESAPAL_ENV", "sandbox").lower()
_KEY       = os.getenv("PESAPAL_CONSUMER_KEY", "")
_SECRET    = os.getenv("PESAPAL_CONSUMER_SECRET", "")
_IPN_URL   = os.getenv("PESAPAL_IPN_URL", "https://sureride.co.ke/ipn")  # placeholder

_BASE_URLS = {
    "sandbox": "https://cybqa.pesapal.com/pesapalv3",
    "live":    "https://pay.pesapal.com/v3",
}
BASE_URL = _BASE_URLS.get(_ENV, _BASE_URLS["sandbox"])

MOCK_MODE = not (_KEY and _SECRET)   # True when no credentials are set


# ── Helpers ───────────────────────────────────────────────────────────────────
def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }


# ── 1. Authentication ─────────────────────────────────────────────────────────
def get_auth_token() -> str:
    """
    Request an OAuth2 bearer token from PesaPal.
    Returns the token string, or raises RuntimeError on failure.
    """
    if MOCK_MODE:
        return "mock_token_demo"

    resp = requests.post(
        f"{BASE_URL}/api/Auth/RequestToken",
        json={"consumer_key": _KEY, "consumer_secret": _SECRET},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("token")
    if not token:
        raise RuntimeError(f"PesaPal auth failed: {data}")
    return token


# ── 2. IPN Registration (run once) ────────────────────────────────────────────
_ipn_id_cache: str | None = None

def get_ipn_id(token: str) -> str:
    """
    Register the SureRide IPN (callback) URL with PesaPal and return the ipn_id.
    Result is cached in-process.
    """
    global _ipn_id_cache
    if _ipn_id_cache:
        return _ipn_id_cache

    if MOCK_MODE:
        _ipn_id_cache = "mock_ipn_id"
        return _ipn_id_cache

    resp = requests.post(
        f"{BASE_URL}/api/URLSetup/RegisterIPN",
        headers=_headers(token),
        json={"url": _IPN_URL, "ipn_notification_type": "GET"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _ipn_id_cache = data.get("ipn_id", "")
    return _ipn_id_cache


# ── 3. Submit Order ───────────────────────────────────────────────────────────
def submit_order(
    amount: int,
    description: str,
    passenger_name: str,
    passenger_email: str = "passenger@sureride.co.ke",
    passenger_phone: str = "+254700000000",
) -> dict:
    """
    Submit a payment order to PesaPal.

    Args:
        amount:          Total fare in KES (integer).
        description:     Trip description shown on PesaPal page.
        passenger_name:  Full name of the passenger.
        passenger_email: Passenger email (default placeholder).
        passenger_phone: Passenger phone (default placeholder).

    Returns:
        dict with keys:
          - order_tracking_id: str
          - redirect_url:      str  (URL to open for payment)
          - mock:              bool (True if in mock mode)
    """
    reference = f"SR-{uuid.uuid4().hex[:8].upper()}"

    if MOCK_MODE:
        # Return a realistic sandbox-style mock response
        mock_id = f"MOCK-{uuid.uuid4().hex[:12].upper()}"
        return {
            "order_tracking_id": mock_id,
            "redirect_url": (
                f"https://cybqa.pesapal.com/pesapalv3/api/Transactions/SubmitOrderRequest"
                f"?demo=true&ref={reference}&amount={amount}"
            ),
            "reference": reference,
            "mock": True,
        }

    token = get_auth_token()
    ipn_id = get_ipn_id(token)

    payload = {
        "id":                    reference,
        "currency":              "KES",
        "amount":                amount,
        "description":           description,
        "callback_url":          _IPN_URL,
        "notification_id":       ipn_id,
        "billing_address": {
            "email_address":     passenger_email,
            "phone_number":      passenger_phone,
            "country_code":      "KE",
            "first_name":        passenger_name.split()[0],
            "last_name":         passenger_name.split()[-1] if len(passenger_name.split()) > 1 else "",
        },
    }

    resp = requests.post(
        f"{BASE_URL}/api/Transactions/SubmitOrderRequest",
        headers=_headers(token),
        json=payload,
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()

    return {
        "order_tracking_id": data.get("order_tracking_id", reference),
        "redirect_url":      data.get("redirect_url", ""),
        "reference":         reference,
        "mock":              False,
    }


# ── 4. Check Payment Status ───────────────────────────────────────────────────
def check_payment_status(order_tracking_id: str) -> dict:
    """
    Query PesaPal for the current payment status of an order.

    Returns:
        dict with keys:
          - status:        "COMPLETED" | "PENDING" | "FAILED" | "INVALID"
          - status_code:   str (PesaPal status code)
          - description:   str
          - mock:          bool
    """
    if MOCK_MODE or order_tracking_id.startswith("MOCK-"):
        # Simulate a completed payment after first check in demo mode
        return {
            "status":      "COMPLETED",
            "status_code": "200",
            "description": "Payment successful (demo mode)",
            "mock":        True,
            "paid_at":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    try:
        token = get_auth_token()
        resp = requests.get(
            f"{BASE_URL}/api/Transactions/GetTransactionStatus",
            headers=_headers(token),
            params={"orderTrackingId": order_tracking_id},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        raw_status = data.get("payment_status_description", "").upper()
        # Normalise PesaPal status strings
        if "COMPLET" in raw_status or raw_status == "200":
            status = "COMPLETED"
        elif "PENDING" in raw_status or raw_status == "1":
            status = "PENDING"
        elif "FAILED" in raw_status or "INVALID" in raw_status:
            status = "FAILED"
        else:
            status = "PENDING"

        return {
            "status":      status,
            "status_code": data.get("status_code", ""),
            "description": data.get("payment_status_description", ""),
            "mock":        False,
            "paid_at":     data.get("created_date", ""),
        }

    except Exception as e:
        return {
            "status":      "PENDING",
            "status_code": "error",
            "description": f"Could not reach PesaPal: {e}",
            "mock":        False,
        }
