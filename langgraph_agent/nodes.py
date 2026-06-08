"""
langgraph_agent/nodes.py

Graph nodes for the SureRide booking agent.
Each node receives BookingState, does one job, and returns a partial update.

Booking flow:
  greet → collect_name → collect_pickup → validate_pickup
        → collect_destination → validate_destination
        → show_fare → confirm_fare → await_payment → done
  (+ rag_tool_node can intercept at collect_pickup / collect_destination)
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage

from langgraph_agent.state import BookingState
from utils.zones import find_zone, road_distance_km, zone_list_text, ZONE_NAMES
from utils.pricing import calculate_fare
from utils.pesapal import submit_order, check_payment_status

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)

# ── Formatting helpers ────────────────────────────────────────────────────────



# ═══════════════════════════════════════════════════════════════════════════════
# GREETING
# ═══════════════════════════════════════════════════════════════════════════════
def greet_node(state: BookingState) -> dict:
    reply = (
        "👋 Welcome to *SureRide* — your safe ride home, anytime! 🚗\n\n"
        "Our AI assistant will book your ride in under 60 seconds.\n\n"
        "First, may I have your name?"
    )
    return {"messages": [AIMessage(content=reply)], "current_step": "collect_name"}


# ═══════════════════════════════════════════════════════════════════════════════
# COLLECT NAME
# ═══════════════════════════════════════════════════════════════════════════════
def collect_name_node(state: BookingState) -> dict:
    last = state["messages"][-1].content.strip()
    name = last.split()[0].capitalize()
    reply = (
        f"Great to meet you, *{name}*! 😊\n\n"
        f"Where would you like to be *picked up* from?"
    )
    return {
        "messages": [AIMessage(content=reply)],
        "user_name": name,
        "current_step": "collect_pickup",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COLLECT PICKUP
# ═══════════════════════════════════════════════════════════════════════════════
def collect_pickup_node(state: BookingState) -> dict:
    raw = state["messages"][-1].content.strip()
    reply = (
        f"Got it — I'll check if *{raw}* is in our pilot zone...\n"
        "One moment ⏳"
    )
    return {
        "messages": [AIMessage(content=reply)],
        "pickup_raw": raw,
        "current_step": "validate_pickup",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATE PICKUP ZONE
# ═══════════════════════════════════════════════════════════════════════════════
def validate_pickup_node(state: BookingState) -> dict:
    raw = state.get("pickup_raw", "")
    zone = find_zone(raw)

    if zone:
        reply = (
            f"✅ *{zone}* — got it!\n\n"
            f"And where are you headed?"
        )
        return {
            "messages": [AIMessage(content=reply)],
            "pickup_zone": zone,
            "current_step": "collect_destination",
        }
    else:
        zones = ", ".join(sorted(ZONE_NAMES))
        reply = (
            f"Sorry, *{raw}* isn't in our pilot area yet.\n\n"
            f"We currently serve:\n{zones}\n\n"
            f"Please enter your pickup from one of these areas."
        )
        return {
            "messages": [AIMessage(content=reply)],
            "pickup_raw": None,
            "current_step": "collect_pickup",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# COLLECT DESTINATION
# ═══════════════════════════════════════════════════════════════════════════════
def collect_destination_node(state: BookingState) -> dict:
    raw = state["messages"][-1].content.strip()
    reply = (
        f"Checking *{raw}* in our pilot zones... ⏳"
    )
    return {
        "messages": [AIMessage(content=reply)],
        "destination_raw": raw,
        "current_step": "validate_destination",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATE DESTINATION ZONE
# ═══════════════════════════════════════════════════════════════════════════════
def validate_destination_node(state: BookingState) -> dict:
    raw = state.get("destination_raw", "")
    zone = find_zone(raw)
    pickup_zone = state.get("pickup_zone", "")

    if not zone:
        zones = ", ".join(sorted(ZONE_NAMES))
        reply = (
            f"Sorry, *{raw}* isn't in our pilot area yet.\n\n"
            f"We currently serve:\n{zones}\n\n"
            f"Please enter a destination from one of these areas."
        )
        return {
            "messages": [AIMessage(content=reply)],
            "destination_raw": None,
            "current_step": "collect_destination",
        }

    if zone == pickup_zone:
        reply = (
            f"⚠️ Your pickup and destination are both in *{zone}*.\n"
            "Please enter a different destination neighbourhood."
        )
        return {
            "messages": [AIMessage(content=reply)],
            "destination_raw": None,
            "current_step": "collect_destination",
        }

    return {
        "messages": [AIMessage(content=f"✅ *{zone}* confirmed. Calculating your fare...")],
        "destination_zone": zone,
        "current_step": "show_fare",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SHOW FARE
# ═══════════════════════════════════════════════════════════════════════════════
def show_fare_node(state: BookingState) -> dict:
    pickup    = state["pickup_zone"]
    dest      = state["destination_zone"]
    name      = state.get("user_name", "there")

    dist_km   = road_distance_km(pickup, dest)
    fare      = calculate_fare(dist_km)

    lines = [
        f"Here's your trip summary, *{name}*:\n",
        f"📍 *Pickup:*      {pickup}",
        f"🏁 *Destination:* {dest}",
        f"📏 *Distance:*    {dist_km} km (estimated)",
        f"",
        f"💰 *Fare Breakdown*",
        f"  Base fare:       KES {fare.base_fare}",
        f"  Distance ({dist_km} km × KES 35): KES {fare.distance_charge}",
        f"  Booking fee:     KES {fare.booking_fee}",
    ]
    if fare.surge_applied:
        lines.append(f"  ⚡ Surge (×{fare.surge_factor}): applied (peak hours)")
    lines += [
        f"  ──────────────────────",
        f"  *Total:  KES {fare.total_kes}*",
        f"",
        f"Reply *yes* to proceed to payment, or *no* to cancel.",
    ]

    reply = "\n".join(lines)
    return {
        "messages": [AIMessage(content=reply)],
        "distance_km": dist_km,
        "fare_kes": fare.total_kes,
        "surge_applied": fare.surge_applied,
        "current_step": "confirm_fare",
        "awaiting_confirmation": True,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIRM FARE (yes / no)
# ═══════════════════════════════════════════════════════════════════════════════
def confirm_fare_node(state: BookingState) -> dict:
    last = state["messages"][-1].content.strip().lower()

    if last not in ("yes", "y", "confirm", "sure", "ok", "yep", "proceed"):
        reply = (
            "🚫 Booking cancelled. No problem at all!\n\n"
            "Type *start* whenever you'd like to book again."
        )
        return {
            "messages": [AIMessage(content=reply)],
            "current_step": "done",
            "awaiting_confirmation": False,
        }

    name      = state.get("user_name", "Passenger")
    fare      = state.get("fare_kes", 0)
    pickup    = state.get("pickup_zone", "")
    dest      = state.get("destination_zone", "")
    dist      = state.get("distance_km", 0)

    description = f"SureRide: {pickup} → {dest} ({dist} km)"

    try:
        order = submit_order(
            amount=fare,
            description=description,
            passenger_name=name,
        )
        pay_url   = order["redirect_url"]
        order_id  = order["order_tracking_id"]
        mock_note = "\n_(Demo mode — no real payment required)_" if order.get("mock") else ""

        reply = (
            f"✅ Fare confirmed! Please complete payment to book your ride.\n\n"
            f"💳 *Amount:* KES {fare}\n"
            f"🔗 *Payment link:* [Pay via PesaPal]({pay_url})\n\n"
            f"Click the link above to pay securely via M-Pesa or card on PesaPal.\n"
            f"Once done, come back and tap the *Check Payment* button.{mock_note}"
        )
        return {
            "messages": [AIMessage(content=reply)],
            "pesapal_order_id": order_id,
            "pesapal_pay_url":  pay_url,
            "payment_status":   "pending",
            "booking_confirmed": False,
            "awaiting_confirmation": False,
            "current_step": "await_payment",
        }

    except Exception as e:
        reply = (
            "⚠️ Payment gateway temporarily unavailable.\n"
            "Please try again in a moment, or type *help* to speak to an agent."
        )
        return {
            "messages": [AIMessage(content=reply)],
            "current_step": "confirm_fare",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK PAYMENT STATUS
# ═══════════════════════════════════════════════════════════════════════════════
def check_payment_node(state: BookingState) -> dict:
    order_id = state.get("pesapal_order_id", "")
    result   = check_payment_status(order_id)
    status   = result["status"]

    if status == "COMPLETED":
        name   = state.get("user_name", "")
        pickup = state.get("pickup_zone", "")
        dest   = state.get("destination_zone", "")
        fare   = state.get("fare_kes", 0)
        reply  = (
            f"🎉 *Payment confirmed!* Thank you, {name}.\n\n"
            f"Your SureRide driver is on the way!\n"
            f"📍 Pickup: *{pickup}*\n"
            f"🏁 Destination: *{dest}*\n"
            f"💳 Paid: *KES {fare}* via PesaPal\n"
            f"⏱ Estimated arrival: *5–10 minutes*\n\n"
            f"Stay safe — SureRide has got you. 🙏"
        )
        return {
            "messages": [AIMessage(content=reply)],
            "payment_status":   "completed",
            "booking_confirmed": True,
            "current_step": "done",
        }

    elif status == "FAILED":
        reply = (
            "❌ Payment failed or was declined.\n\n"
            "Please try again by tapping *Retry Payment*, "
            "or type *help* to speak with an agent."
        )
        return {
            "messages": [AIMessage(content=reply)],
            "payment_status": "failed",
            "current_step":   "await_payment",
        }

    else:  # PENDING
        reply = (
            "⏳ Payment is still pending.\n\n"
            "Please complete the payment on the PesaPal page, "
            "then tap *Check Payment* again."
        )
        return {
            "messages": [AIMessage(content=reply)],
            "payment_status": "pending",
            "current_step":   "await_payment",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# RAG TOOL NODE (FAQ mid-booking)
# ═══════════════════════════════════════════════════════════════════════════════
def rag_tool_node(state: BookingState) -> dict:
    previous_step = state.get("current_step", "collect_pickup")
    query         = state.get("faq_query", "")

    try:
        from rag.retriever import get_retriever
        retriever = get_retriever(k=3)
        docs      = retriever.invoke(query)
        context   = "\n\n".join(d.page_content for d in docs) if docs else ""

        if context:
            prompt = (
                "You are the SureRide AI assistant. Use ONLY the context below to answer "
                "the customer's question concisely and in a friendly, conversational tone. "
                "Do not make up information. Keep the answer under 4 sentences.\n\n"
                f"Context:\n{context}\n\n"
                f"Customer question: {query}\n\nAnswer:"
            )
            response = llm.invoke(prompt)
            answer   = response.content.strip()
        else:
            answer = "I don't have that detail right now — type *help* to reach our support team."

    except Exception:
        answer = "I'm loading my knowledge base. Please try again in a moment!"

    prompt_append = ""
    if previous_step == "collect_name":
        prompt_append = "\n\nFirst, may I have your name?"
    elif previous_step == "collect_pickup":
        prompt_append = "\n\nWhere would you like to be *picked up* from?"
    elif previous_step == "collect_destination":
        prompt_append = "\n\nAnd where are you headed?"

    reply = f"ℹ️ {answer}\n\nNow, back to your booking…{prompt_append}"
    return {
        "messages":    [AIMessage(content=reply)],
        "faq_answer":  answer,
        "current_step": previous_step,
    }
