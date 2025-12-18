#!/bin/bash

# Test script for OnlineBanking Chat API with validation
# Usage: ./run_tests_v2.sh [base_url]
# Default: http://localhost:8000

BASE_URL="${1:-http://localhost:8000}"
ENDPOINT="${BASE_URL}/chat"

PASS_COUNT=0
FAIL_COUNT=0

echo "============================================"
echo "OnlineBanking Chat API Test Suite"
echo "Testing endpoint: $ENDPOINT"
echo "============================================"
echo ""

# Test with validation
test_query() {
    local test_name="$1"
    local message="$2"
    local expected_intent="$3"
    local expected_pattern="$4"
    
    echo "TEST: $test_name"
    echo "Query: \"$message\""
    
    response=$(curl -s -X POST "$ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "{\"accountId\":\"A123\",\"message\":\"$message\"}")
    
    if [ -z "$response" ]; then
        echo "❌ FAILED - No response"
        echo ""
        ((FAIL_COUNT++))
        return 1
    fi
    
    # Parse response
    result=$(echo "$response" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    tr = d['query'].get('time_range')
    intent = d['query']['intent']
    msg = d['ui']['messages'][0]['content']
    charts = len([c for c in d['ui'].get('components', []) if c.get('type')=='chart'])
    
    print('Intent:', intent)
    print('Time:', (tr.get('preset') if tr else None) or (tr.get('mode') if tr else None) or 'None')
    print('Message:', msg[:100])
    print('Charts:', charts)
    print('VALIDATE|' + intent + '|' + msg)
except Exception as e:
    print('ERROR:', str(e))
    sys.exit(1)
" 2>&1)
    
    if [ $? -ne 0 ]; then
        echo "❌ FAILED - Parse error: $result"
        echo ""
        ((FAIL_COUNT++))
        return 1
    fi
    
    echo "$result" | grep -v "^VALIDATE"
    
    # Extract validation data
    validate_line=$(echo "$result" | grep "^VALIDATE")
    actual_intent=$(echo "$validate_line" | cut -d'|' -f2)
    actual_msg=$(echo "$validate_line" | cut -d'|' -f3-)
    
    # Validate intent
    if [ -n "$expected_intent" ] && [ "$actual_intent" != "$expected_intent" ]; then
        echo "❌ FAILED - Expected intent: '$expected_intent', got: '$actual_intent'"
        echo ""
        ((FAIL_COUNT++))
        return 1
    fi
    
    # Validate message pattern
    if [ -n "$expected_pattern" ]; then
        if ! echo "$actual_msg" | grep -qi "$expected_pattern"; then
            echo "❌ FAILED - Expected pattern '$expected_pattern' not found in message"
            echo ""
            ((FAIL_COUNT++))
            return 1
        fi
    fi
    
    echo "✅ PASSED"
    echo ""
    ((PASS_COUNT++))
}

# 1. COUNT-BASED QUERIES
echo "=========================================="
echo "1. COUNT-BASED QUERIES"
echo "=========================================="
test_query "Last 5 transactions" "show me my last 5 transactions" "transactions_list" "\*\*5 most recent"
test_query "Last 10 transactions" "last 10 transactions" "transactions_list" "\*\*10 most recent"
test_query "Most recent 3" "3 most recent transactions" "transactions_list" ""

# 2. TIME-BASED QUERIES
echo "=========================================="
echo "2. TIME-BASED QUERIES"
echo "=========================================="
test_query "This month" "transactions this month" "transactions_list" "\*\*this month\*\*"
test_query "Last month" "transactions last month" "transactions_list" "\*\*last month\*\*"
test_query "Last week" "show me last week transactions" "transactions_list" ""
test_query "Year to date" "transactions year to date" "top_spending_ytd" "Total spending"
test_query "Last 30 days" "transactions from last 30 days" "transactions_list" "\*\*last 30 days\*\*"

# 3. TOP SPENDING QUERIES
echo "=========================================="
echo "3. TOP SPENDING QUERIES"
echo "=========================================="
test_query "Top spendings" "what are my top spendings?" "top_spending_ytd" "Total spending"
test_query "Where money goes" "where does my money go?" "top_spending_ytd" "Total spending"
test_query "Spending categories" "show me my spending categories" "top_spending_ytd" ""
test_query "What I spend most on" "what do I spend the most on?" "top_spending_ytd" "Total spending"
test_query "Biggest spending" "what's my biggest spending?" "top_spending_ytd" "Total spending"

# 4. SUBSCRIPTION QUERIES
echo "=========================================="
echo "4. SUBSCRIPTION QUERIES"
echo "=========================================="
test_query "Subscriptions" "what are my subscriptions?" "recurring_payments" "recurring payments"
test_query "Recurring payments" "show me my recurring payments" "recurring_payments" "recurring payments"
test_query "Monthly charges" "monthly charges" "recurring_payments" "recurring payments"
test_query "What am I paying monthly" "what am I paying for every month?" "recurring_payments" ""

# 5. UNRECOGNIZED TRANSACTION
echo "=========================================="
echo "5. UNRECOGNIZED TRANSACTION"
echo "=========================================="
echo "TEST: Unrecognized transaction (two-step process)"
echo "Step 1: Get transaction list"
txn_response=$(curl -s -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{"accountId":"A123","message":"show me my last 3 transactions"}')

echo "$txn_response" | python3 -c "import sys, json; d=json.load(sys.stdin); print('Transactions retrieved:', len(d['ui']['components'][0]['rows']) if d['ui'].get('components') else 0)"

echo ""
echo "Step 2: Query unrecognized transaction with context"
unrecognized_response=$(curl -s -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{"accountId":"A123","message":"what is this?","context":{"selectedTransactionId":"t001"}}')

if echo "$unrecognized_response" | python3 -c "import sys, json; d=json.load(sys.stdin); print('Intent:', d['query']['intent']); print('Message:', d['ui']['messages'][0]['content'][:100])" 2>&1; then
    echo "✅ PASSED - Unrecognized transaction handling"
    ((PASS_COUNT++))
else
    echo "❌ FAILED - Unrecognized transaction"
    ((FAIL_COUNT++))
fi
echo ""

# 6. EDGE CASES
echo "=========================================="
echo "6. EDGE CASES & VARIATIONS"
echo "=========================================="
test_query "This year" "show me transactions this year" "transactions_list" "year-to-date"
test_query "YTD" "transactions ytd" "top_spending_ytd" "Total spending"
test_query "Last 7 days" "last 7 days" "transactions_list" ""
test_query "Recent transactions" "recent transactions" "transactions_list" ""

echo "============================================"
echo "Test Suite Complete"
echo "============================================"
echo ""
echo "Results: ✅ $PASS_COUNT passed, ❌ $FAIL_COUNT failed"
echo ""
