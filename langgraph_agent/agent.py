"""
langgraph_agent/agent.py

SureRide booking agent — dispatcher pattern.

The graph has a single 'dispatcher' node that reads current_step
and delegates to the correct handler. One invoke() = one turn.
State is kept by the caller (Streamlit session_state).

Public API:
    from langgraph_agent.agent import run_turn, new_state
"""
from langgraph.graph import StateGraph, END
from langgraph_agent.state import BookingState
from langgraph_agent.nodes import (
    greet_node,
    collect_name_node,
    collect_pickup_node,
    validate_pickup_node,
    collect_destination_node,
    validate_destination_node,
    show_fare_node,
    confirm_fare_node,
    check_payment_node,
    rag_tool_node,
)

# ── FAQ detection ─────────────────────────────────────────────────────────────
_FAQ_STARTERS = ("how", "what", "where", "when", "is", "do", "does",
                 "can", "are", "who", "why", "which")
# Steps where FAQ intercept is disabled (user must give a specific answer)
_NO_FAQ_STEPS = {"greet", "collect_name", "validate_pickup",
                 "validate_destination", "show_fare",
                 "confirm_fare", "await_payment", "done"}

def _is_faq(text: str, step: str) -> bool:
    if step in _NO_FAQ_STEPS:
        return False
    s = text.strip().lower()
    first = s.split()[0] if s.split() else ""
    return s.endswith("?") or first in _FAQ_STARTERS


# ── Step → node mapping ───────────────────────────────────────────────────────
_STEP_HANDLERS = {
    "greet":                greet_node,
    "collect_name":         collect_name_node,
    "collect_pickup":       collect_pickup_node,
    "validate_pickup":      validate_pickup_node,
    "collect_destination":  collect_destination_node,
    "validate_destination": validate_destination_node,
    "show_fare":            show_fare_node,
    "confirm_fare":         confirm_fare_node,
    "await_payment":        check_payment_node,
    "done":                 lambda s: {},
}


# ── Dispatcher ────────────────────────────────────────────────────────────────
def dispatcher(state: BookingState) -> dict:
    step     = state.get("current_step", "greet")
    messages = state.get("messages", [])

    # Auto-advance steps that don't wait for user input — run immediately
    if step in ("validate_pickup", "validate_destination", "show_fare"):
        return _STEP_HANDLERS[step](state)

    # No messages or last message is AI → greet
    if not messages or messages[-1].type != "human":
        return greet_node(state)

    user_text = messages[-1].content

    # FAQ intercept
    if _is_faq(user_text, step):
        state["faq_query"] = user_text
        return rag_tool_node(state)

    handler = _STEP_HANDLERS.get(step, greet_node)
    return handler(state)


# ── Build & compile ───────────────────────────────────────────────────────────
builder = StateGraph(BookingState)
builder.add_node("dispatcher", dispatcher)
builder.set_entry_point("dispatcher")
builder.add_edge("dispatcher", END)
graph = builder.compile()


# ── Public helpers ────────────────────────────────────────────────────────────
def new_state() -> BookingState:
    """Return a clean initial BookingState."""
    return {
        "messages":            [],
        "user_name":           None,
        "pickup_raw":          None,
        "destination_raw":     None,
        "pickup_zone":         None,
        "destination_zone":    None,
        "distance_km":         None,
        "fare_kes":            None,
        "surge_applied":       False,
        "booking_confirmed":   False,
        "awaiting_confirmation": False,
        "pesapal_order_id":    None,
        "pesapal_pay_url":     None,
        "payment_status":      "none",
        "current_step":        "greet",
        "faq_query":           None,
        "faq_answer":          None,
    }


def run_turn(
    state: BookingState,
    user_input: str | None = None,
) -> tuple[str, BookingState]:
    """
    Process one conversation turn.

    Args:
        state:      Current BookingState.
        user_input: The user's message (None = opening greeting).

    Returns:
        (bot_reply_text, updated_state)
    """
    from langchain_core.messages import HumanMessage

    if user_input is not None:
        state["messages"].append(HumanMessage(content=user_input))

    # Auto-run validation / fare steps that don't need user input
    result = graph.invoke(state)

    # If the new step also requires no user input, chain immediately
    auto_steps = ("validate_pickup", "validate_destination", "show_fare")
    while result.get("current_step") in auto_steps:
        result = graph.invoke(result)

    ai_msg = next((m for m in reversed(result["messages"]) if m.type == "ai"), None)
    reply  = ai_msg.content if ai_msg else "Sorry, something went wrong."
    return reply, result
