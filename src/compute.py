from __future__ import annotations

from datetime import date, timedelta
from statistics import median
from typing import Any, Dict, List, Tuple

from .schemas import (
    QuerySpec,
    TimeRange,
    Transaction,
    RecurringPayment,
    UIChart,
    UIForm,
    UIFormField,
    UIMessage,
    UITable,
    UISpec,
)

# --------------------------
# Helpers
# --------------------------

def money(x: float) -> str:
    return f"${x:,.2f}"

def is_spend(tx: Transaction) -> bool:
    return tx.direction == "debit"

def is_posted(tx: Transaction) -> bool:
    return not tx.isPending

def _month_bounds(d: date) -> Tuple[date, date]:
    start = d.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end

def resolve_time_range(tr: TimeRange | None) -> Tuple[date, date]:
    """
    Returns (start_date, end_date_exclusive).
    If tr is None, returns a default range (last 30 days).
    """
    today = date.today()
    end = today + timedelta(days=1)
    
    if tr is None:
        # Default: last 30 days
        return today - timedelta(days=30), end

    if tr.mode == "preset":
        if tr.preset == "ytd":
            return date(today.year, 1, 1), end
        if tr.preset == "last_month":
            first_this_month, _ = _month_bounds(today)
            last_day_prev_month = first_this_month - timedelta(days=1)
            return _month_bounds(last_day_prev_month)

    if tr.mode == "relative":
        n = int(tr.last or 30)
        unit = tr.unit or "days"
        days = {
            "days": n,
            "weeks": 7 * n,
            "months": 30 * n,  # MVP approximation (OK for demo)
            "years": 365 * n,  # MVP approximation
        }[unit]
        return today - timedelta(days=days), end

    if tr.mode == "custom":
        start = date.fromisoformat(tr.start)  # type: ignore[arg-type]
        end2 = date.fromisoformat(tr.end) + timedelta(days=1)  # type: ignore[arg-type]
        return start, end2

    # fallback
    return today - timedelta(days=30), end


# --------------------------
# UI builders
# --------------------------

def table_transactions(title: str, txs: List[Transaction], limit: int = 50) -> UITable:
    txs_sorted = sorted(txs, key=lambda t: t.postedAt, reverse=True)[:limit]
    rows: List[List[Any]] = []

    for t in txs_sorted:
        rows.append([
            t.id,
            t.postedAt.date().isoformat(),
            "PENDING" if t.isPending else "POSTED",
            t.merchant.name,
            t.merchant.category,
            t.merchant.subcategory,
            money(t.amount),
            t.direction,
            t.paymentRail or "",
            t.cardLast4 or "",
        ])

    return UITable(
        title=title,
        columns=[
            "id", "date", "status", "merchant", "category", "subcategory",
            "amount", "direction", "payment_rail", "card_last4"
        ],
        rows=rows,
    )


def dispute_form_for_transaction(t: Transaction) -> UIForm:
    # Keep it minimal + prefilled (UI can add dropdowns later)
    return UIForm(
        formId="dispute_transaction_v1",
        title="Report an unrecognized transaction",
        fields=[
            UIFormField(name="transactionId", label="Transaction ID", value=t.id, required=True),
            UIFormField(name="merchant", label="Merchant", value=t.merchant.name, required=True),
            UIFormField(name="date", label="Date", value=t.postedAt.date().isoformat(), required=True),
            UIFormField(name="amount", label="Amount", value=money(t.amount), required=True),
            UIFormField(name="reason", label="Reason (not mine / duplicate / wrong amount)", value="", required=True),
            UIFormField(name="notes", label="Notes (optional)", value="", required=False),
        ],
        actions=[{"type": "submit", "label": "Start dispute"}],
    )


# --------------------------
# 4 core handlers
# --------------------------

def _describe_range(tr: TimeRange | None) -> str:
    if tr is None:
        return "recent history"
    if tr.mode == "preset" and tr.preset == "ytd":
        return "year-to-date"
    if tr.mode == "preset" and tr.preset == "last_month":
        return "last month"
    if tr.mode == "relative" and tr.last and tr.unit:
        return f"the last {tr.last} {tr.unit}"
    if tr.mode == "custom" and tr.start and tr.end:
        return f"{tr.start} to {tr.end}"
    return "recent history"


def handle_transactions_list(q: QuerySpec, txs: List[Transaction]) -> UISpec:
    limit = int(q.params.get("limit", 50))
    shown = min(limit, len(txs))
    label = _describe_range(q.time_range)

    ui = UISpec(
        messages=[UIMessage(content=f"Here are your transactions from **{label}** (showing **{shown}**).")],
        components=[table_transactions("Transactions", txs, limit=limit)],
    )
    return ui


