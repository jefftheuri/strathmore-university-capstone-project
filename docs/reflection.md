# SureRide — Capstone Academic Reflection Essay

**Author:** SureRide Project Developer  
**Institution:** iLabAfrica, Strathmore University  
**Program:** AI Practitioner Programme (AIPP)  
**Date:** June 2026  

---

### Introduction: AI for Road Safety
Drunk driving remains a leading cause of tragic road fatalities in Kenya, with the National Transport and Safety Authority (NTSA) attributing over 30% of annual accidents to alcohol impairment. The primary barrier to safety is not a lack of concern, but rather the friction of booking rides late at night when impaired. SureRide was conceived to address this specific friction point by utilizing an AI-powered conversational agent that makes ride booking as simple as sending a WhatsApp text. The project successfully demonstrates how stateful AI orchestration and retrieval-augmented generation (RAG) can be integrated to solve a critical, real-world societal challenge.

### What Worked Well: Architecture & Grounding
The core technical execution rested on two pillars: **LangGraph** for conversation management and **ChromaDB + Google Gemini** for FAQ grounding. Implementing a stateful, deterministic dispatcher pattern in LangGraph proved highly successful. It kept the conversation on track and avoided loop traps. RAG grounding ensured that policy queries—such as pricing rules or service areas—were answered strictly using verified company documents, eliminating the risk of LLM hallucinations. Furthermore, the frontend upgrade to an authentic WhatsApp-style UI in Streamlit created a familiar, low-cognitive-load interface suited for late-night use.

### Technical Challenges & Mitigations
Developing the application presented several engineering hurdles:
1.  **Streamlit Iframe Rendering:** Integrating custom CSS within Streamlit is notoriously difficult because its layout engine strips external styles. The solution was rendering the chat bubbles inside a secure iframe component (`components.html`), which isolated the styles but introduced height calculation and scrolling complexities. These were resolved by dynamically estimating the iframe height based on the message count and using a scroll injection script.
2.  **Payment Gateway Integration:** Transitioning from mock payment simulations to a live **PesaPal v3 REST API** was a significant challenge. Handling production secrets safely via environment variables and managing real-time payment validation required building robust background polling checks. Since Streamlit runs locally without a public callback URL, we mitigated webhook limitations by implementing a secure manual polling button that queries the PesaPal status API directly.

### Project Limitations & Future Directions
Despite its successes, the SureRide prototype has clear limitations:
*   **Geofencing Restraints:** To manage driver availability and prevent routing errors during the pilot, service is restricted to 19 Nairobi zones. While this mitigates early capacity risks, it restricts broader accessibility.
*   **Heuristic Extraction:** User names are parsed using basic string splits. This can fail for compound names or greeting messages.
*   **Language Barrier:** The agent currently processes and responds only in English, neglecting Swahili-speaking users.

Future iterations will replace Haversine calculations with the Google Maps Directions API to obtain exact road routes. We will also integrate a Swahili-compatible LLM to localize the service, replace heuristics with named-entity recognition (NER) for name extraction, and implement secure, KDPA-compliant database persistence for conversation logs.

### Lessons Learned: Design Principles for Responsible AI
Perhaps the most valuable lesson from this capstone was discovering that responsible AI design is not an afterthought — it must be embedded into every architectural decision. The choice to use a hard-coded LangGraph dispatcher rather than a free-form LLM for conversation flow was driven as much by ethical reasoning (preventing hallucinated bookings) as by engineering preference. Similarly, the decision to delegate all payment processing to PesaPal's hosted pages — rather than collecting card numbers directly — was the correct KDPA-compliance decision even though it added integration complexity. This principle — that safety constraints and ethical guardrails often produce better engineering outcomes — is one I intend to carry into all future AI system design. The SureRide project demonstrated in practice what the AIPP curriculum articulated in theory: that the most impactful AI systems are those built with accountability, explainability, and user safety as first-class design requirements, not compliance checkboxes applied at the end.

---

*This reflective essay fulfills the academic reflection standard of the AIPP Capstone Project Assessment.*
