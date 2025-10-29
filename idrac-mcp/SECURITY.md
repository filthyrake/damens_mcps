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

### Security Level: **HIGH** - Secure Password-Based Encryption

The secure fleet CLI (`secure_fleet_cli.py`) provides encrypted password storage using Fernet (AES-128-CBC) with **password-based key derivation** (PBKDF2-SHA256).

### ✅ Security Features
- **Encrypted passwords** using Fernet symmetric encryption (AES-128)
- **Password-based key derivation** using PBKDF2-SHA256 with 480,000 iterations (OWASP 2023 recommendation)
- **No encryption key stored on disk** - key is derived from your master password each time
- **Secure password prompts** (no command-line exposure)
- **Salt stored with encrypted config** (safe - useless without password)
- **Multi-server management** with centralized credential handling
- **Backward compatible** with legacy `.fleet_key` files (with security warnings)

### 📦 Installation

```bash
# Install the cryptography dependency
pip install cryptography click
```

### 🚀 Usage

```bash
# Initialize fleet management (first time - will prompt for master password)
python secure_fleet_cli.py init

# Add a server (master password + server password will be prompted)
python secure_fleet_cli.py add server1 192.168.1.100 root

# List configured servers (master password will be prompted)
python secure_fleet_cli.py list

# Get system info from a server (master password will be prompted)
python secure_fleet_cli.py info server1

# Use environment variable to avoid repeated password prompts
export IDRAC_FLEET_PASSWORD="your-master-password"
python secure_fleet_cli.py list
```

### 🔐 Protected Files
- `fleet_servers.json` - Server configurations with encrypted passwords and salt
- `.fleet_key` - **DEPRECATED** - Legacy encryption key file (no longer created)
- Both are automatically excluded via `.gitignore`

### 🔒 Security Improvements (Version 2.0)

**What changed from v1.0:**

1. **No persistent encryption key** - The encryption key is no longer stored on disk
   - Key is derived from your master password using PBKDF2-SHA256
   - 480,000 iterations (OWASP 2023 recommendation for password-based key derivation)
   - Even if attacker gains file access, passwords cannot be decrypted without master password

2. **Master password required** - You must provide the master password for each session
   - Can be provided via `--password` flag
   - Can be set via `IDRAC_FLEET_PASSWORD` environment variable
   - Will be prompted interactively if not provided

   > ⚠️ **Security Warning:**  
   > Supplying the master password via the `IDRAC_FLEET_PASSWORD` environment variable can expose your credentials to other users on the system (e.g., via `ps aux`, environment dumps, or shell history).  
   > For production environments, prefer interactive prompts or secure CLI flags to minimize the risk of credential leakage.

3. **Salt storage** - Unique salt stored with encrypted config
   - Salt is not sensitive (useless without password)
   - Prevents rainbow table attacks
   - Different salt per configuration file

### ⚠️ Migration from v1.0

If you have an existing `.fleet_key` file (v1.0):

**Option 1: Continue using legacy key (less secure)**
- The CLI will automatically detect and use the existing `.fleet_key`
- You'll see a security warning on each use
- No migration needed, but security is compromised

**Option 2: Migrate to password-based encryption (recommended)**
```bash
# 1. Export your current server configs
python secure_fleet_cli.py list > servers_backup.txt

# 2. Remove the legacy key file
rm .fleet_key

# 3. Initialize with new password-based encryption
python secure_fleet_cli.py init

# 4. Re-add your servers
python secure_fleet_cli.py add server1 192.168.1.100 root
# ... repeat for each server
```

### ✅ Benefits Over Legacy Approach

1. **No key theft** - Attacker needs your master password, not just file access
2. **Password strength matters** - Strong master password = strong encryption
3. **No false security** - Clear that password is the security boundary
4. **Compliance friendly** - Meets many security standards for credential storage

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
| Encrypted Fleet (v2.0) | ✅ HIGH | Production & Development | **Recommended for most users** |
| External Secrets | ✅ VERY HIGH | Enterprise Production | **Best for enterprise** |

**Version 2.0 Update:** The encrypted fleet management now uses password-based key derivation (PBKDF2-SHA256) with no persistent key on disk, significantly improving security over the legacy v1.0 approach.

---

**Security is everyone's responsibility. Understand your risks and implement appropriate controls.**
