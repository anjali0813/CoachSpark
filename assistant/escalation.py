"""
escalation.py - Coach Spark Supervisor Escalation Guard

A system prompt alone isn't a reliable enough guarantee against soft
hallucination -- a model can follow "never invent procedures" and still
quietly fill a gap with general safety knowledge that isn't actually in
the retrieved manual (e.g. recommending lockout/tagout steps that were
never in the source text). This module is a deterministic backend
safety net: if the model's own wording signals that the manuals don't
fully cover the question, we append one consistent, unambiguous
instruction -- contact your supervisor -- instead of trusting whatever
partial workaround the model came up with on its own.
"""

ESCALATION_NOTE = (
    "\n\n🙋 **Please note:** this specific procedure isn't fully covered in the "
    "training manuals. For safety, contact your supervisor or the maintenance "
    "team before proceeding."
)

# Phrases that indicate the model itself is signalling an information gap.
# Deliberately broad (recall over precision) -- in a shop-floor safety
# context, an unnecessary reminder to check with a supervisor is a much
# smaller cost than a missed one.
GAP_PHRASES = [
    "doesn't specifically address",
    "does not specifically address",
    "not specifically address",
    "isn't specifically covered",
    "not specifically covered",
    "doesn't cover",
    "does not cover",
    "isn't covered",
    "not covered in",
    "not provided in this manual",
    "not provided in the manual",
    "no specific instructions",
    "not specified in the manual",
    "unclear from the manual",
    "manual doesn't",
    "manual does not",
    "manuals don't",
    "manuals do not",
    "refer to a different document",
    "refer to a different procedure",
    "may need to refer to",
    "outside the scope of this manual",
    "not addressed in the manual",
    "exact steps to clear",
    "not explicitly stated",
    "not explicitly mentioned",
]

# If the model already told the person to contact a supervisor on its
# own, don't pile on a second, redundant note.
ALREADY_ESCALATED_PHRASES = [
    "contact your supervisor",
    "ask your supervisor",
    "check with your supervisor",
    "speak to your supervisor",
    "contact the maintenance team",
]


def needs_escalation(answer: str) -> bool:
    """True if the answer's own wording signals an information gap."""
    lowered = answer.lower()
    return any(phrase in lowered for phrase in GAP_PHRASES)


def already_escalated(answer: str) -> bool:
    """True if the answer already tells the person to contact a supervisor."""
    lowered = answer.lower()
    return any(phrase in lowered for phrase in ALREADY_ESCALATED_PHRASES)


def apply_escalation_guard(answer: str) -> str:
    """
    Append a consistent supervisor-escalation note if the answer signals
    a coverage gap and doesn't already include one. Safe to call on
    every answer -- it's a no-op when the answer is fully grounded.
    """
    if needs_escalation(answer) and not already_escalated(answer):
        return answer + ESCALATION_NOTE
    return answer