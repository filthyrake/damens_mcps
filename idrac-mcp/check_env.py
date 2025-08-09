#!/usr/bin/env python3
"""Check what values are being read from the .env file."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Environment Variables Check")
print("=" * 40)

# Check iDRAC settings
idrac_host = os.getenv("IDRAC_HOST")
idrac_port = os.getenv("IDRAC_PORT")
idrac_protocol = os.getenv("IDRAC_PROTOCOL")
idrac_username = os.getenv("IDRAC_USERNAME")
idrac_password = os.getenv("IDRAC_PASSWORD")
idrac_ssl_verify = os.getenv("IDRAC_SSL_VERIFY")

print(f"IDRAC_HOST: {idrac_host}")
print(f"IDRAC_PORT: {idrac_port}")
print(f"IDRAC_PROTOCOL: {idrac_protocol}")
print(f"IDRAC_USERNAME: {idrac_username}")
print(f"IDRAC_PASSWORD: {'*' * len(idrac_password) if idrac_password else 'NOT SET'}")
print(f"IDRAC_SSL_VERIFY: {idrac_ssl_verify}")

print("\n📋 Configuration Summary:")
if idrac_host and idrac_host != "192.168.1.100":
    print(f"✅ Custom iDRAC host: {idrac_host}")
else:
    print(f"⚠️  Using default iDRAC host: {idrac_host}")

if idrac_password and idrac_password != "your-password":
    print("✅ Custom password set")
else:
    print("⚠️  Using default/placeholder password")

print(f"\n🎯 Full URL: {idrac_protocol}://{idrac_host}:{idrac_port}")

print("\n💡 To update your iDRAC settings:")
print("1. Edit the .env file")
print("2. Update IDRAC_HOST with your real server IP")
print("3. Update IDRAC_PASSWORD with your real password")
print("4. Save the file and run the test again")
