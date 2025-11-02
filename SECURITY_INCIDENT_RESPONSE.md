# Security Incident Response Guide

## Purpose

This document provides guidance on how to respond to security incidents, particularly when credentials or sensitive information have been accidentally committed to the repository.

## Incident Types

### 1. Credentials Committed to Repository

When API keys, passwords, or other credentials are accidentally committed to git:

#### Immediate Actions (Within 1 Hour)

1. **Rotate Compromised Credentials Immediately**
   - Change the exposed password on the target system
   - Revoke and regenerate the exposed API key
   - Update credentials in your local `.env` file
   - **DO NOT** commit new credentials to git

2. **Notify Team Members**
   - Alert repository maintainers via Slack/email
   - Document which credentials were exposed
   - Document the time window of exposure

3. **Assess Impact**
   - Check audit logs for unauthorized access
   - Review recent API calls for suspicious activity
   - Determine if data was accessed or modified

#### Short-term Remediation (Within 24 Hours)

1. **Remove Credentials from Git History**

   **Option A: Using BFG Repo-Cleaner (Recommended)**
   ```bash
   # Install BFG
   # macOS: brew install bfg
   # Linux: Download from https://rtyley.github.io/bfg-repo-cleaner/
   
   # Clone a fresh copy of your repository
   git clone --mirror https://github.com/YOUR_ORG/YOUR_REPO.git
   cd YOUR_REPO.git
   
   # Remove .env files from history
   bfg --delete-files .env
   
   # Clean up
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   
   # Force push (requires admin access)
   git push --force
   ```

   **Option B: Using git filter-repo (Alternative)**
   ```bash
   # Install git-filter-repo
   pip install git-filter-repo
   
   # Clone a fresh copy of your repository
   git clone https://github.com/YOUR_ORG/YOUR_REPO.git
   cd YOUR_REPO
   
   # Remove .env files from all history
   git filter-repo --invert-paths --path pfsense-mcp/.env
   
   # Force push (requires admin access)
   git push --force --all
   git push --force --tags
   ```

   **Option C: Using git filter-branch (Fallback)**
   ```bash
   # Clone a fresh copy of your repository
   git clone https://github.com/YOUR_ORG/YOUR_REPO.git
   cd YOUR_REPO
   
   # Remove .env from history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch pfsense-mcp/.env" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Clean up
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   
   # Force push (requires admin access)
   git push --force --all
   git push --force --tags
   ```

2. **Verify Credentials Are Removed**
   ```bash
   # Check that file no longer appears in history
   git log --all --full-history -- pfsense-mcp/.env
   
   # Search for specific credential patterns
   git log --all -S "your-api-key-pattern" --oneline
   
   # Use git-secrets or similar to scan
   git secrets --scan-history
   ```

3. **Update All Active Clones**
   - Notify all developers to delete their local clones
   - Have them re-clone from the cleaned repository
   - Ensure no one pushes old branches that contain credentials

#### Long-term Prevention (Within 1 Week)

1. **Enhance Pre-commit Hooks**
   - Ensure `detect-secrets` is installed and configured
   - Add custom patterns for your specific credential formats
   - Test hooks to verify they catch credentials

2. **Update Documentation**
   - Document the incident in security logs
   - Update security policies based on lessons learned
   - Create training materials for team members

3. **Implement Additional Controls**
   - Enable GitHub secret scanning (if available)
   - Set up branch protection rules
   - Require code review for all changes
   - Implement secret scanning in CI/CD pipeline

## Pre-commit Hook Setup

Ensure all developers have pre-commit hooks installed:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

## Credential Rotation Checklist

When rotating credentials after exposure:

### pfSense API Keys
- [ ] Log into pfSense web interface
- [ ] Navigate to System → API
- [ ] Locate the exposed API key
- [ ] Click "Revoke" or "Delete"
- [ ] Generate new API key
- [ ] Update local `.env` file with new key
- [ ] Verify new key works
- [ ] Document key rotation in security log

### pfSense Passwords
- [ ] Log into pfSense web interface
- [ ] Navigate to System → User Manager
- [ ] Select the affected user account
- [ ] Click "Edit"
- [ ] Change password (use strong password generator)
- [ ] Update local `.env` file with new password
- [ ] Verify new password works
- [ ] Document password change in security log

### TrueNAS API Keys
- [ ] Log into TrueNAS web interface
- [ ] Navigate to Account → API Keys
- [ ] Delete the exposed API key
- [ ] Create new API key
- [ ] Update local `.env` file
- [ ] Test new key
- [ ] Document rotation

### iDRAC Passwords
- [ ] Access iDRAC web interface
- [ ] Navigate to iDRAC Settings → Users
- [ ] Select the user account
- [ ] Change password
- [ ] Update local `config.json` file
- [ ] Test new credentials
- [ ] Document change

### Proxmox Credentials
- [ ] Access Proxmox web interface
- [ ] Navigate to Datacenter → Permissions → Users
- [ ] Select user and change password/token
- [ ] Update local `config.json` file
- [ ] Test new credentials
- [ ] Document rotation

## Monitoring for Compromised Credentials

After an exposure incident, monitor for:

1. **Unusual API Activity**
   - Failed authentication attempts
   - API calls from unknown IP addresses
   - Unusual patterns or volumes of requests
   - Access to sensitive endpoints

2. **Configuration Changes**
   - Unexpected firewall rule modifications
   - Service configuration changes
   - User account creations or modifications
   - Permission changes

3. **System Logs**
   - Review authentication logs
   - Check for privilege escalation attempts
   - Look for data exfiltration patterns
   - Monitor for lateral movement

## Reporting Security Incidents

### Internal Reporting
1. Create incident ticket in issue tracker
2. Document timeline of events
3. List affected systems and credentials
4. Describe remediation actions taken
5. Identify root cause
6. Propose preventive measures

### External Reporting (if required)
- Notify affected parties if data breach occurred
- Report to regulatory bodies if required by law
- Coordinate disclosure timeline
- Prepare public statement if necessary

## Post-Incident Review

Within 1 week after incident resolution:

1. **Conduct Retrospective**
   - What happened?
   - How was it detected?
   - What was the impact?
   - How long were credentials exposed?
   - Were any unauthorized actions taken?

2. **Root Cause Analysis**
   - Why were credentials committed?
   - Why didn't pre-commit hooks catch it?
   - What process failures occurred?
   - What training gaps exist?

3. **Implement Improvements**
   - Update security procedures
   - Enhance technical controls
   - Provide team training
   - Update documentation

4. **Document Lessons Learned**
   - Update this guide based on experience
   - Share knowledge with team
   - Create runbook for similar incidents

## Contact Information

### Security Team
- **Primary Contact**: Repository Maintainers (see SECURITY.md)
- **Email**: Contact information available in repository SECURITY.md
- **Slack/Discord**: Internal team communication channels

### Emergency Contacts
- **After Hours**: Follow organization's on-call procedures
- **Escalation**: Contact repository owner or organization security team

## Additional Resources

- [SECURITY.md](./SECURITY.md) - Security best practices
- [SECURITY_SUMMARY.md](./SECURITY_SUMMARY.md) - Security overview
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-filter-repo](https://github.com/newren/git-filter-repo)

## Version History

- **v1.0.0** (2025-11-02): Initial incident response guide created following security review and hardening

---

**Remember**: The best way to handle a security incident is to prevent it from happening in the first place. Use pre-commit hooks, code review, and proper credential management practices.
