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
curl -s http://localhost:8000/chat -X POST -H "Content-Type: application/json" \
  -d '{"accountId":"A123","message":"what is this transaction t007?"}'
_________________________________

LLM response
'{\n  "is_banking_domain": false,\n  "clarification_needed": true,\n  "clarification_question": "What type transaction t007",\n  "confidence": 0.0,\n  "query": {\n    "intent": "transactions_list",\n    "time_range": null,\n    "params": {\n      "limit": 10\n    }\n  }\n}'

___________________________________

bug - does not recognize intent correctly - better prompt engineering

=================================

5. User's subscriptiptions
Recent transactions by count

API request
curl -s http://localhost:8000/chat -X POST -H "Content-Type: application/json" \
  -d '{"accountId":"A123","message":"what are my subscriptions?"}'    

__________________

LLM response:
--fix - it messed up intent - undecognized_subscriptiopn (?) instead of recurring_payments - and still working!
{\n  "is_banking_domain": false,\n  "clarification_needed": true,\n  "clarification_question": "What type of subscription are you referring to?",\n  "confidence": 0.0,\n  "query": {\n    "intent": "unrecognized_subscription",\n    "time_range": {\n      "mode": "relative",\n      "unit": null\n    },\n    "params": {}\n  }\n}

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


