import re
from typing import Any, Optional, cast

from src.config import OLLAMA_MODEL, OLLAMA_URL
from src.llm import query_spec_call_llm
from src.schemas import ConversationContext, QuerySpec, TimeRange
from src.prompts import QUERY_SPEC_SYSTEM_PROMPT

async def compile_queryspec(message: str, context: Optional[ConversationContext] = None) -> QuerySpec:
    if not OLLAMA_MODEL or not OLLAMA_URL:
        raise ValueError("OLLAMA_MODEL and OLLAMA_URL must be set")
    try:
        llm_response = await query_spec_call_llm(QUERY_SPEC_SYSTEM_PROMPT, message)
        
        # If intent is unrecognized_transaction and context has selectedTransactionId, inject it
        if llm_response.intent == "unrecognized_transaction" and context and context.selectedTransactionId:
            # Create new QuerySpec with updated params (Pydantic models are immutable)
            updated_params: dict[str, Any] = {**llm_response.params, "transaction_id": context.selectedTransactionId}
            llm_response = QuerySpec(
                is_banking_domain=llm_response.is_banking_domain,
                intent=llm_response.intent,
                time_range=llm_response.time_range,
                params=updated_params
            )
        
        return llm_response
    except Exception as e:
       print(f"LLM query spec failed: {e}, falling back to rules-based")
       return _compile_rules(message, context)


def _compile_rules(message: str, context: Optional[ConversationContext]) -> QuerySpec:
    text = (message or "").lower().strip()

    # ---- 1) intent detection (only 4) ----
    if (
        "don't recognize" in text
        or "dont recognize" in text
        or "unrecognized" in text
        or ("what is this" in text and ("charge" in text or "transaction" in text))
    ):
        tx_id = _extract_tx_id(text) or (context.selectedTransactionId if context else None)
        return QuerySpec(
            is_banking_domain=True,
            intent="unrecognized_transaction",
            time_range=_default_time("unrecognized_transaction"),
            params={"transaction_id": tx_id},
        )

    if "recurring" in text or "subscription" in text or "subscriptions" in text:
        return QuerySpec(
            is_banking_domain=True,
            intent="recurring_payments",
            time_range=_default_time("recurring_payments"),
            params={"min_occurrences": 3},
        )

    if ("top" in text and ("spend" in text or "spending" in text)) and ("year" in text or "ytd" in text or "this year" in text):
        return QuerySpec(
            is_banking_domain=True,
            intent="top_spending_ytd",
            time_range=TimeRange(mode="preset", preset="ytd"),
            params={"top_k": 5},
        )

    # transactions list: if they mention transactions at all
    if "transaction" in text or "transactions" in text:
        tr = _parse_time_range(text) or _default_time("transactions_list")
        limit = _parse_limit(text) or 50
        return QuerySpec(
            is_banking_domain=True,
            intent="transactions_list",
            time_range=tr,
            params={"limit": limit, "include_pending": True},
        )

    # safe fallback: show last 30 days transactions
    return QuerySpec(
        is_banking_domain=True,
        intent="transactions_list",
        time_range=_default_time("transactions_list"),
        params={"limit": 50, "include_pending": True},
    )


def _default_time(intent: str) -> TimeRange:
    if intent == "top_spending_ytd":
        return TimeRange(mode="preset", preset="ytd")
    if intent == "recurring_payments":
        return TimeRange(mode="relative", last=3, unit="months")
    return TimeRange(mode="relative", last=30, unit="days")


def _parse_time_range(text: str) -> Optional[TimeRange]:
    if "this year" in text or "ytd" in text or "year to date" in text:
        return TimeRange(mode="preset", preset="ytd")
    if "last month" in text:
        return TimeRange(mode="preset", preset="last_month")

    m = re.search(r"\b(last|past|previous)\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)\b", text)
    if not m:
        return None

    n = int(m.group(2))
    unit_word = m.group(3)
    unit = {
        "day": "days", "days": "days",
        "week": "weeks", "weeks": "weeks",
        "month": "months", "months": "months",
        "year": "years", "years": "years",
    }[unit_word]

    from src.schemas import TimeUnit
    return TimeRange(mode="relative", last=n, unit=cast(TimeUnit, unit))


def _parse_limit(text: str) -> Optional[int]:
    # "last 10 transactions" / "recent 10 transactions"
    m = re.search(r"\b(last|recent)\s+(\d+)\s+transactions?\b", text)
    return int(m.group(2)) if m else None


def _extract_tx_id(text: str) -> Optional[str]:
    m = re.search(r"\b(t\d{3})\b", text)
    return m.group(1) if m else None
