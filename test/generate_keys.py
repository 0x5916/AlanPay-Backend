#!/usr/bin/env python3
"""
Script to generate a secure Fernet key for encryption.
Fernet keys must be 32 url-safe base64-encoded bytes.
"""

from cryptography.fernet import Fernet
import secrets
import base64


def generate_fernet_key():
    """Generate a secure Fernet key"""
    fernet_key = Fernet.generate_key()
    print("=== Fernet Key Generation ===")
    print(f"Generated Key: {fernet_key.decode()}")
    print(f"Key Length: {len(fernet_key)} bytes")
    
    # Verify
    try:
        f = Fernet(fernet_key)
        test_message = b"test"
        encrypted = f.encrypt(test_message)
        decrypted = f.decrypt(encrypted)
        assert decrypted == test_message
        print("ey validation: PASSED")
    except Exception as e:
        print(f"Key validation: FAILED - {e}")
        return None
    
    return fernet_key.decode()

def generate_jwt_secret():
    """Generate a secure JWT secret key"""
    secret_bytes = secrets.token_bytes(64)
    jwt_secret = base64.b64encode(secret_bytes).decode()
    print(f"\n=== JWT Secret Generation ===")
    print(f"Generated JWT Secret: {jwt_secret}")
    print(f"Secret Length: {len(secret_bytes)} bytes")
    return jwt_secret

def main():
    print("Encryption Key Generator for Payment System")
    print("=" * 50)
    
    fernet_key = generate_fernet_key()
    if not fernet_key:
        print("Failed to generate valid Fernet key!")
        return
    
    jwt_secret = generate_jwt_secret()
    
    print(f"\n=== Add to your .env file ===")
    print(f"FERNET_KEY=\"{fernet_key}\"")
    print(f"JWT_SECRET_KEY=\"{jwt_secret}\"")
    
    # Show verification script
    print(f"\n=== Verification (Python) ===")
    print(f"from cryptography.fernet import Fernet")
    print(f"f = Fernet(b'{fernet_key}')")
    print(f"print('Fernet key is valid!')")

if __name__ == "__main__":
    main()
