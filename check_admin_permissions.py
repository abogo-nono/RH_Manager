#!/usr/bin/env python3
"""
Script to check admin user permissions in the database.
"""
import os
import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.models import Utilisateur, Role, Permission

def check_admin_permissions():
    """Check if admin user has the required permissions."""
    app = create_app()
    
    with app.app_context():
        # Find the admin user
        admin_user = Utilisateur.query.filter_by(nom_utilisateur='admin').first()
        if not admin_user:
            print("❌ Admin user not found!")
            return False
        
        print(f"✅ Admin user found: {admin_user.nom_utilisateur}")
        print(f"   Email: {admin_user.email}")
        print(f"   Active: {admin_user.actif}")
        
        # Check admin user's role
        if admin_user.role:
            print(f"   Role: {admin_user.role.nom}")
            print(f"   Role permissions:")
            for perm in admin_user.role.permissions:
                print(f"     - {perm.nom} (code: {perm.code})")
                
            # Check for 'rapports' permission specifically
            has_rapports = any(perm.code == 'rapports' for perm in admin_user.role.permissions)
            print(f"   Has 'rapports' permission: {'✅' if has_rapports else '❌'}")
        else:
            print("   ❌ No role assigned!")
            has_rapports = False
        
        # List all available roles and permissions
        print("\n📋 All available roles:")
        roles = Role.query.all()
        for role in roles:
            print(f"   - {role.nom}")
            for perm in role.permissions:
                print(f"     * {perm.nom} (code: {perm.code})")
        
        print("\n📋 All available permissions:")
        permissions = Permission.query.all()
        for perm in permissions:
            print(f"   - {perm.nom} (code: {perm.code})")
        
        return has_rapports

if __name__ == "__main__":
    try:
        has_required_perms = check_admin_permissions()
        if not has_required_perms:
            print("\n❌ Admin user doesn't have required permissions!")
            sys.exit(1)
        else:
            print("\n✅ Admin user has all required permissions!")
    except Exception as e:
        print(f"❌ Error checking permissions: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
