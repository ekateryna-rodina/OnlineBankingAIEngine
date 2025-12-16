from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, model_validator

# =========================
# Tool data schemas
# =========================

class Merchant(BaseModel):
    name: str
    category: str
    subcategory: str

class Transaction(BaseModel):
    id: str
    accountId: str
    postedAt: datetime
    direction: Literal["debit", "credit"]
    amount: float
    merchant: Merchant
    isPending: bool = False
    paymentRail: Optional[Literal["Card", "ACH", "Zelle", "Wire", "Check", "ATM"]] = None
    cardLast4: Optional[str] = None

# =========================
# Derived analytics
# =========================

Cadence = Literal["weekly", "biweekly", "monthly", "quarterly", "yearly", "unknown"]

class RecurringPayment(BaseModel):
    merchant: str
    cadence: Cadence = "unknown"
    averageAmount: float
    occurrences: int
    lastSeenAt: datetime

class CategoryTotal(BaseModel):
    category: str
    total: float

# =========================
# QuerySpec 
# Only 4 intents supported for now:
# 1. “What are my top spendings this year?” * Output: category + merchant breakdown (UISpec chart + summary) 
# 2. “List my transactions for the last 30 days” * Output: table (include transaction id) 
# 3. “I don’t recognize this transaction” * Requires context: selectedTransactionId from previous table * Output: explain posted vs pending + holds, and return a Dispute Form (FormSpec) prefilled 
# 4. “Show me recurring payments/subscriptions”
# =========================

Intent = Literal[
    "top_spending_ytd",
    "transactions_list",
    "recurring_payments",
    "unrecognized_transaction",
]


TimeMode = Literal["preset", "relative", "custom"]
TimePreset = Literal["ytd", "last_month"]
TimeUnit = Literal["days", "weeks", "months", "years"]

class TimeRange(BaseModel):
    mode: TimeMode = "relative"

    # preset
    preset: Optional[TimePreset] = None

    # relative
    last: Optional[int] = None
    unit: Optional[TimeUnit] = None

    # custom
    start: Optional[str] = None  # YYYY-MM-DD
    end: Optional[str] = None    # YYYY-MM-DD

    @model_validator(mode="after")
    def _check(self):
        if self.mode == "preset":
            if self.preset is None:
                raise ValueError("preset is required when mode='preset'")
        elif self.mode == "relative":
            if self.last is None or self.unit is None:
                raise ValueError("last and unit are required when mode='relative'")
        elif self.mode == "custom":
            if not self.start or not self.end:
                raise ValueError("start and end are required when mode='custom'")
        return self


class QuerySpec(BaseModel):
    is_banking_domain: Optional[bool] = None
    intent: Intent
    time_range: Optional[TimeRange] = Field(default_factory=TimeRange)
    params: Dict[str, Any] = Field(default_factory=dict)
    # examples:
    # top_spending_ytd: {"top_k": 5}
    # transactions_list: {"n_days": 30}
    # unrecognized_transaction: {"transaction_id": "t011"} or {}
    # recurring_payments: {} (or {"min_occurrences": 3})

# =========================
# Chat request context
# =========================

class ConversationContext(BaseModel):
    # UI can pass selected transaction row
    selectedTransactionId: Optional[str] = None


class ChatRequest(BaseModel):
    accountId: str = "A123"
    message: str
    context: Optional[ConversationContext] = None

# =========================
# UI spec
# =========================

class UIMessage(BaseModel):
    type: Literal["text"] = "text"
    content: str


class UITable(BaseModel):
    type: Literal["table"] = "table"
    title: str
    columns: List[str]
    rows: List[List[Any]]


class UIChart(BaseModel):
    type: Literal["chart"] = "chart"
    chartType: Literal["bar", "pie", "line"]
    title: str
    data: List[Dict[str, Any]]  # e.g. [{"category":"Groceries","total":123.45}]


class UIFormField(BaseModel):
    name: str
    label: str
    value: Any = None
    required: bool = True


class UIForm(BaseModel):
    type: Literal["form"] = "form"
    formId: str
    title: str
    fields: List[UIFormField]
    actions: List[Dict[str, Any]]  # e.g. [{"type":"submit","label":"Start dispute"}]


UIComponent = Union[UITable, UIChart, UIForm]

class UISpec(BaseModel):
    messages: list[UIMessage] = Field(default_factory=list)  # type: ignore[assignment]
    components: list[UIComponent] = Field(default_factory=list)  # type: ignore[assignment]


class ChatResponse(BaseModel):
    query: QuerySpec
    ui: UISpec