#!/usr/bin/env bash
set -e

PORT=${PORT:-3001}
BASE_URL="http://localhost:${PORT}"

echo "=========================================================="
echo " Running Live Curl API Tests for Observability Auth API   "
echo " Target URL: ${BASE_URL}                                   "
echo "=========================================================="

echo -e "\n--- 1. POST /api/v1/auth/sign-up ---"
SIGNUP_EMAIL="script_user_$(date +%s)@observability.io"
SIGNUP_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/auth/sign-up" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${SIGNUP_EMAIL}\",
    \"password\": \"StrongPassword123!\",
    \"name\": \"Script Test User\",
    \"organization_name\": \"Script Org $(date +%s)\",
    \"role\": \"admin\"
  }")
echo "${SIGNUP_RESP}"

echo -e "\n--- 2. POST /api/v1/auth/sign-in ---"
SIGNIN_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/auth/sign-in" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${SIGNUP_EMAIL}\",
    \"password\": \"StrongPassword123!\"
  }")
echo "${SIGNIN_RESP}"

TOKEN=$(echo "${SIGNIN_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.token || '');")

if [ -z "$TOKEN" ]; then
  echo "Error: Failed to obtain JWT token from sign-in response"
  exit 1
fi

echo -e "\n--- 3. GET /api/v1/auth/session ---"
curl -s -X GET "${BASE_URL}/api/v1/auth/session" \
  -H "Authorization: Bearer ${TOKEN}"

echo -e "\n\n--- 4. POST /api/v1/auth/forgot-password ---"
FORGOT_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${SIGNUP_EMAIL}\"
  }")
echo "${FORGOT_RESP}"

RESET_TOKEN=$(echo "${FORGOT_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.resetToken || '');")

echo -e "\n\n--- 5. POST /api/v1/auth/reset-password ---"
curl -s -X POST "${BASE_URL}/api/v1/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"${RESET_TOKEN}\",
    \"new_password\": \"NewPassword123!\"
  }"

echo -e "\n\n--- 6. POST /api/v1/auth/change-password ---"
curl -s -X POST "${BASE_URL}/api/v1/auth/change-password" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "NewPassword123!",
    "new_password": "FinalStrongPassword123!"
  }'

ORG_ID=$(echo "${SIGNUP_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.user?.org_id || '');")

echo -e "\n\n--- 7. POST /api/v1/auth/api-keys ---"
KEY_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/auth/api-keys" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Script Generated Key\",
    \"org_id\": \"${ORG_ID}\",
    \"key_type\": \"general\",
    \"permissions\": [\"traces:read\", \"metrics:read\"]
  }")
echo "${KEY_RESP}"

RAW_KEY=$(echo "${KEY_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.rawKey || '');")

echo -e "\n\n--- 8. POST /api/v1/auth/api-keys/verify ---"
curl -s -X POST "${BASE_URL}/api/v1/auth/api-keys/verify" \
  -H "Content-Type: application/json" \
  -d "{
    \"key\": \"${RAW_KEY}\",
    \"required_permission\": \"traces:read\"
  }"

echo -e "\n\n--- 9. GET /api/v1/auth/permissions ---"
curl -s -X GET "${BASE_URL}/api/v1/auth/permissions"

echo -e "\n\n--- 10. GET /api/v1/auth/audit-logs ---"
curl -s -X GET "${BASE_URL}/api/v1/auth/audit-logs" \
  -H "Authorization: Bearer ${TOKEN}"

echo -e "\n\n=========================================================="
echo " All 10 Curl API Endpoints Executed Successfully!         "
echo "=========================================================="
