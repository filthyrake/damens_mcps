# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Security Best Practices

### Credential Management

#### API Key Authentication (Recommended)

**Use API keys instead of username/password when possible:**

```bash
# .env
TRUENAS_API_KEY=your-api-key-here
```

**Benefits:**
- Keys can be rotated without changing passwords
- Easier to revoke specific API access
- Reduces exposure of admin credentials
- Supports granular permissions

**How to generate:**
1. Log into TrueNAS web interface
2. Click on the user icon (top right)
3. Click **API Keys**
4. Click **Add** to create a new API key
5. Give it a descriptive name (e.g., "MCP Server")
6. Copy and securely store the generated key

#### Storing Credentials Securely

**Never store credentials in:**
- Git repositories (use `.gitignore`)
- Code comments or documentation examples
- Unencrypted files on shared systems
- Application logs

**Do store credentials in:**
- Environment variables (`.env` files not in git)
- Secure secret management systems (Vault, AWS Secrets Manager)
- Encrypted configuration files (with separate key management)
- OS credential stores (keychain, credential manager)

**File Permissions:**
```bash
# Ensure only you can read credential files
chmod 600 .env
chmod 600 config.json
```

### SSL/TLS Configuration

#### Production Requirements

**Always use SSL verification in production:**

```bash
TRUENAS_VERIFY_SSL=true  # This is the default
```

**⚠️ CRITICAL SECURITY NOTICE:**
- SSL verification is **enabled by default** in all example configurations
- The server will emit a visible warning on startup if SSL verification is disabled
- Disabling SSL verification exposes your system to **man-in-the-middle attacks**
- An attacker could intercept credentials and API calls between the MCP server and TrueNAS

**Valid Certificate Options:**
1. **Let's Encrypt** (free, automated, recommended)
   - Free SSL certificates with automatic renewal
   - Widely trusted by all major browsers and systems
   - Easy to set up with most web servers
2. **Commercial CA certificates** (DigiCert, GlobalSign, etc.)
   - Best for enterprise environments requiring specific compliance
   - Provides extended validation options
3. **Internal CA** (for enterprise environments)
   - Allows centralized certificate management
   - Requires distribution of CA certificate to all clients
   - Good for isolated networks without internet access

#### Development/Testing

Self-signed certificates should **only** be used for testing in isolated environments:

```bash
TRUENAS_VERIFY_SSL=false  # ⚠️ Development/testing only!
```

**When to disable SSL verification:**
- Local development with self-signed certificates
- Testing in isolated lab environments
- Temporary troubleshooting (re-enable immediately after)

**Never disable SSL verification when:**
- Deploying to production
- Connecting over untrusted networks
- Handling sensitive data
- Accessing the system remotely

#### Setting Up Proper SSL Certificates

**Option 1: Let's Encrypt (Recommended)**
```bash
# Install certbot on TrueNAS
pkg install py39-certbot

# Generate certificate
certbot certonly --standalone -d truenas.yourdomain.com

# Configure TrueNAS to use the certificate via the web UI:
# System -> Certificates -> Import Certificate
```

**Option 2: Import Commercial Certificate**
1. Purchase certificate from a CA
2. Generate CSR in TrueNAS (System -> Certificates)
3. Submit CSR to CA
4. Import signed certificate back into TrueNAS

**Option 3: Internal CA for Enterprise**
```bash
# On your CA server, generate certificate for TrueNAS
openssl req -new -key truenas.key -out truenas.csr

# Sign with your internal CA
openssl x509 -req -in truenas.csr -CA ca.crt -CAkey ca.key -out truenas.crt

# Import into TrueNAS via System -> Certificates
```

**After installing a valid certificate:**
1. Verify the certificate is active in TrueNAS web UI
2. Set `TRUENAS_VERIFY_SSL=true` in your .env file
3. Restart the MCP server
4. Confirm no SSL warnings appear

#### Certificate Best Practices

