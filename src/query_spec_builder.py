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
        
        # Post-processing: Essential fixes only
        message_lower = message.lower()
        
        # Fix 1: Year to date queries should show all transactions
        if ("year to date" in message_lower or "ytd" in message_lower or "this year" in message_lower):
            updated_params = {k: v for k, v in llm_response.params.items() if k not in ["limit_only", "limit"]}
            updated_params["limit"] = 1000
            llm_response = QuerySpec(
                is_banking_domain=llm_response.is_banking_domain,
                intent=llm_response.intent,
                time_range=TimeRange(mode="preset", preset="ytd"),
                params=updated_params
            )
        
        # Fix 1b: Clean up preset time ranges (this_month, last_month)
        # If preset is set, ensure mode="preset" and clear relative fields
        if llm_response.time_range and llm_response.time_range.preset in ["this_month", "last_month"]:
            llm_response = QuerySpec(
                is_banking_domain=llm_response.is_banking_domain,
                intent=llm_response.intent,
                time_range=TimeRange(
                    mode="preset",
                    preset=llm_response.time_range.preset,
                    last=None,
                    unit=None
                ),
                params=llm_response.params
            )
        
        # Fix 1c: Force preset mode for "last month" phrase (LLM often misclassifies this)
        if "last month" in message_lower and llm_response.time_range:
            if llm_response.time_range.mode == "relative" and llm_response.time_range.last == 30 and llm_response.time_range.unit == "days":
                # LLM incorrectly interpreted "last month" as "last 30 days"
                llm_response = QuerySpec(
                    is_banking_domain=llm_response.is_banking_domain,
                    intent=llm_response.intent,
                    time_range=TimeRange(mode="preset", preset="last_month", last=None, unit=None),
                    params=llm_response.params
                )
        
        # Fix 2: Ensure count-based queries have time_range=null and include the limit
        # But first check if we need to CLEAR limit_only if there's actually a time range
        has_time_pattern = _parse_time_range(message_lower) is not None
        has_count_pattern = _parse_limit(message_lower) is not None
        
        if has_time_pattern and llm_response.params.get("limit_only"):
            # LLM incorrectly set limit_only for a time-based query - fix it
            updated_params = {k: v for k, v in llm_response.params.items() if k != "limit_only"}
            llm_response = QuerySpec(
                is_banking_domain=llm_response.is_banking_domain,
                intent=llm_response.intent,
                time_range=llm_response.time_range if llm_response.time_range else _parse_time_range(message_lower),
                params=updated_params
            )
        elif llm_response.params.get("limit_only") or (has_count_pattern and not has_time_pattern):
            # This is a count-based query
            updated_params = llm_response.params.copy()
            updated_params["limit_only"] = True
            if "limit" not in updated_params or updated_params["limit"] is None:
                parsed_limit = _parse_limit(message_lower)
                updated_params["limit"] = parsed_limit if parsed_limit else 50
            llm_response = QuerySpec(
                is_banking_domain=llm_response.is_banking_domain,
                intent=llm_response.intent,
                time_range=None,
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
        tr = _parse_time_range(text)
        parsed_limit = _parse_limit(text)
        limit = parsed_limit if parsed_limit is not None else 50
        
        # If user is asking for a specific count and no time range mentioned,
        # don't set a time range (limit-only mode)
        params = {"limit": limit, "include_pending": True}
        if parsed_limit is not None and tr is None:
            params["limit_only"] = True
            # Leave tr as None for count-based queries
        else:
            # Only set default time range if user didn't specify a count-only query
            tr = tr or _default_time("transactions_list")
        
        return QuerySpec(
            is_banking_domain=True,
            intent="transactions_list",
            time_range=tr,
            params=params,
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
    if "this month" in text:
        return TimeRange(mode="preset", preset="this_month")
    if "last month" in text:
        return TimeRange(mode="preset", preset="last_month")
    # Handle "last week" without a number
    if "last week" in text:
        from src.schemas import TimeUnit
        return TimeRange(mode="relative", last=1, unit=cast(TimeUnit, "weeks"))

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
    # Patterns: "last 10 transactions", "give me 20 transactions", "I need 15 transactions"
    # Try pattern with verb/adjective first: "(give me|show|last|recent) N transactions"
    m = re.search(r"\b(give\s+me|show\s+me|show|last|recent|my|need|want)\s+(\d+)\s+transactions?\b", text)
    if m:
        return int(m.group(2))
    # Also try simple "N transactions" pattern
    m = re.search(r"\b(\d+)\s+transactions?\b", text)
    if m:
        return int(m.group(1))
    return None


def _extract_tx_id(text: str) -> Optional[str]:
    m = re.search(r"\b(t\d{3})\b", text)
    return m.group(1) if m else None
