# Oracle mTLS Integration Guide

## Overview

This guide explains how to deploy your SCIM service with mTLS authentication for Oracle Identity Cloud Service (IDCS) or Oracle IAM integration.

## Architecture

### Local Testing (with nginx)
```
Client → nginx (TLS termination) → Flask App
         ↓
    Validates certificate
    Passes cert info via headers
```

### Oracle Production (no nginx)
```
Client → Oracle Load Balancer/Gateway (TLS termination) → Your Flask App
         ↓
    Validates certificate
    Passes cert info via headers
```

**Key Point:** Oracle handles TLS termination, so you don't need nginx in production!

## Files Overview

| File | Purpose |
|------|---------|
| `Dockerfile.production` | **For Oracle deployment** - Lightweight, no nginx |
| `Dockerfile.local-mtls` | **For local testing** - Includes nginx for mTLS simulation |
| `Dockerfile.mtls` | **Legacy** - Can be removed or kept as backup |
| `.env.production` | Production environment config for Oracle |
| `.env.mtls` | Local testing environment config |

## Step-by-Step Setup

### Step 1: Generate Certificates

```bash
# Generate test certificates (if not already done)
./tools/generate_mtls_certs.sh

# This creates:
# - certs/ca-cert.pem (CA certificate)
# - certs/ca-key.pem (CA private key)
# - certs/client-*.pem (test client certificates)
# - certs/server-*.pem (server certificates for local testing)
```

### Step 2: Generate Oracle Client Certificate

```bash
cd certs

# Generate certificate for Oracle IDCS
openssl genrsa -out oracle-client-key.pem 2048

openssl req -new -key oracle-client-key.pem \
  -out oracle-client-req.pem \
  -subj "/C=US/ST=California/L=SanFrancisco/O=Oracle/CN=oracle-idcs-client"

openssl x509 -req -in oracle-client-req.pem \
  -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial \
  -out oracle-client-cert.pem -days 365 -sha256

# Combine certificate and key for Oracle
cat oracle-client-cert.pem oracle-client-key.pem > oracle-client.pem

echo "✅ Oracle client certificate created: oracle-client.pem"
```

### Step 3: Update Certificate Mapping

Edit `auth/config.py` (around line 115-126) to add Oracle certificate mapping:

```python
# mTLS configuration
mtls = MutualTLSConfig(
    enabled=os.getenv('AUTH_MTLS_ENABLED', 'false').lower() == 'true',
    require_client_cert=os.getenv('AUTH_MTLS_REQUIRE_CERT', 'false').lower() == 'true',
    trusted_ca_certs_path=os.getenv('AUTH_MTLS_CA_CERTS_PATH', 'certs/ca-cert.pem'),
    
    # Certificate mappings (CN -> identity)
    cert_subject_mapping={
        'admin-client': 'admin-client',
        'readonly-client': 'readonly-client',
        'scim-client': 'scim-client',
        'oracle-idcs-client': 'oracle-idcs-client'  # ADD THIS LINE
    },
    
    # Identity-specific scopes
    cert_scopes={
        'admin-client': ['scim.read', 'scim.write', 'supportingdata.read'],
        'readonly-client': ['scim.read', 'supportingdata.read'],
        'scim-client': ['scim.read', 'scim.write'],
        'oracle-idcs-client': ['scim.read', 'scim.write']  # ADD THIS LINE
    },
    default_scopes=['scim.read']
)
```

### Step 4: Local Testing (Before Oracle)

Test mTLS locally with nginx to ensure everything works:

```bash
# 1. Build local testing image
docker build -f Dockerfile.local-mtls -t scim-local-mtls .

# 2. Run with local mTLS environment
docker run -p 8080:8080 -p 8443:8443 \
  --env-file .env.mtls \
  scim-local-mtls

# 3. Test HTTP endpoint (no certificate)
curl http://localhost:8080/scim/v2/ServiceProviderConfig

# 4. Test HTTPS with admin certificate
curl -k --cert certs/client-admin.pem \
  https://localhost:8443/scim/v2/Users

# 5. Run automated tests
python3 test_mtls_remote.py https://localhost:8443
```

**Expected Results:**
- ✅ HTTP endpoint works without certificate
- ✅ HTTPS with valid certificate returns data
- ✅ HTTPS without certificate returns 401 (if required)
- ✅ Different certificates have different scopes

### Step 5: Deploy to Oracle

```bash
# 1. Build production image (no nginx)
docker build -f Dockerfile.production -t scim-production .

# 2. Test locally first
docker run -p 5000:5000 \
  --env-file .env.production \
  scim-production

# 3. Push to your container registry
docker tag scim-production your-registry/scim-production:latest
docker push your-registry/scim-production:latest

# 4. Deploy to Oracle Cloud Infrastructure (OCI)
# Use Oracle Container Engine for Kubernetes (OKE) or Container Instances
```

### Step 6: Configure Oracle IDCS

1. **Login to Oracle IDCS Console**
   - Navigate to: Applications → Add Application → Confidential Application

2. **Configure SCIM Settings**
   - SCIM Base URL: `https://your-domain.com/scim/v2`
   - Authentication: Mutual TLS (mTLS)

3. **Upload Certificates**
   - **CA Certificate**: Upload `certs/ca-cert.pem`
   - **Client Certificate**: Upload `certs/oracle-client.pem`
   - **Client Key**: Upload `certs/oracle-client-key.pem` (if separate upload)

4. **Configure Certificate Validation**
   - Enable certificate validation
   - Set certificate verification depth: 2
   - Enable hostname verification (optional)

5. **Test Connection**
   - Use IDCS "Test Connection" feature
   - Should successfully connect and retrieve ServiceProviderConfig