- **Use strong encryption** (TLS 1.2 or higher)
- **Rotate certificates** before expiration
- **Monitor certificate expiry** (alerts at 30/7 days)
- **Use strong key sizes** (2048-bit RSA minimum, 256-bit ECC)
- **Disable weak ciphers** (RC4, 3DES, MD5)

### JWT Token Security

#### Secret Key Requirements

**CRITICAL:** The `SECRET_KEY` environment variable is used to sign JWT authentication tokens. A weak key compromises the entire authentication system.

**The server enforces strong secret key requirements:**
- **Minimum 32 characters long**
- **At least 3 of 4 character types:** lowercase letters, uppercase letters, digits, special characters
- **No excessive repetition:** no single character can appear more than half the time

#### Generating Secure Secret Keys

**Recommended method** (Python secrets module):
```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

**Alternative methods:**
```bash
# Using OpenSSL
openssl rand -base64 32

# Using /dev/urandom (Linux/macOS)
head -c 32 /dev/urandom | base64
```

**❌ Examples of WEAK keys that will be REJECTED:**
```bash
SECRET_KEY=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa  # All same character
SECRET_KEY=00000000000000000000000000000000  # All zeros  
SECRET_KEY=abcdefghijklmnopqrstuvwxyzabcdef  # Only lowercase, no diversity
SECRET_KEY=password123password123password123 # Predictable pattern
SECRET_KEY=short                             # Too short
```

**✅ Examples of STRONG keys that will be ACCEPTED:**
```bash
SECRET_KEY=MyS3cureP@ssw0rd!WithMixedChars123  # Mixed character types
SECRET_KEY=Abcd1234!@#$efgh5678%^&*IJKL9876   # High entropy
SECRET_KEY=K7mN_p2QrS-tU3vWx4Yz!A5bC6dE7fG8  # Random generation
```

#### Why JWT Token Security Matters

JWT tokens provide authentication for the MCP server HTTP API. If the secret key is compromised:

**Attack Scenarios:**
1. **Token Forgery:** Attacker creates valid JWT tokens with any username/permissions
2. **Privilege Escalation:** Attacker gains admin access to TrueNAS through forged tokens
3. **Data Breach:** Full read/write access to all TrueNAS data and configurations
4. **System Compromise:** Ability to execute any API call with admin privileges

**Impact:**
- Complete bypass of authentication system
- Unauthorized access to storage systems
- Potential data loss or corruption
- Breach of multi-tenant boundaries
- Compliance violations (HIPAA, SOC2, etc.)

#### JWT Token Best Practices

**Secret Key Management:**
- Generate keys using cryptographically secure random number generators
- Store keys in environment variables, never in code or git
- Rotate keys periodically (recommended: every 90 days)
- Use different keys for development, staging, and production
- Treat secret keys with same sensitivity as root passwords

**Token Configuration:**
```bash
# Strong secret key (required)
SECRET_KEY=<generated-secure-key>

# Token expiration (default: 30 minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30

# JWT algorithm (default: HS256)
JWT_ALGORITHM=HS256
```

**Token Handling:**
- Use HTTPS/TLS for all API calls to prevent token interception
- Set appropriate token expiration times (30 minutes recommended)
- Implement token refresh mechanisms for long-running sessions
- Revoke tokens on logout or password change
- Monitor for unusual token usage patterns

**Validation on Startup:**
The server validates secret key strength on startup. If validation fails:
```
ValidationError: SECRET_KEY must be at least 32 characters with sufficient entropy.
Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

This prevents the server from starting with weak keys, protecting against configuration errors.

### Network Security

#### Network Segmentation

**Isolate TrueNAS management:**
- Place management interface on dedicated VLAN
- Use firewall rules to restrict access
- Allow access only from trusted networks
- Consider VPN for remote management

**Example Network Architecture:**
```
Internet
    |
[Firewall]
    |
[User Network: 192.168.1.0/24]
    |
[Management VLAN] - [Admin Network: 10.0.0.0/24]
    |
    +-- [TrueNAS Management: 10.0.0.5]
    +-- [Admin Workstation: 10.0.0.10]
```

#### Firewall Rules

