from typing import List
import httpx

from src.config import TOOL_BASE_URL
from src.compute import (
    handle_recurring_payments,
    handle_top_spending_ytd,
    handle_transactions_list,
    handle_unrecognized_transaction,
    resolve_time_range
)
from src.query_spec_builder import compile_queryspec
from src.schemas import ChatRequest, ChatResponse, Transaction, UIMessage, UISpec

# ----------------------------
# Tool calls
# ----------------------------

async def tool_get_transactions(account_id: str, start: str, end: str) -> List[Transaction]:
    """Fetch transactions from the tool API."""
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{TOOL_BASE_URL}/tool/transactions", params={
            "accountId": account_id,
            "start": start,
            "end": end,
        })
        r.raise_for_status()
        return [Transaction.model_validate(x) for x in r.json()]

async def tool_get_transaction_by_id(account_id: str, tx_id: str) -> Transaction:
    """Fetch a single transaction by ID from the tool API."""
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{TOOL_BASE_URL}/tool/transactions/{tx_id}", params={"accountId": account_id})
        r.raise_for_status()
        return Transaction.model_validate(r.json())

# ----------------------------
# Orchestration logic
# ----------------------------

async def orchestrate_chat(req: ChatRequest) -> ChatResponse:
    """
    Main orchestration logic for chat requests.
    
    Flow:
    1. Compile user message into QuerySpec
    2. Validate it's a banking domain query
    3. Route based on intent:
       - unrecognized_transaction: needs tx_id
       - others: fetch transactions and compute UI
    4. Return ChatResponse with UI specification
    """
    q = await compile_queryspec(req.message, req.context)
    
    if not q.is_banking_domain:
        ui = UISpec(messages=[UIMessage(
            content="I can help with banking/account questions (transactions, spending, balance). What would you like to check?"
        )])
        return ChatResponse(query=q, ui=ui)
    
    # 1) Unrecognized transaction: needs tx id (from params OR UI context)
    if q.intent == "unrecognized_transaction":
        tx_id = None
        if q.params.get("transaction_id"):
            tx_id = str(q.params["transaction_id"])
        elif req.context and req.context.selectedTransactionId:
            tx_id = req.context.selectedTransactionId

        if not tx_id:
            ui = UISpec(messages=[UIMessage(
                content="Which transaction do you mean? Please select a transaction row (or provide its transaction id)."
            )])
            return ChatResponse(query=q, ui=ui)

        tx = await tool_get_transaction_by_id(req.accountId, tx_id)
        ui = handle_unrecognized_transaction(tx)
        return ChatResponse(query=q, ui=ui)

    # 2) For the other intents: pull transactions for a single resolved range
    start_d, end_d = resolve_time_range(q.time_range)
    txs = await tool_get_transactions(req.accountId, start_d.isoformat(), end_d.isoformat())

    if q.intent == "transactions_list":
        ui = handle_transactions_list(q, txs)
    elif q.intent == "top_spending_ytd":
        ui = handle_top_spending_ytd(q, txs)
    elif q.intent == "recurring_payments":
        ui = handle_recurring_payments(q, txs)
    else:
        ui = UISpec(messages=[UIMessage(
            content="I didn't understand that request. Try: top spendings this year, last 30 days transactions, recurring subscriptions, or dispute a transaction."
        )])

    return ChatResponse(query=q, ui=ui)
    

