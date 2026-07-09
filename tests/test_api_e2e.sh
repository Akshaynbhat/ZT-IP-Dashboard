#!/bin/bash

# ZT-IP Dashboard API End-to-End Test Script
# Run from repository root: bash tests/test_api_e2e.sh

set -e

echo "========================================="
echo "Starting End-to-End API Integration Tests"
echo "========================================="

# Base settings
BACKEND_URL="http://localhost:8000"
KEYCLOAK_URL="http://localhost:8080"
REALM="zt-dashboard"

PASSED_COUNT=0
FAILED_COUNT=0
FAILED_LIST=()

# Helper function to inspect test results
verify_test() {
  local test_num="$1"
  local test_name="$2"
  local expected_status="$3"
  local actual_status="$4"
  local response_body="$5"

  echo -n "TEST $test_num: $test_name... "
  if [ "$actual_status" -eq "$expected_status" ]; then
    echo "PASS (Status: $actual_status)"
    PASSED_COUNT=$((PASSED_COUNT + 1))
    return 0
  else
    echo "FAIL (Expected: $expected_status, Actual: $actual_status)"
    echo "  Response Body: $response_body"
    FAILED_COUNT=$((FAILED_COUNT + 1))
    FAILED_LIST+=("TEST $test_num ($test_name) - Expected $expected_status, got $actual_status. Response: $response_body")
    return 1
  fi
}

# Helper function to extract JWT 'sub' claim (User ID)
extract_user_id() {
  local token="$1"
  python3 -c "
import base64, json
token = '$token'
parts = token.split('.')
if len(parts) > 1:
    payload = parts[1]
    payload += '=' * ((4 - len(payload) % 4) % 4)
    data = json.loads(base64.b64decode(payload).decode('utf-8'))
    print(data.get('sub', ''))
else:
    print('')
" 2>/dev/null || echo ""
}

# Step 1 & 2: Obtain authorization tokens
echo "Requesting tokens from Keycloak..."

# Admin Token
ADMIN_RES=$(curl -s -X POST "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=backend-api" \
  -d "client_secret=zt_backend_secret" \
  -d "username=test.admin" \
  -d "password=Admin@123" \
  -d "grant_type=password")

