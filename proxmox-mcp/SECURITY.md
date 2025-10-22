# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Security Best Practices

### Credential Management

#### Username/Password Authentication

Proxmox uses username/password or API token authentication:

```json
// config.json
{
  "host": "192.168.1.10",
  "username": "root@pam",
  "password": "your-password-here"
}
```

**Best Practices:**
- Use dedicated service accounts instead of root
- Create user in Proxmox with minimal required permissions
- Store credentials in secure configuration files with restrictive permissions

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

```json
{
  "ssl_verify": true
}
```

**Valid Certificate Options:**
1. **Let's Encrypt** (free, automated)
2. **Commercial CA certificates** (DigiCert, etc.)
3. **Internal CA** (for enterprise environments)

#### Development/Testing

Self-signed certificates can be used for testing:

```json
{
  "ssl_verify": false  // Development only!
}
```

**⚠️ Warning:** Disabling SSL verification makes you vulnerable to man-in-the-middle attacks.

#### Certificate Best Practices

- **Use strong encryption** (TLS 1.2 or higher)
- **Rotate certificates** before expiration
- **Monitor certificate expiry** (alerts at 30/7 days)
- **Use strong key sizes** (2048-bit RSA minimum, 256-bit ECC)
- **Disable weak ciphers** (RC4, 3DES, MD5)

### Network Security

#### Network Segmentation

**Isolate Proxmox management:**
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
[VM Network: 192.168.1.0/24]
    |
[Management VLAN] - [Admin Network: 10.0.0.0/24]
    |
    +-- [Proxmox Node: 10.0.0.20]
    +-- [Admin Workstation: 10.0.0.10]
```

#### Firewall Rules

**Restrict MCP server access:**
```
Action: Pass
Interface: LAN
Protocol: TCP
Source: Admin Network (10.0.0.0/24)
Destination: Proxmox Node (10.0.0.20:8006)
Description: Allow MCP server to Proxmox API
```

### Access Control

#### Principle of Least Privilege

**Create dedicated API users:**
1. Don't use the default `root@pam` account
2. Create service account: `proxmox-mcp@pve`
3. Grant only required permissions:
   - VM.Allocate (if creating VMs)
   - VM.Config.* (for VM management)
   - Datastore.Allocate (for storage operations)
   - Sys.Audit (for monitoring)
4. Regularly review and audit permissions

#### Multi-Factor Authentication

**Enable 2FA on Proxmox:**
1. Navigate to **Datacenter → Users**
2. Select the user
3. Click **TFA**
4. Add TOTP authentication
5. Configure with Google Authenticator, Authy, etc.

### Input Validation

All inputs are validated before processing, but you should also:

**Validate VM operations:**
```python
# Good - specific VMs
vmid = 100

# Risky - operations on production VMs
# Always double-check VMID before destructive operations
```

**Sanitize user input:**
```python
# Never pass unsanitized input to API
description = user_input.strip()[:255]  # Limit length
description = re.sub(r'[^\w\s-]', '', description)  # Remove special chars
```

### Logging and Monitoring

#### Enable Logging

**Proxmox logging:**
```bash
# Enable detailed logging
Datacenter → Options → Syslog
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
- VM creation/deletion
- Snapshot operations
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
# Update Proxmox
apt update && apt upgrade

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
  - [ ] Logging enabled on Proxmox
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
