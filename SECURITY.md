# Security Policy

## Supported Versions

This repository contains multiple MCP server projects. All current versions are actively maintained:

| Project | Version | Supported |
|---------|---------|-----------|
| pfSense MCP | 1.x.x | ✅ |
| TrueNAS MCP | 1.x.x | ✅ |
| iDRAC MCP | 1.x.x | ✅ |
| Proxmox MCP | 1.x.x | ✅ |

## Reporting a Vulnerability

**Please report security vulnerabilities responsibly.**

### 🔒 Private Reporting (Preferred)

Use GitHub's private vulnerability reporting:

1. Go to the [Security tab](../../security)
2. Click "Report a vulnerability"
3. Fill out the form with:
   - Which project(s) are affected
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### 📧 Email Reporting

Alternatively, email security concerns to the repository maintainers (see [README.md](README.md) for contact information).

### ⚠️ What NOT to Do

- **Do NOT** open public GitHub issues for security bugs
- **Do NOT** disclose vulnerabilities publicly before they're fixed
- **Do NOT** post exploits or proof-of-concept code publicly

### What to Include

A good security report includes:

```
Project: [pfsense-mcp/truenas-mcp/idrac-mcp/proxmox-mcp]
Severity: [Critical/High/Medium/Low]
Type: [e.g., Command Injection, Path Traversal, etc.]

Description:
[Clear description of the vulnerability]

Steps to Reproduce:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Impact:
[What can an attacker do?]

Suggested Fix:
[Optional: Your proposed solution]

Additional Context:
[Any other relevant information]
```

## Response Timeline

We are committed to addressing security issues promptly:

| Severity | Response Time | Fix Target |
|----------|--------------|------------|
| **Critical** | 24 hours | 7 days |
| **High** | 48 hours | 30 days |
| **Medium** | 1 week | 90 days |
| **Low** | 2 weeks | Next release |

### What to Expect

1. **Acknowledgment** within 24-48 hours
2. **Initial assessment** within 1 week
3. **Regular updates** on fix progress
4. **Fix and disclosure** coordination
5. **Credit** in security advisory (if desired)
6. **CVE assignment** for significant issues

## Security Best Practices

### For Contributors

When contributing code:

- **Validate all inputs** before processing
- **Use whitelist approaches** for validation (allow known-good, not block known-bad)
- **Never hardcode credentials** or secrets
- **Use parameterized queries** to prevent injection attacks
- **Sanitize error messages** to avoid information leakage
- **Follow least privilege principle** in all designs
- **Review project-specific SECURITY.md** files

### For Users/Deployers

When deploying these MCP servers:

#### 1. Credential Management

**Use API keys instead of passwords:**
```bash
# Good
PLATFORM_API_KEY=your-secure-api-key

# Less secure
PLATFORM_USERNAME=admin
PLATFORM_PASSWORD=password123
```

**Secure credential storage:**
- Use environment variables (`.env` files not in git)
- Set file permissions: `chmod 600 .env config.json`
- Consider secret management systems (Vault, AWS Secrets Manager)
- Rotate credentials regularly (quarterly minimum)

#### 2. Network Security

**Isolate management networks:**
- Place MCP servers on dedicated management VLANs
- Restrict access with firewall rules
- Use VPN for remote access
- Implement network segmentation

**Use HTTPS/TLS:**
```bash
# Production (always!)
SSL_VERIFY=true

# Development only (never in production!)
SSL_VERIFY=false
```

#### 3. Access Control

**Principle of least privilege:**
- Create dedicated service accounts for MCP servers
- Grant only required permissions
- Avoid using default admin accounts
- Enable multi-factor authentication where possible
- Regularly audit access permissions

#### 4. Monitoring & Logging

**Enable comprehensive logging:**
- Log all authentication attempts
- Monitor for failed login attempts
- Track configuration changes
- Set up alerts for suspicious activity
- Forward logs to centralized SIEM

**What to monitor:**
- Failed authentication (threshold: 5 in 5 minutes)
- Unauthorized API access attempts
- Configuration changes
- Unusual API usage patterns
- Service restarts or disruptions

#### 5. Updates & Patching

**Keep everything updated:**
```bash
# Update Python dependencies regularly
pip install --upgrade -r requirements.txt

# Check for security issues
pip install safety
safety check

# Update the MCP server code
git pull
```

**Update schedule:**
- **Critical security patches:** Within 24 hours
- **Important updates:** Within 1 week
- **Regular updates:** Monthly
- **Dependency updates:** Quarterly

## Known Security Considerations

### Authentication

