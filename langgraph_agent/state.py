"""
langgraph_agent/state.py

Defines the shared state that flows through every node in the
SureRide LangGraph booking agent.
"""
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class BookingState(TypedDict):
    """Complete state for the SureRide booking conversation."""

    # Conversation history (append-only via add_messages reducer)
    messages: Annotated[list, add_messages]

    # Raw user input (unvalidated)
    user_name:          Optional[str]
    pickup_raw:         Optional[str]   # what the user typed
    destination_raw:    Optional[str]   # what the user typed

    # Validated zone names (from utils/zones.py)
    pickup_zone:        Optional[str]   # e.g. "Westlands"
    destination_zone:   Optional[str]   # e.g. "Karen"

    # Pricing
    distance_km:        Optional[float]
    fare_kes:           Optional[int]
    surge_applied:      bool

    # Booking confirmation
    booking_confirmed:  bool
    awaiting_confirmation: bool

    # Payment (PesaPal)
    pesapal_order_id:   Optional[str]
    pesapal_pay_url:    Optional[str]
    payment_status:     str            # "none" | "pending" | "completed" | "failed"

    # Flow control
    current_step: str
    # greet | collect_name | collect_pickup | validate_pickup |
    # collect_destination | validate_destination | show_fare |
    # confirm_fare | await_payment | done

    # RAG
    faq_query:  Optional[str]
    faq_answer: Optional[str]
