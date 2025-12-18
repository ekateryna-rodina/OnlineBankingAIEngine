# OnlineBanking AI Engine - Architecture

Natural language queries → Structured UI responses. FastAPI + OpenAI gpt-4o-mini for intent classification.

## System Architecture

```
┌─────────────┐
│ User Query  │ "What are my 20 most recent transactions?"
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI (app.py)                        │
│                     POST /chat endpoint                      │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│            Orchestrator (orchestrator.py)                    │
│  • Calls query builder                                       │
│  • Fetches transaction data                                  │
│  • Routes to intent handler                                  │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│       Query Builder (query_spec_builder.py)                  │
│  • Sends prompt to LLM                                       │
│  • Parses response → QuerySpec                               │
│  • Post-processing overrides (Fix -2, -1, 0, 1, 2)          │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              LLM (llm.py)                                    │
│  OpenAI API | LocalLLM: gpt-4o-mini                                        │
│  Returns: { intent, params }                     │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│           Intent Handlers (compute.py)                       │
│  • transactions_list                                         │
│  • top_spending_ytd                                          │
│  • recurring_payments                                        │
│  • category_spending_analysis                                │
│  • unrecognized_transaction                                  │
│  • account_balance                                           │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│           Response (schemas.py)                              │
│  ChatResponse {                                              │
│    query: QuerySpec                                          │
│    ui: { messages: [...], components: [...] }                │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

## Component Map

| File | Purpose | Key Exports |
|------|---------|-------------|
| **app.py** | FastAPI app | `/chat`, `/health` endpoints |
| **orchestrator.py** | Request coordinator | `orchestrate_chat()` |
| **query_spec_builder.py** | Intent classification | `compile_queryspec()` + 5 post-processing fixes |
| **llm.py** | LLM wrapper | `chat_completion()` for OpenAI/Ollama |
| **compute.py** | Business logic | 6 intent handler functions |
| **prompts.py** | LLM instructions | 217-line system prompt with intent rules |
| **schemas.py** | Type definitions | `QuerySpec`, `ChatResponse`, `UISpec`, `Intent` |
| **config.py** | Configuration | Environment variables, API keys |
| **tools_api.py** | Mock data source | Transaction data endpoints |

## Architecture Highlights

**✅ Strict Type Validation**
- Pydantic schemas enforce LLM response structure
- Invalid JSON → automatic fallback to safe defaults
- Type-safe `Intent` literal prevents hallucinated intents

**✅ Post-Processing Safety**
- 5 override rules catch LLM edge cases
- Pattern matching after classification (doesn't break existing queries)
- Example: "too much on dining" → Override ensures correct intent even if LLM misclassifies

**✅ Dual LLM Support**
- Single codebase supports OpenAI (production) + Ollama (local dev)
- Switch via `USE_OPENAI` env var
- Cost optimization: $0.0001/query vs free self-hosted

**✅ Separation of Concerns**
- Orchestrator → Query Builder → LLM → Handlers (clean flow)
- Each component has single responsibility
- Easy to test, debug, and extend

**✅ Production-Ready**
- Docker Compose deployment
- Automated testing (35 test cases)
- Health checks and error handling

## Future Improvements

**🎯 Two-Step Intent Classification**
- **Current:** Single 217-line prompt does intent + parameter extraction
- **Improved:** Step 1: Pure intent classification (30 lines) → Step 2: Intent-specific param extraction
- **Benefits:** 2-3x faster, higher accuracy, easier to debug, less token cost

**📈 Scalability & Architecture**
- **Rate limiting:** Prevent abuse (e.g., 10 req/min per user)
- **Caching layer:** Redis for common queries (balance, recent transactions)
- **Async transaction fetching:** Parallel data loading for faster response
- **Response streaming:** Stream LLM output for better perceived performance

**🔒 Security Enhancements**
- **Input sanitization:** Prevent prompt injection attacks
- **API key rotation:** Automated rotation for OpenAI keys
- **Request validation:** Strict schema validation on all inputs
- **Rate limiting:** Per-user and per-IP throttling
- **Audit logging:** Track all queries and intent classifications

**💡 Accuracy & Intelligence**
- **Multi-turn conversations:** Context retention across queries
- **Confidence scores:** LLM confidence metrics to trigger clarification questions
- **A/B testing framework:** Compare prompt variations, measure accuracy improvements
- **Real category spending:** Replace mocked data with actual transaction analysis

**🚀 Additional Features**
- **Budget alerts:** "You're 80% through your dining budget"
- **Savings suggestions:** AI-driven spending optimization tips
- **Anomaly detection:** Flag unusual transactions automatically
- **Natural language responses:** Conversational output instead of just UI components (LLM to produce response query)


======================================================================================================================


SETUP:

How do we run the LLM locally:

1. Open Docker Desktop
2. Pull the image: docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
3. Run the model: docker exec -it ollama ollama run llama3.2
4. Once you run the model - you can smoke test it in your terminal - just talk to it :)

   <img width="682" height="563" alt="complete" src="https://github.com/user-attachments/assets/3b07d28d-bc10-48a3-9920-06e4bf3c131a" />

   Yohooo! You’ve got the model running locally using CPU. 


How do we run our project API:

1. Check if python is installed on your PC: “which python3”
2. Navigate to repo’s root: cd ~/OnlineBanking_Chat
3. Create virtual environment (required to isolate python dependencies for this project on your PC): python3 -m venv .venv
4. Activate virtual environment: source .venv/bin/activate
5. Install dependencies: ‘pip install -r requirements.txt’ or ‘python -m pip install -r requirements.txt’
6. Create .env file in the root of the project with variables:
    * OLLAMA_URL=http://localhost:11434/v1/chat/completions
    * OLLAMA_MODEL=llama3.2:latest
    * TOOL_BASE_URL=http://localhost:8000

1. Run the API: ‘uvicorn src.app:app --reload --port 8000’
2. Test: curl http://localhost:8000/health
3. Call: curl -i -X POST http://localhost:8000/chat \  -H "Content-Type: application/json" \
4.   -d '{"accountId":"A123","message":"What are my top spendings this year?"}'
5.   For debuggin in VS code - here is a launch.json config. Make sure that python interpreter is setup in the Workplace.
   Run Shift + Command + P (mac) -> Python:Interpreter -> <img width="622" height="432" alt="image" src="https://github.com/user-attachments/assets/e9ef23f5-f44e-4113-8262-c2c9d6a0ec6c" />

launch.json file
   
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.app:app",
                "--reload",
                "--port", "8000"
            ],
            "jinja": true,
            "cwd": "${workspaceFolder}",
            "env": {
                "OLLAMA_URL": "http://localhost:11434/v1/chat/completions",
                "OLLAMA_MODEL": "llama3.2:latest",
                "TOOL_BASE_URL": "http://localhost:8000"
            }
        }
    ]
}


TESTING:


1. What user spends money on?

API request
curl -s http://localhost:8000/chat -X POST -H "Content-Type: application/json" \
  -d '{"accountId":"A123","message":"What are my top spendings this year?"}'

__________________

LLM response:
'{\n  "is_banking_domain": true,\n  "clarification_needed": false,\n  "query": {\n    "intent": "top_spending_ytd",\n    "time_range": {\n      "mode": "preset",\n      "preset": "ytd"\n    },\n    "params": {}\n  }\n}'

___________________

API response:
{
  "query": {
    "is_banking_domain": true,
    "intent": "top_spending_ytd",
    "time_range": {
      "mode": "preset",
      "preset": "ytd",
      "last": null,
      "unit": null,
      "start": null,
      "end": null
    },
    "params": {}
  },
  "ui": {
    "messages": [
      {
        "type": "text",
        "content": "Total spending (posted debits): **$19,117.48**"
      }
    ],
    "components": [
      {
        "type": "chart",
        "chartType": "pie",
        "title": "Top 5 categories",
        "data": [
          { "category": "Housing", "total": 15600.0 },
          { "category": "Groceries", "total": 1419.16 },
          { "category": "Shopping", "total": 1138.21 },
          { "category": "Utilities", "total": 473.35 },
          { "category": "Transport", "total": 225.6 }
        ]
      },
      {
        "type": "chart",
        "chartType": "bar",
        "title": "Top 5 merchants",
        "data": [
          { "merchant": "Main Street Apartments", "total": 15600.0 },
          { "merchant": "Whole Foods", "total": 1419.16 },
          { "merchant": "Amazon", "total": 1138.21 },
          { "merchant": "PECO", "total": 313.37 },
          { "merchant": "Uber", "total": 225.6 }
        ]
      }
    ]
  }
}

================================

2. Recent transactions for the time range.

API request
curl -s http://localhost:8000/chat -X POST -H "Content-Type: application/json" \
  -d '{"accountId":"A123","message":"show me transactions for 2 weeks"}'    

__________________

LLM response:
'{\n  "is_banking_domain": true,\n  "clarification_needed": false,\n  "confidence": 0.9,\n  "query": {\n    "intent": "transactions_list",\n    "time_range": {\n      "mode": "relative",\n      "preset": null,\n      "last": 14,\n      "unit": "days"\n    },\n    "params": {}\n  }\n}'

___________________

API response:
{
  "query": {
    "is_banking_domain": true,
    "intent": "transactions_list",
    "time_range": {
      "mode": "relative",
      "preset": null,
      "last": 14,
      "unit": "days",
      "start": null,
      "end": null
    },
    "params": {}
  },
  "ui": {
    "messages": [
      {
        "type": "text",
        "content": "Here are your transactions from **the last 14 days** (showing **8**)."
      }
    ],
    "components": [
      {
        "type": "table",
        "title": "Transactions",
        "columns": [
          "id",
          "date",
          "status",
          "merchant",
          "category",
          "subcategory",
          "amount",
          "direction",
          "payment_rail",
          "card_last4"
        ],
        "rows": [
          [
            "t070",
            "2025-12-14",
            "POSTED",
            "ATM Withdrawal",
            "Cash",
            "ATM",
            "$80.00",
            "debit",
            "ATM",
            ""
          ],
          [
            "t069",
            "2025-12-12",
            "POSTED",
            "Netflix",
            "Subscriptions",
            "Streaming",
            "$15.49",
            "debit",
            "Card",
            "4242"
          ],
          [
            "t068",
            "2025-12-12",
            "POSTED",
            "Payroll",
            "Income",
            "Salary",
            "$3,352.90",
            "credit",
            "ACH",
            ""
          ],
          [
            "t067",
            "2025-12-11",
            "POSTED",
            "Verizon Fios",
            "Utilities",
            "Internet",
            "$79.99",
            "debit",
            "ACH",
            ""
          ],
          [
            "t066",
            "2025-12-10",
            "PENDING",
            "MALVERN BUTTERY",
            "Food",
            "Bakery",
            "$18.75",
            "debit",
            "Card",
            "4242"
          ],
          [
            "t065",
            "2025-12-10",
            "POSTED",
            "Spotify",
            "Subscriptions",
            "Music",
            "$11.99",
            "debit",
            "Card",
            "4242"
          ],
          [
            "t064",
            "2025-12-04",
            "POSTED",
            "Uber",
            "Transport",
            "Rideshare",
            "$19.60",
            "debit",
            "Card",
            "4242"
          ],
          [
            "t063",
            "2025-12-03",
            "POSTED",
            "Whole Foods",
            "Groceries",
            "Supermarket",
            "$111.09",
            "debit",
            "Card",
            "4242"
          ]
        ]
      }
    ]
  }
}

==================================

3. Recent transactions by count

API request
curl -s http://localhost:8000/chat -X POST -H "Content-Type: application/json" \
  -d '{"accountId":"A123","message":"show me 10 most recent transactions"}'    

__________________

LLM response:
'{\n  "is_banking_domain": true,\n  "clarification_needed": false,\n  "clarification_question": null,\n  "confidence": 0.0,\n  "query": {\n    "intent": "transactions_list",\n    "time_range": {\n      "mode": "relative",\n      "preset": null,\n      "last": 30,\n      "unit": "days",\n      "start": null,\n      "end": null\n    },\n    "params": {\n      "limit": 10\n    }\n  }\n}'


API response
{
  "query": {
    "is_banking_domain": true,
    "intent": "transactions_list",
    "time_range": {
      "mode": "relative",
      "preset": null,
      "last": 30,
      "unit": "days",
      "start": null,
      "end": null
    },
    "params": {
      "limit": 10
    }
  },
  "ui": {
    "messages": [
      {
        "type": "text",
        "content": "Here are your transactions from **the last 30 days** (showing **10**)."
      }
    ],
    "components": [
      {
        "type": "table",
        "title": "Transactions",
        "columns": [
          "id",
          "date",
          "status",
          "merchant",
          "category",
          "subcategory",
          "amount",
          "direction",
          "payment_rail",
          "card_last4"
        ],
        "rows": [
          [
            "t070",
            "2025-12-14",
            "POSTED",
            "ATM Withdrawal",
            "Cash",
            "ATM",
            "$80.00",
            "debit",
            "ATM",
            ""
          ],
          [
            "t069",
            "2025-12-12",
            "POSTED",
            "Netflix",
            "Subscriptions",
            "Streaming",
            "$15.49",
            "debit",
            "Card",
            "4242"
          ],
          [
            "t068",
            "2025-12-12",
            "POSTED",
            "Payroll",
            "Income",
            "Salary",
            "$3,352.90",
            "credit",
            "ACH",
            ""
          ],
          [
            "t067",
            "2025-12-11",
            "POSTED",
            "Verizon Fios",
            "Utilities",
            "Internet",
            "$79.99",
            "debit",
            "ACH",
            ""
          ],
          [
            "t066",
            "2025-12-10",
            "PENDING",
            "MALVERN BUTTERY",
            "Food",
            "Bakery",
            "$18.75",
            "debit",
            "Card",
            "4242"
          ],
          [
            "t065",
            "2025-12-10",
            "POSTED",
            "Spotify",
            "Subscriptions",
            "Music",
            "$11.99",
            "debit",
            "Card",
            "4242"
          ],
          [
            "t064",
            "2025-12-04",
            "POSTED",
            "Uber",
            "Transport",
            "Rideshare",
            "$19.60",
            "debit",
            "Card",
            "4242"
          ],
          [
            "t063",
            "2025-12-03",
            "POSTED",
            "Whole Foods",
            "Groceries",
            "Supermarket",
            "$111.09",
            "debit",
            "Card",
            "4242"
          ],
          [
            "t062",
            "2025-12-01",
            "POSTED",
            "Main Street Apartments",
            "Housing",
            "Rent",
            "$1,950.00",
            "debit",
            "ACH",
            ""
          ],
          [
            "t061",
            "2025-11-28",
            "POSTED",
            "Payroll",
            "Income",
            "Salary",
            "$3,315.30",
            "credit",
            "ACH",
            ""
          ]
        ]
      }
    ]
  }
}

=================================

4. User does not recognize the transaction

API request
curl -s http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "accountId": "A123",
    "message": "I don’t recognize this transaction",
    "context": { "selectedTransactionId": "t016" }
  }'
_________________________________

LLM response
'{\n  "is_banking_domain": true,\n  "clarification_needed": false,\n  "clarification_question": null,\n  "confidence": 0.0,\n  "query": {\n    "intent": "unrecognized_transaction",\n    "time_range": {\n      "mode": null,\n      "preset": null,\n      "last": null,\n      "unit": null,\n      "start": null,\n      "end": null\n    },\n    "params": {\n      "transaction_id": null\n    }\n  }\n}'

___________________________________

{
  "query": {
    "is_banking_domain": true,
    "intent": "unrecognized_transaction",
    "time_range": null,
    "params": {
      "transaction_id": "t016"
    }
  },
  "ui": {
    "messages": [
      {
        "type": "text",
        "content": "I found this transaction:\n\n**Uber** (Transport / Rideshare)\n- **Amount:** $18.60 (debit)\n- **Date:** 2025-07-27\n- **Status:** POSTED\n- **Method:** Card (•••• 4242)\n\nIf you don’t recognize it, you can start a dispute below (a team member will review)."
      }
    ],
    "components": [
      {
        "type": "card",
        "title": "Transaction details",
        "items": [
          { "label": "Transaction ID", "value": "t016" },
          { "label": "Merchant", "value": "Uber (Transport / Rideshare)" },
          { "label": "Amount", "value": "$18.60", "badge": "Debit" },
          { "label": "Date", "value": "2025-07-27" },
          { "label": "Status", "value": "POSTED" },
          { "label": "Payment method", "value": "Card •••• 4242" }
        ]
      },
      {
        "type": "form",
        "formId": "dispute_transaction_v1",
        "title": "Report an unrecognized transaction",
        "description": "Tell us what looks wrong. We’ll review and follow up.",
        "fields": [
          {
            "name": "transactionId",
            "label": "Transaction ID",
            "type": "text",
            "value": "t016",
            "required": true,
            "readOnly": true
          },
          {
            "name": "merchant",
            "label": "Merchant",
            "type": "text",
            "value": "Uber",
            "required": true,
            "readOnly": true
          },
          {
            "name": "date",
            "label": "Date",
            "type": "date",
            "value": "2025-07-27",
            "required": true,
            "readOnly": true
          },
          {
            "name": "amount",
            "label": "Amount",
            "type": "money",
            "currency": "USD",
            "value": "18.60",
            "displayValue": "$18.60",
            "required": true,
            "readOnly": true
          },
          {
            "name": "reason",
            "label": "What’s wrong?",
            "type": "select",
            "placeholder": "Choose one",
            "options": [
              { "label": "Not mine", "value": "not_mine" },
              { "label": "Duplicate charge", "value": "duplicate" },
              { "label": "Wrong amount", "value": "wrong_amount" }
            ],
            "required": true
          },
          {
            "name": "notes",
            "label": "Notes (optional)",
            "type": "textarea",
            "placeholder": "Anything else you want us to know?",
            "value": "",
            "required": false
          }
        ],
        "actions": [
          {
            "type": "submit",
            "label": "Start dispute",
            "style": "primary"
          }
        ]
      }
    ]
  }
}


=================================

5. User's subscriptiptions
Recent transactions by count

API request
curl -s http://localhost:8000/chat -X POST -H "Content-Type: application/json" \
  -d '{"accountId":"A123","message":"what are my subscriptions?"}'    

__________________

LLM response:
'{\n  "is_banking_domain": true,\n  "clarification_needed": false,\n  "clarification_question": null,\n  "confidence": 0.0,\n  "query": {\n    "intent": "recurring_payments",\n    "time_range": {\n      "mode": "relative",\n      "preset": null,\n      "last": null,\n      "unit": null,\n      "start": null,\n      "end": null\n    },\n    "params": {}\n  }\n}'

API response:
{
  "query": {
    "is_banking_domain": true,
    "intent": "recurring_payments",
    "time_range": {
      "mode": "relative",
      "preset": null,
      "last": 180,
      "unit": "days",
      "start": null,
      "end": null
    },
    "params": {}
  },
  "ui": {
    "messages": [
      {
        "type": "text",
        "content": "Found **4** likely recurring payments (posted debits only)."
      }
    ],
    "components": [
      {
        "type": "table",
        "title": "Recurring payments / subscriptions",
        "columns": [
          "merchant",
          "cadence",
          "avg_amount",
          "occurrences",
          "last_seen"
        ],
        "rows": [
          [
            "Main Street Apartments",
            "monthly",
            "$1,950.00",
            "6",
            "2025-12-01"
          ],
          [
            "Netflix",
            "monthly",
            "$15.49",
            "4",
            "2025-12-12"
          ],
          [
            "Spotify",
            "monthly",
            "$11.99",
            "4",
            "2025-12-10"
          ],
          [
            "PECO",
            "monthly",
            "$104.46",
            "3",
            "2025-10-28"
          ]
        ]
      }
    ]
  }
}


