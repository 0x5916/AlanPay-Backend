#!/usr/bin/env python3
"""
Verification script to test the generated keys.
"""

import os
from cryptography.fernet import Fernet
import jwt
from datetime import datetime, timedelta


def test_fernet_key():
    """Test the Fernet key from environment"""
    print("Testing Fernet Key...")

    fernet_key = input("Enter your Fernet key: ")

    if fernet_key is None:
        return

    try:
        # Initialize Fernet
        f = Fernet(fernet_key.encode())
        
        # Test encryption/decryption
        test_data = {"user_id": 123, "username": "test_user"}
        test_json = str(test_data).encode()
        
        # Encrypt
        encrypted = f.encrypt(test_json)
        print(f"Encryption successful: {len(encrypted)} bytes")
        
        # Decrypt
        decrypted = f.decrypt(encrypted)
        print(f"Decryption successful: {decrypted.decode()}")
        
        return True
        
    except Exception as e:
        print(f"Fernet test failed: {e}")
        return False

def test_jwt_key():
    """Test the JWT key"""
    print("\nTesting JWT Key...")
    
    jwt_secret = input("Enter your JWT secret: ")
    
    try:
        # Create a test payload
        payload = {
            "sub": "test_user",
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow()
        }
        
        # Encode JWT
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")
        print(f"JWT encoding successful: {len(token)} characters")
        
        # Decode JWT
        decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        print(f"JWT decoding successful: user = {decoded.get('sub')}")
        
        return True
        
    except Exception as e:
        print(f"JWT test failed: {e}")
        return False

def test_combined_encryption():
    """Test the combined encryption approach used in your app"""
    print("\nTesting Combined Encryption (like your app)...")

    fernet_key = os.getenv("FERNET_KEY")
    jwt_secret = os.getenv("JWT_SECRET")

    if fernet_key is None or jwt_secret is None:
        print("Missing keys in environment")
        return

    try:
        import json
        
        # Initialize Fernet
        f = Fernet(fernet_key.encode())
        
        # Step 1: Create payload like your app does
        payload = {
            "sub": "test_user",
            "exp": (datetime.utcnow() + timedelta(minutes=30)).timestamp(),
            "iat": datetime.utcnow().timestamp()
        }
        
        # Step 2: Encrypt the payload
        payload_bytes = json.dumps(payload).encode()
        encrypted_payload = f.encrypt(payload_bytes).decode()
        
        # Step 3: Create JWT with encrypted payload
        token_payload = {"encrypted_data": encrypted_payload}
        token = jwt.encode(token_payload, jwt_secret, algorithm="HS256")
        
        print(f"Combined encryption successful: {len(token)} character token")
        
        # Step 4: Decode and decrypt (like your app does)
        token_data = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        decrypted_bytes = f.decrypt(token_data["encrypted_data"].encode())
        final_payload = json.loads(decrypted_bytes.decode())
        
        print(f"Combined decryption successful: user = {final_payload.get('sub')}")
        
        return True
        
    except Exception as e:
        print(f"Combined encryption test failed: {e}")
        return False

def main():
    print("🧪 Key Verification Tests")
    print("=" * 40)
    
    tests = [
        test_fernet_key(),
        test_jwt_key(),
        test_combined_encryption()
    ]
    
    print(f"\nResults: {sum(tests)}/{len(tests)} tests passed")
    
    if all(tests):
        print("All tests passed! Your keys are working correctly.")
    else:
        print("Some tests failed. Check your key configuration.")

if __name__ == "__main__":
    main()
