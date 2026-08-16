#!/usr/bin/env bash
set -e

PORT=${PORT:-3001}
BASE_URL="http://localhost:${PORT}"

echo "=========================================================="
echo " Running Live Curl API Tests for Observability Auth API   "
echo " Target URL: ${BASE_URL}                                   "
echo "=========================================================="

echo -e "\n--- 1. POST /api/v1/auth/organizations (Create Standalone Organization) ---"
ORG_NAME="Org Standalone $(date +%s)"
CREATE_ORG_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/auth/organizations" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${ORG_NAME}\"
  }")
echo "${CREATE_ORG_RESP}"

ORG_ID=$(echo "${CREATE_ORG_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.id || '');")

echo -e "\n--- 2. POST /api/v1/auth/users (Create User in Target Organization with Specific Permissions) ---"
USER_EMAIL="orguser_$(date +%s)@observability.io"
CREATE_USER_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/auth/users" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${USER_EMAIL}\",
    \"password\": \"StrongPassword123!\",
    \"name\": \"Target Org User\",
    \"org_id\": \"${ORG_ID}\",
    \"role\": \"member\",
    \"permissions\": [\"traces:read\", \"metrics:read\"]
  }")
echo "${CREATE_USER_RESP}"

CREATED_USER_ID=$(echo "${CREATE_USER_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.id || '');")

echo -e "\n--- 3. POST /api/v1/auth/sign-in ---"
SIGNIN_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/auth/sign-in" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${USER_EMAIL}\",
    \"password\": \"StrongPassword123!\"
  }")
echo "${SIGNIN_RESP}"

TOKEN=$(echo "${SIGNIN_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.token || '');")

echo -e "\n--- 4. GET /api/v1/auth/session ---"
curl -s -X GET "${BASE_URL}/api/v1/auth/session" \
  -H "Authorization: Bearer ${TOKEN}"

echo -e "\n\n--- 5. POST /api/v1/auth/api-keys ---"
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

echo -e "\n\n--- 6. POST /api/v1/auth/api-keys/verify ---"
curl -s -X POST "${BASE_URL}/api/v1/auth/api-keys/verify" \
  -H "Content-Type: application/json" \
  -d "{
    \"key\": \"${RAW_KEY}\",
    \"required_permission\": \"traces:read\"
  }"

echo -e "\n\n--- 7. GET /api/v1/auth/permissions ---"
curl -s -X GET "${BASE_URL}/api/v1/auth/permissions"

echo -e "\n\n--- 8. GET /api/v1/auth/audit-logs ---"
curl -s -X GET "${BASE_URL}/api/v1/auth/audit-logs" \
  -H "Authorization: Bearer ${TOKEN}"

echo -e "\n\n--- 9. POST /api/v1/auth/users/${CREATED_USER_ID}/block (Block User Access) ---"
curl -s -X POST "${BASE_URL}/api/v1/auth/users/${CREATED_USER_ID}/block" \
  -H "Authorization: Bearer ${TOKEN}"

echo -e "\n\n--- 10. DELETE /api/v1/auth/users/${CREATED_USER_ID} (Soft Delete User with 30-Day Backup Retention) ---"
curl -s -X DELETE "${BASE_URL}/api/v1/auth/users/${CREATED_USER_ID}" \
  -H "Authorization: Bearer ${TOKEN}"

echo -e "\n\n--- 11. DELETE /api/v1/auth/organizations/${ORG_ID} (Soft Delete Org with Cascading Soft Delete) ---"
curl -s -X DELETE "${BASE_URL}/api/v1/auth/organizations/${ORG_ID}" \
  -H "Authorization: Bearer ${TOKEN}"

echo -e "\n\n=========================================================="
echo " All API Endpoints Executed Successfully!                 "
echo "=========================================================="