- API keys/tokens are transmitted with each request (HTTPS required)
- No built-in rate limiting (implement at network/proxy level)
- Session management depends on underlying platform APIs

### Authorization

- MCP servers inherit the permissions of their API credentials
- Granular permission control depends on platform capabilities
- No built-in role-based access control in MCP layer

### Data Storage

- Credentials stored in plaintext in `.env` or `config.json` files
  - **Critical:** Set proper file permissions (`chmod 600`)
  - **Better:** Use external secret management systems
- No built-in encryption for configuration files
- Consider encrypted volumes for production deployments

### Network Communications

- All API calls go over network to target platforms
- HTTPS/TLS required for production (prevents MITM attacks)
- No built-in request signing or additional authentication layers

## Security Features by Project

Each project has specific security considerations documented in their respective `SECURITY.md` files:

### pfSense MCP
- Firewall rule validation
- Command injection prevention
- Network segmentation recommendations
- See: [pfsense-mcp/SECURITY.md](pfsense-mcp/SECURITY.md)

### TrueNAS MCP
- Path traversal protection
- Dataset name validation
- Storage access controls
- See: [truenas-mcp/SECURITY.md](truenas-mcp/SECURITY.md)

### iDRAC MCP
- Multi-server credential management
- Power operation safeguards
- Fleet security considerations
- See: [idrac-mcp/SECURITY.md](idrac-mcp/SECURITY.md)

### Proxmox MCP
- VM/Container operation validation
- Node access controls
- Virtualization security
- See: [proxmox-mcp/SECURITY.md](proxmox-mcp/SECURITY.md)

## Recent Security Improvements

### Input Validation Enhancement (2024-10)

Comprehensive input validation improvements across all projects:

- **pfSense**: Command injection prevention for package/service operations
- **TrueNAS**: Path traversal protection for ID-based operations
- **iDRAC**: VMID and node name validation
- **Proxmox**: Enhanced validation for VM/container operations

See: [SECURITY_SUMMARY.md](SECURITY_SUMMARY.md) for details.

### CodeQL Security Scanning

All projects are scanned with CodeQL for:
- Command injection vulnerabilities
- Path traversal issues
- SQL injection risks
- Credential exposure
- Other common vulnerabilities

Current status: ✅ **0 known vulnerabilities**

## Compliance Considerations

### Regulatory Frameworks

If your deployment must comply with regulations:

**PCI DSS:**
- Encrypt transmission (HTTPS/TLS)
- Restrict access (network segmentation, firewall rules)
- Maintain audit trails (comprehensive logging)
- Regular security testing (penetration tests)

**HIPAA:**
- Access controls (MFA, least privilege)
- Encryption in transit (SSL/TLS)
- Audit logging (centralized logging)
- Breach notification procedures

**GDPR:**
- Data protection (encryption, access control)
- Processing records (audit logs)
- Incident response procedures
- Data minimization

**SOC 2:**
- Documented security controls
- Access controls implemented
- Monitoring and logging
- Incident response plan

## Security Checklist

### Deployment Checklist

Before production deployment:

- [ ] **Credentials**
  - [ ] API keys used instead of passwords
  - [ ] Files have 600 permissions
  - [ ] Credentials not in version control
  - [ ] Rotation schedule defined
  
- [ ] **Network**
  - [ ] Management network isolated
  - [ ] Firewall rules restrict access
  - [ ] HTTPS/TLS enabled and verified
  - [ ] VPN required for remote access
  
- [ ] **Access**
  - [ ] Least privilege permissions assigned
  - [ ] Dedicated service accounts created
  - [ ] MFA enabled where possible
  - [ ] Regular access reviews scheduled
  
- [ ] **Monitoring**
  - [ ] Logging enabled
  - [ ] Logs forwarded to SIEM
  - [ ] Alerts configured
  - [ ] Log retention policy defined
  
- [ ] **Maintenance**
  - [ ] Update procedure documented
  - [ ] Backup schedule defined
  - [ ] Incident response plan created
  - [ ] Security contacts current

### Operational Checklist

Ongoing security practices:

- [ ] **Weekly:** Review auth logs, check failed logins
- [ ] **Monthly:** Audit permissions, check updates, review alerts
- [ ] **Quarterly:** Rotate credentials, update dependencies, test IR procedures
- [ ] **Annually:** Security audit, penetration test, policy review

## Contact

For security-related questions or concerns:

- **Vulnerability reports:** Use GitHub Security tab or email maintainers
- **Security questions:** Open a [discussion](../../discussions) (non-sensitive only)
- **Emergency security issues:** Contact repository owner directly

---

**Last Updated:** 2025-10-31

**Remember: Security is a continuous process, not a one-time configuration.**
