#!/usr/bin/env bash
# scripts/make_ca.sh - generate private CA and node certificates for hyge mTLS
# Plain openssl commands only. CA key stays offline after signing.

set -euo pipefail

OUT_DIR="${1:-certs}"
mkdir -p "${OUT_DIR}"

# 1. Private Certificate Authority (CA)
openssl genrsa -out "${OUT_DIR}/ca.key" 2048
openssl req -x509 -new -nodes -key "${OUT_DIR}/ca.key" -sha256 -days 3650 \
    -out "${OUT_DIR}/ca.crt" -subj "/CN=hyge-ca"

# 2. Node certificates signed by CA
for NODE in desktop laptop-a laptop-b authority; do
    openssl genrsa -out "${OUT_DIR}/${NODE}.key" 2048
    openssl req -new -key "${OUT_DIR}/${NODE}.key" -out "${OUT_DIR}/${NODE}.csr" \
        -subj "/CN=${NODE}"
    openssl x509 -req -in "${OUT_DIR}/${NODE}.csr" -CA "${OUT_DIR}/ca.crt" \
        -CAkey "${OUT_DIR}/ca.key" -CAcreateserial \
        -out "${OUT_DIR}/${NODE}.crt" -days 3650 -sha256
    rm -f "${OUT_DIR}/${NODE}.csr"
done

# Set permissions: private keys read-only by owner
chmod 600 "${OUT_DIR}"/*.key
chmod 644 "${OUT_DIR}"/*.crt

echo "Certificates generated in ${OUT_DIR}"
