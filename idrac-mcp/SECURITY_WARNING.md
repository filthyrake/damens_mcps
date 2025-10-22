# 🔐 SECURITY - Credential Management

## ⚠️ IMPORTANT: Credential Storage Options

This project provides **two methods** for managing iDRAC credentials. Understanding the security implications of each is critical.

---

## Method 1: Basic Configuration (config.json) ⚠️

### Security Level: **LOW** - For Development/Testing Only

The basic `working_mcp_server.py` uses a simple JSON configuration file where **credentials are stored in plain text**.

**File: `config.json`**
```json
{
  "idrac_servers": {
    "server1": {
      "host": "192.168.1.100",
      "username": "root",
      "password": "your_password_here",  // ⚠️ PLAIN TEXT
      "ssl_verify": false
    }
  }
}
```

### ⚠️ Security Risks
- **Plain text passwords** - Anyone with file access can read credentials
- **Accidental commits** - Easy to commit to version control
- **No encryption** - No protection if file is exposed
- **Not suitable for production** - Should only be used in isolated test environments

### 🛡️ Mitigation Steps (If Using config.json)
1. **NEVER commit `config.json`** to version control
2. Ensure `config.json` is in `.gitignore` (it is by default)
3. Set restrictive file permissions: `chmod 600 config.json`
4. Store on encrypted filesystems only
5. Regularly rotate passwords
6. Use least-privilege accounts
7. **Consider this for DEVELOPMENT ONLY**

---

## Method 2: Encrypted Fleet Management (Recommended) ✅

### Security Level: **MEDIUM** - Better for Multi-Server Environments

The secure fleet CLI (`secure_fleet_cli.py`) provides encrypted password storage using Fernet (AES-128-CBC).

### ✅ Security Features
- **Encrypted passwords** using Fernet symmetric encryption (AES-128)
- **Separate encryption key** stored in `.fleet_key`
- **Secure password prompts** (no command-line exposure)
- **Both sensitive files** are in `.gitignore`
- **Multi-server management** with centralized credential handling

### 📦 Installation

```bash
# Install the cryptography dependency
pip install cryptography
```

### 🚀 Usage

```bash
# Initialize fleet management (first time only)
python secure_fleet_cli.py init

# Add a server (password will be prompted securely)
python secure_fleet_cli.py add server1 192.168.1.100 root

# List configured servers
python secure_fleet_cli.py list

# Get system info from a server
python secure_fleet_cli.py system-info server1
```

### 🔐 Protected Files
- `fleet_servers.json` - Server configurations with encrypted passwords
- `.fleet_key` - Encryption key (automatically generated)
- Both are automatically excluded via `.gitignore`

### ⚠️ Important Limitations

**Even with encryption, this method has limitations:**

1. **Encryption key on disk** - The `.fleet_key` file is stored unencrypted on the same system
   - If an attacker gains access to the system, they can decrypt passwords
   - This is **symmetric encryption**, not a password manager

2. **No master password** - The encryption key is not password-protected
   - Anyone with filesystem access can decrypt credentials
   - Consider this "obfuscation plus access control" rather than true security

3. **Key management** - If you lose `.fleet_key`, all passwords are irrecoverable

---

## 🏆 Best Practices for Production

For **production environments**, consider these better alternatives:

### Option 1: Environment Variables
```bash
# Set per-server credentials in environment
export IDRAC_HOST="192.168.1.100"
export IDRAC_USERNAME="root"
export IDRAC_PASSWORD="$(cat /secure/vault/idrac_password)"
```

### Option 2: External Secret Management
- **HashiCorp Vault** - Enterprise secret management
- **AWS Secrets Manager** - Cloud-based secrets
- **Azure Key Vault** - Azure secret storage
- **Kubernetes Secrets** - Container orchestration secrets

### Option 3: Certificate-Based Authentication
- Use X.509 certificates instead of passwords where supported
- Eliminates password storage entirely

### Option 4: SSO/LDAP Integration
- Configure iDRAC for LDAP/Active Directory authentication
- Centralized credential management
- No local password storage needed

---

## 🔒 General Security Recommendations

### File Permissions
```bash
# Secure your configuration files
chmod 600 config.json        # Only owner can read/write
chmod 600 .fleet_key         # Only owner can read/write
chmod 600 fleet_servers.json # Only owner can read/write
```

### Access Control
- **Restrict shell access** to the system running the MCP server
- **Use dedicated service accounts** with minimal privileges
- **Enable iDRAC audit logging** to track access
- **Implement network segmentation** - restrict access to iDRAC management network

### Credential Hygiene
- **Rotate passwords regularly** (every 90 days minimum)
- **Use strong passwords** (16+ characters, mixed case, numbers, symbols)
- **Never reuse passwords** across systems
- **Enable multi-factor authentication** on iDRAC if available
- **Use least-privilege accounts** - avoid using root if possible

### Network Security
- **Use HTTPS only** for iDRAC connections
- **Enable SSL verification** in production (`ssl_verify: true`)
- **Use VPN or bastion hosts** for remote access
- **Firewall iDRAC interfaces** - restrict to management networks only

### Monitoring
- **Enable iDRAC logging** and forward to SIEM
- **Monitor for failed authentication attempts**
- **Alert on configuration changes**
- **Regular security audits** of access logs

---

## 🚨 Emergency Response

### If credentials are compromised:

1. **Immediately change all affected passwords** on iDRAC systems
2. **Review iDRAC audit logs** for unauthorized access
3. **Check for unauthorized configuration changes**
4. **Rotate encryption keys** if using fleet management
5. **Investigate the compromise** - how did it happen?

### If sensitive files were committed to git:

```bash
# Remove files from git history (DESTRUCTIVE - coordinate with team)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch config.json fleet_servers.json .fleet_key' \
  --prune-empty --tag-name-filter cat -- --all

# Force push (WARNING: rewrites history)
git push origin --force --all

# All team members must re-clone the repository
```

**Then:**
1. Change all passwords that were exposed
2. Rotate any encryption keys
3. Audit recent iDRAC activity for suspicious access

---

## 📋 Security Checklist

Before deploying to production:

- [ ] Credentials are NOT in version control
- [ ] Sensitive files have restrictive permissions (600)
- [ ] Using HTTPS for all iDRAC connections
- [ ] SSL verification is enabled (or documented why not)
- [ ] Passwords meet complexity requirements
- [ ] Password rotation schedule is defined
- [ ] iDRAC audit logging is enabled
- [ ] Access to management network is restricted
- [ ] Monitoring/alerting is configured
- [ ] Incident response procedure is documented
- [ ] Consider external secret management for production

---

## 🎯 Summary

| Method | Security | Use Case | Recommendation |
|--------|----------|----------|----------------|
| `config.json` | ⚠️ LOW | Development/Testing | Local testing only |
| Encrypted Fleet | 🔶 MEDIUM | Small deployments | Better, but still limited |
| External Secrets | ✅ HIGH | Production | **Recommended** |

**Remember:** The secure fleet CLI is better than plain text, but it's not a substitute for proper enterprise secret management. Choose the method appropriate for your risk tolerance and environment.

---

**Security is everyone's responsibility. Understand your risks and implement appropriate controls.**