**Restrict MCP server access:**
```
Action: Pass
Interface: LAN
Protocol: TCP
Source: Admin Network (10.0.0.0/24)
Destination: TrueNAS Management (10.0.0.5:443)
Description: Allow MCP server to TrueNAS API
```

### Access Control

#### Principle of Least Privilege

**Create dedicated API users:**
1. Don't use the default `admin` account
2. Create service account: `truenas-mcp`
3. Grant only required permissions:
   - System: Read (for status monitoring)
   - Storage: Read/Write (for pool/dataset management)
   - Network: Read (for interface status)
   - Services: Read/Write (for service control)
4. Regularly review and audit permissions

#### Multi-Factor Authentication

**Enable 2FA on TrueNAS:**
1. Navigate to **Credentials → Local Users**
2. Edit the admin user
3. Enable **Two-Factor Authentication**
4. Configure TOTP (Google Authenticator, Authy, etc.)
5. API keys may bypass MFA, so protect them carefully

### Input Validation

All inputs are validated before processing, but you should also:

**Validate storage operations:**
```python
# Good - specific datasets
dataset = "tank/safe-data"

# Risky - root pool operations
dataset = "tank"  # Only use when truly needed
```

**Sanitize user input:**
```python
# Never pass unsanitized input to API
description = user_input.strip()[:255]  # Limit length
description = re.sub(r'[^\w\s-]', '', description)  # Remove special chars
```

### Logging and Monitoring

#### Enable Logging

**TrueNAS logging:**
```bash
# Enable detailed API logging
System → Advanced → Audit
```

**MCP server logging:**
```bash
# Set log level
export LOG_LEVEL=INFO  # Or DEBUG for troubleshooting
```

#### Log Monitoring

**What to monitor:**
- Failed authentication attempts (threshold: 5 in 5 minutes)
- Unauthorized API access attempts
- Storage pool changes
- Dataset creation/deletion
- Configuration changes

**Log forwarding:**
- Send logs to centralized SIEM (Splunk, ELK, Graylog)
- Configure alerts for suspicious patterns
- Retain logs for compliance (typically 90+ days)

#### Sensitive Data in Logs

**Never log:**
- Passwords or API keys
- Full authentication tokens
- Personal identifiable information (PII)

**Redact sensitive data:**
```python
logger.info(f"Authentication attempt for user: {username}")
# Not: logger.info(f"Auth attempt: {username}:{password}")
```

### Security Updates

#### Keep Software Updated

**Update regularly:**
```bash
# Update TrueNAS
System → Update → Check Available

# Update MCP server dependencies
pip install --upgrade -r requirements.txt

# Check for security advisories
pip install safety
safety check
```

**Update schedule:**
- **Critical security patches:** Within 24 hours
- **Important updates:** Within 1 week
- **Regular updates:** Monthly
- **Dependency updates:** Quarterly

### Incident Response

#### Security Incident Procedure

**If you suspect a security breach:**

1. **Isolate the system**
   - Disconnect from network if necessary
   - Disable API access
   - Revoke potentially compromised credentials

2. **Assess the damage**
   - Review audit logs
   - Check for unauthorized changes
   - Identify affected systems

3. **Contain the incident**
   - Change all passwords immediately
   - Rotate API keys
   - Update firewall rules to block attacker

4. **Eradicate the threat**
   - Remove any malicious configurations
   - Close security vulnerabilities
   - Update to patched versions

5. **Recover**
   - Restore from clean backups if needed
   - Verify system integrity
   - Gradually restore services

6. **Post-incident review**
   - Document what happened
   - Identify root cause
   - Implement preventive measures
   - Update incident response procedures

### Vulnerability Disclosure

#### Reporting Security Vulnerabilities

**🔒 Please report security vulnerabilities responsibly.**

**Do NOT:**
- Open public GitHub issues for security bugs
- Disclose vulnerabilities before they're fixed
- Post exploits publicly

**DO:**
- Email security concerns privately to maintainers
- Provide detailed information:
  - Description of vulnerability
  - Steps to reproduce
  - Potential impact
  - Suggested fix (if any)
