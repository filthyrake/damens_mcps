# Security Fix: Password-Based Encryption for Fleet Management

## Vulnerability Fixed
**HIGH Severity**: Encryption key stored unencrypted on disk

### Original Issue
The iDRAC fleet management encryption key (`.fleet_key`) was stored as plain bytes on disk without password protection. If an attacker gained filesystem access, they could decrypt all stored passwords, completely defeating the purpose of encryption.

**Location**: `idrac-mcp/src/secure_multi_server_manager.py` (lines 41-71)

**Impact**: 
- If attacker gains file system access, can decrypt all passwords
- Encryption provided false sense of security
- Key file could be stolen
- No additional protection beyond file permissions

## Solution Implemented

### Password-Based Key Derivation
Replaced persistent key file with password-based key derivation using industry-standard cryptography:

1. **PBKDF2-SHA256** - Standard key derivation function
2. **480,000 iterations** - OWASP 2023 recommendation
3. **Unique salt per config** - Stored with encrypted data (safe without password)
4. **No persistent key** - Encryption key never written to disk

### Security Improvements

**Before (v1.0)**:
```python
# INSECURE: Key written to disk unencrypted
key = Fernet.generate_key()
with open('.fleet_key', 'wb') as f:
    f.write(key)  # ❌ Vulnerable
```

**After (v2.0)**:
```python
# SECURE: Key derived from password each time
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=480000,  # OWASP 2023 recommendation
)
key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
# ✅ Key never written to disk
```

### Key Features
- ✅ **No persistent key on disk** - Attacker needs password, not just file access
- ✅ **Strong key derivation** - 480,000 PBKDF2 iterations (OWASP 2023)
- ✅ **Password required per session** - Via CLI flag, env var, or interactive prompt
- ✅ **Backward compatible** - Legacy `.fleet_key` files work with warnings
- ✅ **Salt per config** - Prevents rainbow table attacks
- ✅ **Clean migration path** - Clear instructions in SECURITY.md

## Testing

### Test Coverage
Created comprehensive test suite (`tests/test_secure_encryption.py`):

1. ✅ Initialization with password
2. ✅ Password mismatch handling  
3. ✅ Salt persistence
4. ✅ No key file created
5. ✅ Backward compatibility with legacy keys
6. ✅ Password encryption/decryption
7. ✅ Config version 2.0 format
8. ✅ Empty password validation
9. ✅ Multiple sessions with same password
10. ✅ Key derivation iterations verification
11. ✅ Salt uniqueness

**Result**: All 11 tests passing ✅

### Security Scanning
- ✅ CodeQL security scanner: 0 alerts
- ✅ No security vulnerabilities detected
- ✅ Code review feedback addressed

### Manual Testing
- ✅ CLI initialization works correctly
- ✅ Password prompting works (interactive, flag, env var)
- ✅ No `.fleet_key` file created
- ✅ Config format is version 2.0 with salt
- ✅ Legacy key backward compatibility verified
- ✅ Security warnings displayed for legacy keys

## Usage

### New Installations
```bash
# Set password via environment variable (recommended)
export IDRAC_FLEET_PASSWORD="your_secure_password"
python secure_fleet_cli.py init

# Or provide via CLI flag
python secure_fleet_cli.py --password "your_secure_password" init

# Or will prompt interactively
python secure_fleet_cli.py init
# (prompts for password)
```

### Migrating from v1.0
Users with existing `.fleet_key` files have two options:

**Option 1**: Continue using legacy key (less secure)
- CLI automatically detects and uses existing `.fleet_key`
- Security warning displayed on each use
- No action needed

**Option 2**: Migrate to password-based encryption (recommended)
```bash
# 1. Remove legacy key
rm .fleet_key

# 2. Re-initialize with password
python secure_fleet_cli.py init

# 3. Re-add servers with new encryption
python secure_fleet_cli.py add server1 192.168.1.100 root
```

## Files Modified

1. **src/secure_multi_server_manager.py**
   - Implemented password-based key derivation
   - Added backward compatibility for legacy keys
   - Improved error handling and validation

2. **secure_fleet_cli.py**
   - Added `--password` flag
   - Support for `IDRAC_FLEET_PASSWORD` env var
   - Updated security-info command

3. **SECURITY.md**
   - Upgraded security level from MEDIUM to HIGH
   - Documented new password-based approach
   - Added migration instructions
   - Updated security recommendations

4. **tests/test_secure_encryption.py** (NEW)
   - Comprehensive test suite for password-based encryption
   - 11 tests covering all functionality

## Security Assessment

### Before This Fix
- **Security Level**: MEDIUM (obfuscation + file permissions)
- **Threat Model**: Vulnerable to anyone with filesystem access
- **Key Protection**: None (key stored in plain text)

### After This Fix
- **Security Level**: HIGH (password-based encryption)
- **Threat Model**: Requires attacker to obtain master password
- **Key Protection**: PBKDF2-SHA256 with 480,000 iterations

### Remaining Considerations
For enterprise deployments, consider:
- External secret management (HashiCorp Vault, AWS Secrets Manager)
- Hardware security modules (HSM)
- Multi-factor authentication
- Certificate-based authentication

Documentation updated to reflect these options in SECURITY.md.

## Conclusion

This fix addresses the HIGH severity security vulnerability by eliminating the persistent encryption key file. The new password-based approach:

1. ✅ Removes the vulnerability (no key on disk)
2. ✅ Maintains usability (password via env var)
3. ✅ Backward compatible (legacy keys still work)
4. ✅ Well-tested (11 comprehensive tests)
5. ✅ Properly documented (SECURITY.md updated)
6. ✅ Security-scanned (0 CodeQL alerts)

The solution follows industry best practices (OWASP recommendations) and provides a clear migration path for existing users.
