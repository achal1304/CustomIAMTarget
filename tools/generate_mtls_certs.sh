#!/bin/bash

# Generate mTLS Test Certificates
# Creates CA, server, and client certificates for testing mTLS authentication

set -e

CERT_DIR="certs"
DAYS_VALID=3650  # 10 years for testing

echo "🔐 Generating mTLS Test Certificates..."
echo ""

# Create certs directory
mkdir -p "$CERT_DIR"

# 1. Generate CA (Certificate Authority)
echo "📋 Step 1: Generating CA certificate..."
openssl req -x509 -newkey rsa:4096 -days $DAYS_VALID -nodes \
  -keyout "$CERT_DIR/ca-key.pem" \
  -out "$CERT_DIR/ca-cert.pem" \
  -subj "/C=US/ST=Test/L=Test/O=SCIM Test CA/CN=scim-test-ca"

echo "   ✓ CA certificate created: $CERT_DIR/ca-cert.pem"
echo ""

# 2. Generate Server Certificate
echo "📋 Step 2: Generating server certificate..."
openssl req -newkey rsa:4096 -nodes \
  -keyout "$CERT_DIR/server-key.pem" \
  -out "$CERT_DIR/server-req.pem" \
  -subj "/C=US/ST=Test/L=Test/O=SCIM Server/CN=localhost"

openssl x509 -req -in "$CERT_DIR/server-req.pem" -days $DAYS_VALID \
  -CA "$CERT_DIR/ca-cert.pem" -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial \
  -out "$CERT_DIR/server-cert.pem" \
  -extfile <(printf "subjectAltName=DNS:localhost,IP:127.0.0.1")

echo "   ✓ Server certificate created: $CERT_DIR/server-cert.pem"
echo ""

# 3. Generate Client Certificates (3 different clients with different permissions)
echo "📋 Step 3: Generating client certificates..."

# Client 1: admin-client (full access)
openssl req -newkey rsa:4096 -nodes \
  -keyout "$CERT_DIR/client-admin-key.pem" \
  -out "$CERT_DIR/client-admin-req.pem" \
  -subj "/C=US/ST=Test/L=Test/O=SCIM Client/CN=admin-client"

openssl x509 -req -in "$CERT_DIR/client-admin-req.pem" -days $DAYS_VALID \
  -CA "$CERT_DIR/ca-cert.pem" -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial \
  -out "$CERT_DIR/client-admin-cert.pem"

echo "   ✓ Admin client certificate created: $CERT_DIR/client-admin-cert.pem"

# Client 2: readonly-client (read-only access)
openssl req -newkey rsa:4096 -nodes \
  -keyout "$CERT_DIR/client-readonly-key.pem" \
  -out "$CERT_DIR/client-readonly-req.pem" \
  -subj "/C=US/ST=Test/L=Test/O=SCIM Client/CN=readonly-client"

openssl x509 -req -in "$CERT_DIR/client-readonly-req.pem" -days $DAYS_VALID \
  -CA "$CERT_DIR/ca-cert.pem" -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial \
  -out "$CERT_DIR/client-readonly-cert.pem"

echo "   ✓ Readonly client certificate created: $CERT_DIR/client-readonly-cert.pem"

# Client 3: scim-client (SCIM operations only)
openssl req -newkey rsa:4096 -nodes \
  -keyout "$CERT_DIR/client-scim-key.pem" \
  -out "$CERT_DIR/client-scim-req.pem" \
  -subj "/C=US/ST=Test/L=Test/O=SCIM Client/CN=scim-client"

openssl x509 -req -in "$CERT_DIR/client-scim-req.pem" -days $DAYS_VALID \
  -CA "$CERT_DIR/ca-cert.pem" -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial \
  -out "$CERT_DIR/client-scim-cert.pem"

echo "   ✓ SCIM client certificate created: $CERT_DIR/client-scim-cert.pem"
echo ""

# 4. Create combined PEM files (cert + key) for easier use
echo "📋 Step 4: Creating combined PEM files..."
cat "$CERT_DIR/client-admin-cert.pem" "$CERT_DIR/client-admin-key.pem" > "$CERT_DIR/client-admin.pem"
cat "$CERT_DIR/client-readonly-cert.pem" "$CERT_DIR/client-readonly-key.pem" > "$CERT_DIR/client-readonly.pem"
cat "$CERT_DIR/client-scim-cert.pem" "$CERT_DIR/client-scim-key.pem" > "$CERT_DIR/client-scim.pem"
echo "   ✓ Combined PEM files created"
echo ""

# 5. Clean up intermediate files
rm -f "$CERT_DIR"/*.req "$CERT_DIR"/*.srl

# 6. Display certificate information
echo "✅ Certificate generation complete!"
echo ""
echo "📁 Generated files in $CERT_DIR/:"
echo "   CA Certificate:        ca-cert.pem"
echo "   CA Private Key:        ca-key.pem"
echo "   Server Certificate:    server-cert.pem"
echo "   Server Private Key:    server-key.pem"
echo ""
echo "   Client Certificates:"
echo "   1. admin-client:       client-admin.pem (full access)"
echo "   2. readonly-client:    client-readonly.pem (read-only)"
echo "   3. scim-client:        client-scim.pem (SCIM only)"
echo ""
echo "🔍 Certificate Details:"
echo ""
echo "Admin Client (CN=admin-client):"
openssl x509 -in "$CERT_DIR/client-admin-cert.pem" -noout -subject -dates
echo ""
echo "Readonly Client (CN=readonly-client):"
openssl x509 -in "$CERT_DIR/client-readonly-cert.pem" -noout -subject -dates
echo ""
echo "SCIM Client (CN=scim-client):"
openssl x509 -in "$CERT_DIR/client-scim-cert.pem" -noout -subject -dates
echo ""
echo "📝 Next steps:"
echo "   1. Update .env with: AUTH_MTLS_ENABLED=true"
echo "   2. Configure nginx/Apache for mTLS (see MTLS_SETUP_GUIDE.md)"
echo "   3. Test with: curl --cert certs/client-admin.pem --cacert certs/ca-cert.pem https://localhost:5000/scim/v2/Users"
echo ""

# Made with Bob