- Allow reasonable time for fix (typically 90 days)
- Coordinate disclosure timeline

**What to expect:**
- Acknowledgment within 48 hours
- Regular updates on fix progress
- Credit in security advisory (if desired)
- CVE assignment for significant issues

#### Security Response Timeline

- **Critical vulnerabilities:** Fix within 7 days
- **High severity:** Fix within 30 days
- **Medium severity:** Fix within 90 days
- **Low severity:** Fix in next release

## Security Checklist

### Deployment Checklist

Before deploying to production:

- [ ] **Credentials**
  - [ ] API keys stored securely (not in git)
  - [ ] File permissions set to 600
  - [ ] Using dedicated service account
  - [ ] Password complexity requirements met
  - [ ] Password rotation schedule defined

- [ ] **Network Security**
  - [ ] Management network is isolated
  - [ ] Firewall rules restrict MCP server access
  - [ ] VPN required for remote access
  - [ ] SSL/TLS verification enabled

- [ ] **Access Control**
  - [ ] Least privilege permissions assigned
  - [ ] Multi-factor authentication enabled
  - [ ] Regular access reviews scheduled
  - [ ] Unused accounts disabled

- [ ] **Monitoring**
  - [ ] Logging enabled on TrueNAS
  - [ ] Logs forwarded to SIEM
  - [ ] Alerts configured for suspicious activity
  - [ ] Log retention policy defined

- [ ] **Maintenance**
  - [ ] Update procedure documented
  - [ ] Backup schedule defined
  - [ ] Incident response plan created
  - [ ] Security contact information current

### Operational Security

Ongoing security practices:

- [ ] **Weekly:**
  - [ ] Review authentication logs
  - [ ] Check for failed login attempts
  - [ ] Monitor for unusual API activity

- [ ] **Monthly:**
  - [ ] Review firewall rule changes
  - [ ] Audit user access and permissions
  - [ ] Check for software updates
  - [ ] Review security alerts

- [ ] **Quarterly:**
  - [ ] Rotate API keys
  - [ ] Update dependencies
  - [ ] Security training refresh
  - [ ] Test incident response procedures

- [ ] **Annually:**
  - [ ] Comprehensive security audit
  - [ ] Penetration testing
  - [ ] Update security policies
  - [ ] Review and update documentation

## Known Limitations

### Current Security Constraints

**Authentication:**
- API keys transmitted with each request (use HTTPS!)
- No built-in rate limiting (implement at network level)
- Session management depends on pfSense API

**Authorization:**
- Granular permission control depends on pfSense API
- MCP server inherits API user's full permissions

**Encryption:**
- Credentials stored in plain text in `.env` (file permissions critical)
- No built-in encryption for configuration files
- Consider external secret management for production

### Planned Security Improvements

- [ ] Integration with external secret managers (Vault, AWS Secrets Manager)
- [ ] Built-in rate limiting
- [ ] Session token management
- [ ] Encrypted configuration files
- [ ] Audit logging framework
- [ ] Security policy enforcement

## Compliance

### Regulatory Considerations

If your deployment must comply with regulations:

**PCI DSS:**
- Encrypt transmission of cardholder data (use HTTPS)
- Restrict access to cardholder data (network segmentation)
- Maintain audit trails (enable comprehensive logging)
- Regularly test security systems (penetration testing)

**HIPAA:**
- Implement access controls (MFA, least privilege)
- Encrypt data in transit (SSL/TLS)
- Maintain audit logs (centralized logging)
- Have breach notification procedures

**GDPR:**
- Protect personal data (encryption, access control)
- Maintain processing records (audit logs)
- Have incident response procedures
- Implement data minimization

**SOC 2:**
- Security controls documented
- Access controls implemented
- Monitoring and logging in place
- Incident response procedures defined

---

## Contact

For security concerns, contact:
- **Email:** [See repository maintainers]
- **Security Advisory:** Use GitHub Security Advisories
- **Emergency:** Contact repository owner directly

---

**Last Updated:** 2024-10-22

**Remember: Security is a continuous process, not a one-time task.**
