#!/usr/bin/env python3
"""Test script to identify import issues"""

print("Starting import tests...")

try:
    print("1. Testing basic Flask...")
    from flask import Flask
    print("   ✅ Flask imported successfully")
except Exception as e:
    print(f"   ❌ Flask import failed: {e}")
    exit(1)

try:
    print("2. Testing config...")
    from config import Config
    print("   ✅ Config imported successfully")
except Exception as e:
    print(f"   ❌ Config import failed: {e}")
    exit(1)

try:
    print("3. Testing app.models...")
    from app.models import Employee, Conge
    print("   ✅ Models imported successfully")
except Exception as e:
    print(f"   ❌ Models import failed: {e}")
    exit(1)

try:
    print("4. Testing app.forms...")
    from app.forms import ModifierMonCompteForm
    print("   ✅ Forms imported successfully")
except Exception as e:
    print(f"   ❌ Forms import failed: {e}")
    exit(1)

try:
    print("5. Testing app.__init__...")
    from app import create_app
    print("   ✅ App factory imported successfully")
except Exception as e:
    print(f"   ❌ App factory import failed: {e}")
    exit(1)

try:
    print("6. Testing app creation...")
    app = create_app()
    print("   ✅ App created successfully")
except Exception as e:
    print(f"   ❌ App creation failed: {e}")
    exit(1)

print("All tests passed! ✅")