ADMIN_TOKEN=$(echo "$ADMIN_RES" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")

if [ -z "$ADMIN_TOKEN" ]; then
  echo "ERROR: Failed to retrieve Admin Token from Keycloak."
  echo "Response: $ADMIN_RES"
  exit 1
fi

ADMIN_ID=$(extract_user_id "$ADMIN_TOKEN")
echo "Got Admin Token (User ID: $ADMIN_ID)"

# Analyst Token
ANALYST_RES=$(curl -s -X POST "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=backend-api" \
  -d "client_secret=zt_backend_secret" \
  -d "username=test.analyst" \
  -d "password=Analyst@123" \
  -d "grant_type=password")

ANALYST_TOKEN=$(echo "$ANALYST_RES" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
echo "Got Analyst Token"

# Employee Token
EMPLOYEE_RES=$(curl -s -X POST "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=backend-api" \
  -d "client_secret=zt_backend_secret" \
  -d "username=test.employee" \
  -d "password=Employee@123" \
  -d "grant_type=password")

EMPLOYEE_TOKEN=$(echo "$EMPLOYEE_RES" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
EMPLOYEE_ID=$(extract_user_id "$EMPLOYEE_TOKEN")
echo "Got Employee Token (User ID: $EMPLOYEE_ID)"

echo "-----------------------------------------"
echo "Executing test cases..."

# TEST 1: GET /health (no token)
RES_1=$(curl -s -w "%{http_code}" -o /tmp/res1.json "$BACKEND_URL/health")
BODY_1=$(cat /tmp/res1.json 2>/dev/null || echo "")
verify_test "1" "GET /health (Anonymous)" "200" "$RES_1" "$BODY_1"

# TEST 2: GET /api/v1/users (no token)
RES_2=$(curl -s -w "%{http_code}" -o /tmp/res2.json "$BACKEND_URL/api/v1/users")
BODY_2=$(cat /tmp/res2.json 2>/dev/null || echo "")
verify_test "2" "GET /api/v1/users (Anonymous)" "401" "$RES_2" "$BODY_2"

# TEST 3: GET /api/v1/users (ADMIN_TOKEN)
RES_3=$(curl -s -w "%{http_code}" -o /tmp/res3.json "$BACKEND_URL/api/v1/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
BODY_3=$(cat /tmp/res3.json 2>/dev/null || echo "")
verify_test "3" "GET /api/v1/users (Admin)" "200" "$RES_3" "$BODY_3"

# Extract user ID to use for events testing
TEST_USER_ID=$(echo "$BODY_3" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '$EMPLOYEE_ID')" 2>/dev/null || echo "$EMPLOYEE_ID")
if [ -z "$TEST_USER_ID" ]; then
  TEST_USER_ID="f5fbf104-e3f3-470b-85be-587265bf02ab"
fi

# TEST 4: GET /api/v1/users (EMPLOYEE_TOKEN)
RES_4=$(curl -s -w "%{http_code}" -o /tmp/res4.json "$BACKEND_URL/api/v1/users" \
  -H "Authorization: Bearer $EMPLOYEE_TOKEN")
BODY_4=$(cat /tmp/res4.json 2>/dev/null || echo "")
verify_test "4" "GET /api/v1/users (Employee)" "403" "$RES_4" "$BODY_4"

# TEST 5: POST /api/v1/events (ADMIN_TOKEN) - Normal Event
BODY_5_DATA="{\"user_id\":\"$TEST_USER_ID\",\"device_fingerprint\":\"test-device-abc123\",\"event_type\":\"repo_access\",\"resource\":\"core-payments-service\",\"bytes_transferred\":0,\"ip_address\":\"10.0.0.1\",\"location\":\"Bengaluru, IN\"}"
RES_5=$(curl -s -w "%{http_code}" -o /tmp/res5.json -X POST "$BACKEND_URL/api/v1/events" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$BODY_5_DATA")
BODY_5=$(cat /tmp/res5.json 2>/dev/null || echo "")
verify_test "5" "POST /api/v1/events (Normal Event)" "202" "$RES_5" "$BODY_5"

# TEST 6: POST /api/v1/events (ADMIN_TOKEN) - Suspicious Event
BODY_6_DATA="{\"user_id\":\"$TEST_USER_ID\",\"device_fingerprint\":\"unknown-device-xyz999\",\"event_type\":\"file_download\",\"resource\":\"entire_repo.zip\",\"bytes_transferred\":480000000,\"ip_address\":\"185.220.101.5\",\"location\":\"Unknown\"}"
RES_6=$(curl -s -w "%{http_code}" -o /tmp/res6.json -X POST "$BACKEND_URL/api/v1/events" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$BODY_6_DATA")
BODY_6=$(cat /tmp/res6.json 2>/dev/null || echo "")
verify_test "6" "POST /api/v1/events (Suspicious Event)" "202" "$RES_6" "$BODY_6"

# TEST 7: Sleep 70s to wait for background APScheduler scoring task
echo "Waiting 70 seconds for background scoring execution cycle to compute..."
for i in {70..1}; do
  echo -ne "Time remaining: $i seconds...\r"
  sleep 1
done
echo -e "\nDelays finished. Verifying computed scores and alerts..."

# Check trust score computed
RES_7_SCORES=$(curl -s -w "%{http_code}" -o /tmp/res7_scores.json "$BACKEND_URL/api/v1/scores" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
BODY_7_SCORES=$(cat /tmp/res7_scores.json 2>/dev/null || echo "")
verify_test "7a" "GET /api/v1/scores (Check Computed Scores)" "200" "$RES_7_SCORES" "$BODY_7_SCORES"

# Check alerts triggered
RES_7_ALERTS=$(curl -s -w "%{http_code}" -o /tmp/res7_alerts.json "$BACKEND_URL/api/v1/alerts" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
BODY_7_ALERTS=$(cat /tmp/res7_alerts.json 2>/dev/null || echo "")
verify_test "7b" "GET /api/v1/alerts (Check Triggered Alerts)" "200" "$RES_7_ALERTS" "$BODY_7_ALERTS"

# Extract alert ID if exists
ALERT_ID=$(echo "$BODY_7_ALERTS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')" 2>/dev/null || echo "")

# TEST 8: GET /api/v1/scores (ANALYST_TOKEN)
RES_8=$(curl -s -w "%{http_code}" -o /tmp/res8.json "$BACKEND_URL/api/v1/scores" \
  -H "Authorization: Bearer $ANALYST_TOKEN")
BODY_8=$(cat /tmp/res8.json 2>/dev/null || echo "")
verify_test "8" "GET /api/v1/scores (Analyst)" "200" "$RES_8" "$BODY_8"

# TEST 9: GET /api/v1/alerts?status=open (ANALYST_TOKEN)
RES_9=$(curl -s -w "%{http_code}" -o /tmp/res9.json "$BACKEND_URL/api/v1/alerts?status_filter=open" \
  -H "Authorization: Bearer $ANALYST_TOKEN")
BODY_9=$(cat /tmp/res9.json 2>/dev/null || echo "")
verify_test "9" "GET /api/v1/alerts?status_filter=open (Analyst)" "200" "$RES_9" "$BODY_9"

# TEST 10: PATCH /api/v1/alerts/{alert_id} (ANALYST_TOKEN)
if [ ! -z "$ALERT_ID" ]; then
  BODY_10_DATA="{\"status\":\"reviewed\",\"reviewed_by\":\"test.analyst\"}"
  RES_10=$(curl -s -w "%{http_code}" -o /tmp/res10.json -X PATCH "$BACKEND_URL/api/v1/alerts/$ALERT_ID" \
    -H "Authorization: Bearer $ANALYST_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$BODY_10_DATA")
  BODY_10=$(cat /tmp/res10.json 2>/dev/null || echo "")
  verify_test "10" "PATCH /api/v1/alerts/$ALERT_ID (Analyst)" "200" "$RES_10" "$BODY_10"
else
  echo "TEST 10: PATCH /api/v1/alerts (Analyst)... SKIP (No Alert ID available)"
fi

# TEST 11: GET /api/v1/policy-rules (ADMIN_TOKEN)
RES_11=$(curl -s -w "%{http_code}" -o /tmp/res11.json "$BACKEND_URL/api/v1/policy-rules" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
BODY_11=$(cat /tmp/res11.json 2>/dev/null || echo "")
verify_test "11" "GET /api/v1/policy-rules (Admin)" "200" "$RES_11" "$BODY_11"

# TEST 12: GET /api/v1/policy-rules (ANALYST_TOKEN)
RES_12=$(curl -s -w "%{http_code}" -o /tmp/res12.json "$BACKEND_URL/api/v1/policy-rules" \
  -H "Authorization: Bearer $ANALYST_TOKEN")
BODY_12=$(cat /tmp/res12.json 2>/dev/null || echo "")
verify_test "12" "GET /api/v1/policy-rules (Analyst)" "403" "$RES_12" "$BODY_12"

# TEST 13: GET /api/v1/users/{id}/history (EMPLOYEE_TOKEN for own id)
if [ ! -z "$EMPLOYEE_ID" ]; then
  RES_13=$(curl -s -w "%{http_code}" -o /tmp/res13.json "$BACKEND_URL/api/v1/users/$EMPLOYEE_ID/history" \
    -H "Authorization: Bearer $EMPLOYEE_TOKEN")
  BODY_13=$(cat /tmp/res13.json 2>/dev/null || echo "")
  verify_test "13" "GET /api/v1/users/own_id/history (Employee)" "200" "$RES_13" "$BODY_13"
else
  echo "TEST 13: GET /api/v1/users/own_id/history (Employee)... SKIP (No Employee ID)"
fi

# TEST 14: GET /api/v1/users/{admin_id}/history (EMPLOYEE_TOKEN)
if [ ! -z "$ADMIN_ID" ]; then
  RES_14=$(curl -s -w "%{http_code}" -o /tmp/res14.json "$BACKEND_URL/api/v1/users/$ADMIN_ID/history" \
    -H "Authorization: Bearer $EMPLOYEE_TOKEN")
  BODY_14=$(cat /tmp/res14.json 2>/dev/null || echo "")
  verify_test "14" "GET /api/v1/users/admin_id/history (Employee)" "403" "$RES_14" "$BODY_14"
else
  echo "TEST 14: GET /api/v1/users/admin_id/history (Employee)... SKIP (No Admin ID)"
fi

# Cleanup temp files
rm -f /tmp/res*.json

# Output Summary
echo ""
echo "=============================="
echo "        TEST SUMMARY"
echo "=============================="
echo "PASSED: $PASSED_COUNT"
echo "FAILED: $FAILED_COUNT"
echo "------------------------------"
if [ ${#FAILED_LIST[@]} -ne 0 ]; then
  echo "Failed test details:"
  for details in "${FAILED_LIST[@]}"; do
    echo "  - $details"
  done
else
  echo "All integration tests completed successfully!"
fi
echo "=============================="
