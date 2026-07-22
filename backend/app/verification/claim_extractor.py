"""
Splits generated narrative into individual claims - the unit that gets
checked against ComputedChart. This is what makes "hallucination rate"
a countable ratio instead of a vague impression of the whole paragraph.

Two passes:

1. Sentence-boundary splitting (fast, free, no API cost).
2. Compound-claim splitting within each sentence: many generated
   sentences fuse a factual placement with interpretive commentary in
   one clause - "The Moon is in the 3rd house, often relating to
   communication." Checking that whole sentence as one claim means the
   interpretive tail rides along on the factual head's verdict, which
   under-counts what's actually being asserted. Splitting on a fixed set
   of known interpretive connector phrases turns that into two claims:
   the factual half (checkable against ComputedChart) and the
   interpretive half (correctly routed to "unverifiable" rather than
   silently inheriting "grounded").

Known limitation, same spirit as before: this catches the connector
phrases in INTERPRETIVE_CONNECTORS specifically. A sentence phrased with
an interpretive connector not in this list still gets treated as one
claim. Expanding this list as real generated narratives surface new
phrasing is expected, ordinary maintenance - not a redesign.
"""

import re

from app.models.verification import ExtractedClaim

SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

INTERPRETIVE_CONNECTORS = [
    "often relates to", "often relate to", "is often associated with",
    "are often associated with", "often associated with", "which often",
    "typically indicates", "which suggests", "often suggesting", "suggesting",
    "indicating", "often brings", "which typically", "often means",
    "which is associated with", "tends to bring", "which indicates", "often bringing",
]


def _split_compound(sentence: str) -> list[str]:
    lowered = sentence.lower()
    for connector in INTERPRETIVE_CONNECTORS:
        idx = lowered.find(connector)
        if idx > 0:  # must not be at the very start - need a factual clause before it
            before = sentence[:idx].strip().rstrip(",")
            after = sentence[idx:].strip()
            if before and after:
                if not before.endswith((".", "!", "?")):
                    before += "."
                return [before, after]
    return [sentence]


def extract_claims(narrative: str, source_model: str) -> list[ExtractedClaim]:
    sentences = SENTENCE_BOUNDARY.split(narrative.strip())
    claims = []
    for s in sentences:
        s = s.strip()
        if len(s) < 8:  # skip stray fragments / empty splits
            continue
        for sub_claim in _split_compound(s):
            sub_claim = sub_claim.strip()
            if len(sub_claim) < 8:
                continue
            claims.append(ExtractedClaim(text=sub_claim, source_model=source_model))
    return claims
