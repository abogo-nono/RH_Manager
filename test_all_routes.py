#!/usr/bin/env python3
"""
Test all main application routes with authentication
"""

import sys
sys.path.insert(0, '.')

from app import create_app
from app.models import Utilisateur

def test_all_routes():
    """Test all main routes with authentication"""
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            # Test login
            login_response = client.post('/login', data={
                'nom_utilisateur': 'admin',
                'mot_de_passe': 'admin123'
            }, follow_redirects=True)
            
            if login_response.status_code != 200:
                print(f"❌ Login failed: {login_response.status_code}")
                return
            
            print("✅ Login successful")
            
            # Test main routes
            test_routes = [
                ('/', 'Dashboard'),
                ('/dashboard', 'Dashboard Alt'),
                ('/dashboard/reports', 'Reports'),
                ('/dashboard/advanced', 'Advanced Dashboard'),
                ('/employes', 'Employees'),
                ('/conges-temps', 'Conges Temps'),
                ('/evaluations', 'Evaluations'),
                ('/paie', 'Paie'),
                ('/recrutement', 'Recrutement'),
                ('/parametres', 'Parametres'),
                ('/absences', 'Absences'),
                ('/conges-temps/presences', 'Presences'),
                ('/conges-temps/conges', 'Conges'),
                ('/conges-temps/absences', 'Absences List'),
                ('/evaluations/list', 'Evaluations List'),
                ('/paie/bulletins', 'Bulletins'),
                ('/parametres/utilisateurs', 'Utilisateurs'),
                ('/parametres/roles', 'Roles'),
                ('/parametres/permissions', 'Permissions'),
                ('/parametres/paie', 'Parametres Paie'),
                ('/parametres/conges', 'Parametres Conges'),
                ('/parametres/presences', 'Parametres Presences'),
            ]
            
            print("\n🔍 Testing All Routes:")
            print("=" * 60)
            
            success_count = 0
            redirect_count = 0
            error_count = 0
            
            for route_path, route_name in test_routes:
                try:
                    response = client.get(route_path)
                    if response.status_code == 200:
                        print(f"✅ {route_name:<25} {route_path:<30} -> {response.status_code}")
                        success_count += 1
                    elif response.status_code == 302:
                        print(f"🔄 {route_name:<25} {route_path:<30} -> {response.status_code} (Redirect)")
                        redirect_count += 1
                    elif response.status_code == 403:
                        print(f"🚫 {route_name:<25} {route_path:<30} -> {response.status_code} (Forbidden)")
                        error_count += 1
                    elif response.status_code == 404:
                        print(f"❌ {route_name:<25} {route_path:<30} -> {response.status_code} (Not Found)")
                        error_count += 1
                    else:
                        print(f"⚠️  {route_name:<25} {route_path:<30} -> {response.status_code}")
                        error_count += 1
                except Exception as e:
                    print(f"💥 {route_name:<25} {route_path:<30} -> ERROR: {str(e)}")
                    error_count += 1
            
            print("\n" + "=" * 60)
            print("📊 ROUTE TESTING SUMMARY")
            print("=" * 60)
            print(f"✅ Successful (200): {success_count}")
            print(f"🔄 Redirects (302): {redirect_count}")
            print(f"❌ Errors (4xx/5xx): {error_count}")
            print(f"📝 Total routes tested: {len(test_routes)}")
            
            if error_count == 0:
                print("\n🎉 ALL ROUTES WORKING CORRECTLY!")
            else:
                print(f"\n⚠️  {error_count} routes need attention")

if __name__ == "__main__":
    test_all_routes()