def handle_top_spending_ytd(q: QuerySpec, txs: List[Transaction]) -> UISpec:
    # posted debits only for analytics
    spend = [t for t in txs if is_spend(t) and is_posted(t)]

    total = sum(t.amount for t in spend)
    top_k = int(q.params.get("top_k", 5))

    by_cat: Dict[str, float] = {}
    by_merch: Dict[str, float] = {}

    for t in spend:
        by_cat[t.merchant.category] = by_cat.get(t.merchant.category, 0.0) + t.amount
        by_merch[t.merchant.name] = by_merch.get(t.merchant.name, 0.0) + t.amount

    top_categories = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:top_k]
    top_merchants = sorted(by_merch.items(), key=lambda x: x[1], reverse=True)[:top_k]

    ui = UISpec(
        messages=[UIMessage(content=f"Total spending (posted debits): **{money(total)}**")],
        components=[
            UIChart(
                title=f"Top {len(top_categories)} categories",
                chartType="pie",
                data=[{"category": k, "total": round(v, 2)} for k, v in top_categories],
            ),
            UIChart(
                title=f"Top {len(top_merchants)} merchants",
                chartType="bar",
                data=[{"merchant": k, "total": round(v, 2)} for k, v in top_merchants],
            ),
        ],
    )
    return ui


def handle_unrecognized_transaction(tx: Transaction) -> UISpec:
    # No balances/holds in your current schema, so keep explanation simple + bank-real
    lines = [
        "Here’s what I see for that transaction:",
        f"- Merchant: **{tx.merchant.name}** ({tx.merchant.category} / {tx.merchant.subcategory})",
        f"- Amount: **{money(tx.amount)}** ({tx.direction})",
        f"- Date: **{tx.postedAt.date().isoformat()}**",
        f"- Status: **{'PENDING' if tx.isPending else 'POSTED'}**",
    ]

    if tx.paymentRail:
        rail = tx.paymentRail
        if rail == "Card" and tx.cardLast4:
            rail += f" (card •••• {tx.cardLast4})"
        lines.append(f"- Method: **{rail}**")

    if tx.isPending:
        lines.append("")
        lines.append("Pending card charges can change slightly when posted, or disappear if canceled.")
        lines.append("If you still don’t recognize it after it posts, you can start a dispute below.")
    else:
        lines.append("")
        lines.append("If you don’t recognize it, you can start a dispute below (a team member will review).")

    ui = UISpec(
        messages=[UIMessage(content="\n".join(lines))],
        components=[dispute_form_for_transaction(tx)],
    )
    return ui


# --------------------------
# Recurring detection (pure deterministic)
# --------------------------

def _classify_cadence(median_gap_days: float) -> str:
    targets = [
        ("weekly", 7),
        ("biweekly", 14),
        ("monthly", 30),
        ("quarterly", 90),
        ("yearly", 365),
    ]
    best_name = "unknown"
    best_score = 0.0

    for name, target in targets:
        diff = abs(median_gap_days - target)
        score = max(0.0, 1.0 - (diff / target))  # 1.0 is perfect match
        if score > best_score:
            best_name = name
            best_score = score

    # Require a decent match; otherwise call it unknown
    return best_name if best_score >= 0.75 else "unknown"


def detect_recurring_payments(txs: List[Transaction], min_occurrences: int = 3) -> List[RecurringPayment]:
    # posted debits only
    debits = [t for t in txs if is_spend(t) and is_posted(t)]

    by_merchant: Dict[str, List[Transaction]] = {}
    for t in debits:
        by_merchant.setdefault(t.merchant.name, []).append(t)

    out: List[RecurringPayment] = []

    for merch, items in by_merchant.items():
        if len(items) < min_occurrences:
            continue

        items.sort(key=lambda t: t.postedAt)
        gaps: List[int] = []
        for i in range(1, len(items)):
            gaps.append((items[i].postedAt.date() - items[i - 1].postedAt.date()).days)

        if not gaps:
            continue

        med = float(median(gaps))
        cadence = _classify_cadence(med)
        if cadence == "unknown":
            continue

        avg_amt = sum(t.amount for t in items) / len(items)
        last_seen = items[-1].postedAt

        out.append(RecurringPayment(
            merchant=merch,
            cadence=cadence,  # type: ignore
            averageAmount=round(avg_amt, 2),
            occurrences=len(items),
            lastSeenAt=last_seen,
        ))

    # sort: most frequent & largest first
    out.sort(key=lambda r: (r.occurrences, r.averageAmount), reverse=True)
    return out


def handle_recurring_payments(q: QuerySpec, txs: List[Transaction]) -> UISpec:
    min_occ = int(q.params.get("min_occurrences", 3))
    rec = detect_recurring_payments(txs, min_occurrences=min_occ)

    rows: List[List[Any]] = []
    for r in rec[:25]:
        rows.append([
            r.merchant,
            r.cadence,
            money(r.averageAmount),
            str(r.occurrences),
            r.lastSeenAt.date().isoformat(),
        ])

    ui = UISpec(
        messages=[UIMessage(content=f"Found **{len(rec)}** likely recurring payments (posted debits only).")],
        components=[
            UITable(
                title="Recurring payments / subscriptions",
                columns=["merchant", "cadence", "avg_amount", "occurrences", "last_seen"],
                rows=rows,
            )
        ],
    )
    return ui
