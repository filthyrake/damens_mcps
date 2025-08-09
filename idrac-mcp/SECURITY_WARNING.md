# 🔐 SECURITY WARNING - Password Storage

## ⚠️ CRITICAL SECURITY ISSUE RESOLVED

**The previous version of the fleet management system stored passwords in plain text JSON files. This has been fixed.**

### What Was Wrong
- Passwords were stored in plain text in `fleet_servers.json`
- This file could accidentally be committed to version control
- Anyone with access to the file could see all server passwords

### What's Fixed
- ✅ Passwords are now encrypted using Fernet (AES-128-CBC)
- ✅ Encryption key is stored separately in `.fleet_key`
- ✅ Both files are now in `.gitignore`
- ✅ Secure CLI prompts for passwords (no command line exposure)
- ✅ Master password protection for the encryption key

### Files Now Protected
- `fleet_servers.json` - Encrypted server configurations
- `.fleet_key` - Encryption key (keep this secure!)
- `.env` files - Environment variables

### How to Use the Secure Version

1. **Install the cryptography dependency:**
   ```bash
   pip install cryptography
   ```

2. **Use the secure CLI:**
   ```bash
   python secure_fleet_cli.py init
   python secure_fleet_cli.py add server_name host username
   ```

3. **The password will be prompted securely (hidden input)**

### Security Best Practices

1. **Keep the encryption key secure** - If lost, you'll need to reconfigure all servers
2. **Never commit `.fleet_key` or `fleet_servers.json` to version control**
3. **Use strong master passwords** for the encryption key
4. **Regularly rotate iDRAC passwords**
5. **Use HTTPS for all iDRAC connections**
6. **Enable SSL verification when possible**

### Migration from Insecure Version

If you had the old insecure `fleet_servers.json` file:

1. **DELETE IT IMMEDIATELY** - It contains plain text passwords
2. **Change all iDRAC passwords** that were stored in it
3. **Use the new secure CLI** to reconfigure servers
4. **Verify the old file is not in git history**

### Commands to Check Security

```bash
# Check what's in .gitignore
grep -E "(fleet_servers\.json|\.fleet_key|\.env)" .gitignore

# Check if any sensitive files are tracked
git status --porcelain | grep -E "(fleet_servers\.json|\.fleet_key|\.env)"

# View security info
python secure_fleet_cli.py security-info
```

### Emergency Response

If you accidentally committed passwords:

1. **Immediately change all affected passwords**
2. **Remove files from git history:**
   ```bash
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch fleet_servers.json .fleet_key' \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push to remove from remote:**
   ```bash
   git push origin --force --all
   ```

---

**Remember: Security is everyone's responsibility. Always use the secure tools and never store passwords in plain text!**
