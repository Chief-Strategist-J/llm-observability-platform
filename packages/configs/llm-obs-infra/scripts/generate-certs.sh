#!/usr/bin/env bash
#
# generate-certs.sh — Self-Signed TLS Certificate Generator
#
# Generates a Root CA + Server certificate with SAN entries for all
# llmobs.* custom gateway domains. Idempotent — skips if valid certs exist.
#
# Usage:
#   ./scripts/generate-certs.sh           (skip if valid certs exist)
#   ./scripts/generate-certs.sh --force   (regenerate even if valid)
#

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"
CERT_DIR="$PKG_DIR/config/certs"

CA_KEY="$CERT_DIR/ca-key.pem"
CA_CERT="$CERT_DIR/ca.pem"
SERVER_KEY="$CERT_DIR/server-key.pem"
SERVER_CSR="$CERT_DIR/server.csr"
SERVER_CERT="$CERT_DIR/server.pem"
OPENSSL_CNF="$CERT_DIR/openssl-san.cnf"

CERT_VALIDITY_DAYS=825
CA_SUBJECT="/C=IN/ST=Gujarat/L=Ahmedabad/O=LLMObs/OU=Platform/CN=LLMObs Root CA"
SERVER_SUBJECT="/C=IN/ST=Gujarat/L=Ahmedabad/O=LLMObs/OU=Frontend/CN=llmobs.gateway"

SAN_DOMAINS=(
  "llmobs.gateway"
  "llmobs.grafana"
  "llmobs.tempo"
  "llmobs.otel"
  "llmobs.kafka"
  "llmobs.redis"
  "gateway.llmobs.local"
  "grafana.llmobs.local"
  "tempo.llmobs.local"
  "otel.llmobs.local"
  "localhost"
)

SAN_IPS=(
  "127.0.0.1"
  "::1"
)

check_existing_certs() {
  if [ -f "$CA_CERT" ] && [ -f "$SERVER_CERT" ] && [ -f "$SERVER_KEY" ]; then
    if openssl x509 -checkend 2592000 -noout -in "$SERVER_CERT" 2>/dev/null; then
      echo -e "${GREEN}✓ Valid TLS certificates already exist in ${CERT_DIR}${NC}"
      echo -e "  CA Certificate:     ${CA_CERT}"
      echo -e "  Server Certificate: ${SERVER_CERT}"
      echo -e "  Server Key:         ${SERVER_KEY}"
      return 0
    else
      echo -e "${YELLOW}⚠ Existing certificates are expiring soon or invalid. Regenerating...${NC}"
      return 1
    fi
  fi
  return 1
}

generate_openssl_config() {
  cat > "$OPENSSL_CNF" <<EOF
[req]
default_bits       = 4096
distinguished_name = req_distinguished_name
req_extensions     = v3_req
prompt             = no

[req_distinguished_name]
C  = IN
ST = Gujarat
L  = Ahmedabad
O  = LLMObs
OU = Frontend
CN = llmobs.gateway

[v3_req]
basicConstraints     = CA:FALSE
keyUsage             = digitalSignature, keyEncipherment
extendedKeyUsage     = serverAuth, clientAuth
subjectAltName       = @alt_names

[v3_ca]
basicConstraints     = critical, CA:TRUE, pathlen:0
keyUsage             = critical, keyCertSign, cRLSign
subjectKeyIdentifier = hash

[alt_names]
EOF

  local idx=1
  for domain in "${SAN_DOMAINS[@]}"; do
    echo "DNS.${idx} = ${domain}" >> "$OPENSSL_CNF"
    idx=$((idx + 1))
  done

  idx=1
  for ip in "${SAN_IPS[@]}"; do
    echo "IP.${idx} = ${ip}" >> "$OPENSSL_CNF"
    idx=$((idx + 1))
  done
}

main() {
  echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"
  echo -e "${BOLD} TLS CERTIFICATE GENERATOR — LLMObs Platform${NC}"
  echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"

  if ! command -v openssl &>/dev/null; then
    echo -e "${RED}✖ Error: openssl is required but not installed.${NC}"
    echo -e "  Install: ${BOLD}sudo apt install openssl${NC}"
    exit 1
  fi

  if [ "${1:-}" != "--force" ] && check_existing_certs; then
    return 0
  fi

  mkdir -p "$CERT_DIR"

  echo -e "\n${YELLOW}1. Generating OpenSSL SAN configuration...${NC}"
  generate_openssl_config
  echo -e "   Config: ${OPENSSL_CNF}"

  echo -e "\n${YELLOW}2. Generating Root CA private key (4096-bit RSA)...${NC}"
  openssl genrsa -out "$CA_KEY" 4096 2>/dev/null
  chmod 600 "$CA_KEY"
  echo -e "   Key: ${CA_KEY}"

  echo -e "\n${YELLOW}3. Generating Root CA certificate (${CERT_VALIDITY_DAYS} days)...${NC}"
  openssl req -new -x509 -sha256 \
    -key "$CA_KEY" \
    -out "$CA_CERT" \
    -days "$CERT_VALIDITY_DAYS" \
    -subj "$CA_SUBJECT" \
    -extensions v3_ca \
    -config "$OPENSSL_CNF"
  echo -e "   Cert: ${CA_CERT}"

  echo -e "\n${YELLOW}4. Generating server private key (4096-bit RSA)...${NC}"
  openssl genrsa -out "$SERVER_KEY" 4096 2>/dev/null
  chmod 644 "$SERVER_KEY"
  echo -e "   Key: ${SERVER_KEY}"

  echo -e "\n${YELLOW}5. Generating server certificate signing request (CSR)...${NC}"
  openssl req -new -sha256 \
    -key "$SERVER_KEY" \
    -out "$SERVER_CSR" \
    -subj "$SERVER_SUBJECT" \
    -config "$OPENSSL_CNF"
  echo -e "   CSR: ${SERVER_CSR}"

  echo -e "\n${YELLOW}6. Signing server certificate with Root CA...${NC}"
  openssl x509 -req -sha256 \
    -in "$SERVER_CSR" \
    -CA "$CA_CERT" \
    -CAkey "$CA_KEY" \
    -CAcreateserial \
    -out "$SERVER_CERT" \
    -days "$CERT_VALIDITY_DAYS" \
    -extensions v3_req \
    -extfile "$OPENSSL_CNF"
  echo -e "   Cert: ${SERVER_CERT}"

  echo -e "\n${YELLOW}7. Verifying certificate chain...${NC}"
  if openssl verify -CAfile "$CA_CERT" "$SERVER_CERT" 2>/dev/null | grep -q "OK"; then
    echo -e "   ${GREEN}✓ Certificate chain verification: OK${NC}"
  else
    echo -e "   ${RED}✖ Certificate chain verification: FAILED${NC}"
    exit 1
  fi

  echo -e "\n${YELLOW}8. Certificate SAN entries:${NC}"
  openssl x509 -in "$SERVER_CERT" -noout -text 2>/dev/null | grep -A1 "Subject Alternative Name" | tail -1 | tr ',' '\n' | sed 's/^ */   - /'

  rm -f "$SERVER_CSR" "$CERT_DIR/ca.srl"

  echo -e "\n${BLUE}══════════════════════════════════════════════════════${NC}"
  echo -e "${GREEN}${BOLD}✓ TLS certificates generated successfully!${NC}"
  echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"
  echo -e "  CA Certificate:     ${CA_CERT}"
  echo -e "  Server Certificate: ${SERVER_CERT}"
  echo -e "  Server Key:         ${SERVER_KEY}"
  echo -e "  SAN Config:         ${OPENSSL_CNF}"
}

main "$@"