### Step 7: Verify Oracle Integration

```bash
# Check your application logs
docker logs <container-name>

# You should see:
# [INFO] mTLS authentication enabled
# [DEBUG] Certificate received: CN=oracle-idcs-client
# [DEBUG] Identity mapped: oracle-idcs-client
# [DEBUG] Scopes granted: ['scim.read', 'scim.write']
```

## How It Works

### Local Testing Flow
1. Client sends HTTPS request with certificate to nginx (port 8443)
2. nginx validates certificate against CA
3. nginx extracts certificate info and passes to Flask via headers:
   - `SSL-Client-Cert`: Full certificate
   - `SSL-Client-S-DN`: Subject DN (e.g., `CN=oracle-idcs-client,O=Oracle,...`)
   - `SSL-Client-Verify`: SUCCESS or FAILED
4. Flask's `MutualTLSAuthenticator` reads headers
5. Extracts CN from Subject DN
6. Maps CN to identity and scopes
7. Authorizes request based on scopes

### Oracle Production Flow
1. Client (Oracle IDCS) sends HTTPS request with certificate to Oracle Gateway
2. **Oracle Gateway** validates certificate against your CA
3. **Oracle Gateway** extracts certificate info and passes to your app via headers
4. Your Flask app receives plain HTTP with certificate headers
5. Same authentication logic as local testing
6. No nginx needed!

## Environment Variables

### Production (.env.production)
```bash
AUTH_MTLS_ENABLED=true
AUTH_MTLS_REQUIRE_CERT=true
AUTH_OAUTH_ENABLED=false
AUTH_BASIC_ENABLED=false
```

### Local Testing (.env.mtls)
```bash
AUTH_MTLS_ENABLED=true
AUTH_MTLS_REQUIRE_CERT=false  # Optional for testing
AUTH_OAUTH_ENABLED=false
AUTH_BASIC_ENABLED=false
```

## Troubleshooting

### Issue: Certificate not recognized

**Check:**
```bash
# Verify certificate CN
openssl x509 -in certs/oracle-client-cert.pem -noout -subject

# Should show: CN=oracle-idcs-client
```

**Fix:** Ensure CN matches your `cert_subject_mapping` in `auth/config.py`

### Issue: 401 Unauthorized from Oracle

**Check:**
1. Is `AUTH_MTLS_ENABLED=true`?
2. Is certificate uploaded to Oracle correctly?
3. Is CA certificate trusted by Oracle?
4. Check Oracle IDCS logs for certificate errors

**Debug:**
```bash
# Enable debug logging
export DEBUG=True

# Check what headers your app receives
# Add to app.py temporarily:
print(f"Headers: {dict(request.headers)}")
```

### Issue: 403 Forbidden (authenticated but no access)

**Check:**
1. Does the identity have required scopes?
2. Check `cert_scopes` mapping in `auth/config.py`
3. Verify endpoint requires correct scopes

**Debug:**
```python
# In auth/authenticators.py, add logging:
print(f"Identity: {identity}")
print(f"Scopes: {scopes}")
print(f"Required: {required_scopes}")
```

### Issue: Local testing works, Oracle doesn't

**Likely causes:**
1. Oracle not passing certificate headers correctly
2. Header names different (check Oracle documentation)
3. Certificate validation failing at Oracle gateway

**Fix:**
- Contact Oracle support for header format
- May need to adjust header names in `auth/authenticators.py`
- Verify Oracle gateway configuration

## Testing Commands

```bash
# Local unit tests
python3 test_mtls.py

# Local integration tests (requires Docker)
docker build -f Dockerfile.local-mtls -t scim-local-mtls .
docker run -p 8080:8080 -p 8443:8443 --env-file .env.mtls scim-local-mtls
python3 test_mtls_remote.py https://localhost:8443

# Test specific certificate
curl -k --cert certs/oracle-client.pem \
  https://localhost:8443/scim/v2/Users

# Test without certificate (should fail if required)
curl -k https://localhost:8443/scim/v2/Users
```

## Security Best Practices

1. **Certificate Rotation**
   - Rotate certificates every 90-365 days
   - Update Oracle IDCS when rotating
   - Keep CA key secure

2. **Production Settings**
   - Always set `AUTH_MTLS_REQUIRE_CERT=true` in production
   - Disable debug mode: `DEBUG=False`
   - Use strong TLS protocols (TLSv1.2+)

3. **Monitoring**
   - Log all authentication attempts
   - Monitor for certificate expiration
   - Alert on authentication failures

4. **Access Control**
   - Use least-privilege scopes
   - Separate read/write certificates if needed
   - Audit certificate usage regularly

## Quick Reference

| Task | Command |
|------|---------|
| Generate certs | `./tools/generate_mtls_certs.sh` |
| Local test | `docker build -f Dockerfile.local-mtls -t scim-local-mtls .` |
| Production build | `docker build -f Dockerfile.production -t scim-production .` |
| Run local | `docker run -p 8080:8080 -p 8443:8443 --env-file .env.mtls scim-local-mtls` |
| Run production | `docker run -p 5000:5000 --env-file .env.production scim-production` |
| Test mTLS | `python3 test_mtls_remote.py https://localhost:8443` |

## Summary

✅ **Local Testing**: Use `Dockerfile.local-mtls` with nginx
✅ **Oracle Production**: Use `Dockerfile.production` without nginx
✅ **Oracle handles**: TLS termination, certificate validation
✅ **Your app receives**: Plain HTTP with certificate headers
✅ **No nginx needed**: In Oracle production deployment

The key insight: Oracle's infrastructure does what nginx does locally!