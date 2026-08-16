#!/usr/bin/env bash
set -e

PORT=${PORT:-3001}
BASE_URL="http://localhost:${PORT}"

echo "=========================================================="
echo " Running Live Curl API Tests for Observability Auth API   "
echo " Target URL: ${BASE_URL}                                   "
echo "=========================================================="

echo -e "\n--- 1. POST /api/v1/auth/sign-up (Register Admin & Org) ---"
ADMIN_EMAIL="admin_$(date +%s)@observability.io"
ORG_NAME="Org Primary $(date +%s)"
SIGNUP_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/auth/sign-up" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${ADMIN_EMAIL}\",
    \"password\": \"StrongPassword123!\",
    \"name\": \"Primary Admin\",
    \"organization_name\": \"${ORG_NAME}\"
  }")
echo "${SIGNUP_RESP}"

TOKEN=$(echo "${SIGNUP_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.token || '');")
PRIMARY_ORG_ID=$(echo "${SIGNUP_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.user?.org_id || '');")
ADMIN_USER_ID=$(echo "${SIGNUP_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.user?.id || '');")

echo -e "\n--- 2. GET /api/v1/auth/users/me (Get Profile) ---"
curl -s -X GET "${BASE_URL}/api/v1/auth/users/me" \
  -H "Authorization: Bearer ${TOKEN}"

echo -e "\n\n--- 3. PATCH /api/v1/auth/users/me (Update Profile) ---"
curl -s -X PATCH "${BASE_URL}/api/v1/auth/users/me" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Admin Name"}'

echo -e "\n\n--- 4. POST /api/v1/auth/organizations (Create Secondary Org) ---"
SEC_ORG_NAME="Org Secondary $(date +%s)"
CREATE_SEC_ORG_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/auth/organizations" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"${SEC_ORG_NAME}\"}")
echo "${CREATE_SEC_ORG_RESP}"

SEC_ORG_ID=$(echo "${CREATE_SEC_ORG_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.id || '');")

echo -e "\n--- 5. GET /api/v1/auth/organizations (List User Organizations) ---"
curl -s -X GET "${BASE_URL}/api/v1/auth/organizations" \
  -H "Authorization: Bearer ${TOKEN}"

echo -e "\n\n--- 6. POST /api/v1/auth/organizations/${SEC_ORG_ID}/switch (Switch Org Context) ---"
SWITCH_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/auth/organizations/${SEC_ORG_ID}/switch" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json")
echo "${SWITCH_RESP}"

SWITCHED_TOKEN=$(echo "${SWITCH_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.token || '');")

echo -e "\n--- 7. POST /api/v1/auth/users/invite (Invite Member) ---"
INVITE_EMAIL="member_$(date +%s)@observability.io"
INVITE_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/auth/users/invite" \
  -H "Authorization: Bearer ${SWITCHED_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${INVITE_EMAIL}\",
    \"name\": \"Invited Member\",
    \"role\": \"member\",
    \"permissions\": [\"traces:read\"]
  }")
echo "${INVITE_RESP}"

MEMBER_USER_ID=$(echo "${INVITE_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.id || '');")

echo -e "\n--- 8. GET /api/v1/auth/users (List Org Members) ---"
curl -s -X GET "${BASE_URL}/api/v1/auth/users" \
  -H "Authorization: Bearer ${SWITCHED_TOKEN}"

echo -e "\n\n--- 9. PATCH /api/v1/auth/users/${MEMBER_USER_ID}/role (Update Member Role) ---"
curl -s -X PATCH "${BASE_URL}/api/v1/auth/users/${MEMBER_USER_ID}/role" \
  -H "Authorization: Bearer ${SWITCHED_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'

echo -e "\n\n--- 10. POST /api/v1/auth/api-keys (Generate API Key) ---"
KEY_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/auth/api-keys" \
  -H "Authorization: Bearer ${SWITCHED_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Telemetry Key\",
    \"org_id\": \"${SEC_ORG_ID}\",
    \"key_type\": \"general\",
    \"permissions\": [\"traces:read\"]
  }")
echo "${KEY_RESP}"

RAW_KEY=$(echo "${KEY_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.rawKey || '');")
KEY_ID=$(echo "${KEY_RESP}" | node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(0, 'utf-8')); console.log(d.data?.keyRecord?.key_id || '');")

echo -e "\n\n--- 11. POST /api/v1/auth/api-keys/verify (Verify Key) ---"
curl -s -X POST "${BASE_URL}/api/v1/auth/api-keys/verify" \
  -H "Content-Type: application/json" \
  -d "{
    \"key\": \"${RAW_KEY}\",
    \"required_permission\": \"traces:read\"
  }"

echo -e "\n\n--- 12. GET /api/v1/auth/api-keys (List API Keys) ---"
curl -s -X GET "${BASE_URL}/api/v1/auth/api-keys" \
  -H "Authorization: Bearer ${SWITCHED_TOKEN}"

echo -e "\n\n--- 13. POST /api/v1/auth/api-keys/${KEY_ID}/revoke (Revoke Key) ---"
curl -s -X POST "${BASE_URL}/api/v1/auth/api-keys/${KEY_ID}/revoke" \
  -H "Authorization: Bearer ${SWITCHED_TOKEN}"

echo -e "\n\n--- 14. GET /api/v1/auth/audit-logs (Filtered Audit Logs) ---"
curl -s -X GET "${BASE_URL}/api/v1/auth/audit-logs?event_type=ORG_SWITCH" \
  -H "Authorization: Bearer ${SWITCHED_TOKEN}"

echo -e "\n\n--- 15. POST /api/v1/auth/sign-out (Sign Out & Invalidate Token) ---"
curl -s -X POST "${BASE_URL}/api/v1/auth/sign-out" \
  -H "Authorization: Bearer ${SWITCHED_TOKEN}"

echo -e "\n\n=========================================================="
echo " All API Endpoints Executed Successfully!                 "
echo "=========================================================="
