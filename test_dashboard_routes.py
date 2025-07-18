#!/usr/bin/env python3
"""
Test dashboard routes accessibility after permission seeding.
"""
import os
import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from app import create_app
from app.models import Utilisateur

def test_dashboard_routes():
    """Test if dashboard routes are accessible for the admin user."""
    app = create_app()
    
    with app.app_context():
        # Get the admin user
        admin_user = Utilisateur.query.filter_by(nom_utilisateur='admin').first()
        if not admin_user:
            print("❌ Admin user not found!")
            return False
        
        print(f"✅ Testing dashboard routes for user: {admin_user.nom_utilisateur}")
        print(f"   User permissions: {[p.code for p in admin_user.role.permissions] if admin_user.role else 'None'}")
        
        # Test client with the admin user
        client = app.test_client()
        
        # Login as admin
        login_response = client.post('/login', data={
            'nom_utilisateur': 'admin',
            'mot_de_passe': 'admin123'
        }, follow_redirects=True)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed with status {login_response.status_code}")
            return False
        
        print("✅ Login successful")
        
        # Test dashboard routes
        routes_to_test = [
            '/dashboard',
            '/dashboard/reports',
            '/dashboard/advanced'
        ]
        
        all_success = True
        for route in routes_to_test:
            response = client.get(route)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} {route}: {response.status_code}")
            if response.status_code != 200:
                all_success = False
                print(f"      Response data: {response.data.decode()[:200]}...")
        
        return all_success

if __name__ == "__main__":
    try:
        success = test_dashboard_routes()
        if success:
            print("\n✅ All dashboard routes are accessible!")
        else:
            print("\n❌ Some dashboard routes are not accessible!")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error testing routes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
