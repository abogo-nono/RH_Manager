#!/usr/bin/env python3
"""
Test script to verify Employee module functionality
"""

import requests
from bs4 import BeautifulSoup
import re

def test_employee_module():
    base_url = 'http://127.0.0.1:5001'
    session = requests.Session()
    
    print("Testing Employee Module Functionality")
    print("=" * 50)
    
    # Step 1: Login
    print("\n1. Login Test...")
    try:
        login_page = session.get(f'{base_url}/login')
        if login_page.status_code == 200:
            print("✅ Login page accessible")
            
            login_data = {
                'nom_utilisateur': 'admin',
                'mot_de_passe': 'admin123'
            }
            login_response = session.post(f'{base_url}/login', data=login_data)
            
            if login_response.status_code == 302 or 'dashboard' in login_response.url:
                print("✅ Login successful")
            else:
                print("❌ Login failed")
                return
        else:
            print("❌ Cannot access login page")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: Test Employee List
    print("\n2. Employee List Test...")
    try:
        emp_list = session.get(f'{base_url}/employes')
        if emp_list.status_code == 200:
            print("✅ Employee list page accessible")
            
            # Check for form presence
            if 'addEmployeModal' in emp_list.text:
                print("✅ Add employee form detected")
            else:
                print("⚠️ Add employee form not found")
                
            # Check for basic content
            if 'employé' in emp_list.text.lower() or 'employee' in emp_list.text.lower():
                print("✅ Page contains employee content")
            else:
                print("⚠️ Employee content may be missing")
                
        else:
            print(f"❌ Employee list failed: {emp_list.status_code}")
    except Exception as e:
        print(f"❌ Employee list error: {e}")
    
    # Step 3: Test Employee Detail (if employees exist)
    print("\n3. Employee Detail Test...")
    try:
        emp_detail = session.get(f'{base_url}/employes/1')
        if emp_detail.status_code == 200:
            print("✅ Employee detail page accessible")
            
            # Check for document form
            if 'document_form' in emp_detail.text or 'addDocumentModal' in emp_detail.text:
                print("✅ Document form detected")
            else:
                print("⚠️ Document form not found")
                
        elif emp_detail.status_code == 404:
            print("⚠️ No employee with ID 1 exists (this is normal if DB is empty)")
        else:
            print(f"❌ Employee detail failed: {emp_detail.status_code}")
    except Exception as e:
        print(f"❌ Employee detail error: {e}")
    
    # Step 4: Test Absences
    print("\n4. Absences Test...")
    try:
        abs_list = session.get(f'{base_url}/absences')
        if abs_list.status_code == 200:
            print("✅ Absences list page accessible")
            
            # Check for absence form
            if 'addAbsenceModal' in abs_list.text:
                print("✅ Add absence form detected")
            else:
                print("⚠️ Add absence form not found")
                
        else:
            print(f"❌ Absences list failed: {abs_list.status_code}")
    except Exception as e:
        print(f"❌ Absences error: {e}")
    
    # Step 5: Test Export Functions
    print("\n5. Export Functions Test...")
    try:
        exports = [
            ('/employes/export/excel', 'Employee Excel'),
            ('/employes/export/pdf', 'Employee PDF'),
            ('/absences/export/excel', 'Absence Excel'),
            ('/absences/export/pdf', 'Absence PDF')
        ]
        
        for route, name in exports:
            try:
                response = session.get(f'{base_url}{route}')
                if response.status_code == 200:
                    print(f"✅ {name} export works")
                elif response.status_code == 302:
                    print(f"⚠️ {name} export redirected (may need auth)")
                else:
                    print(f"❌ {name} export failed: {response.status_code}")
            except Exception as e:
                print(f"❌ {name} export error: {e}")
                
    except Exception as e:
        print(f"❌ Export test error: {e}")
    
    # Step 6: Test JSON endpoints
    print("\n6. JSON Endpoints Test...")
    try:
        # Test employee search
        search_response = session.get(f'{base_url}/employes/search?term=test')
        if search_response.status_code == 200:
            try:
                search_data = search_response.json()
                print("✅ Employee search JSON endpoint works")
                print(f"   Search returned: {search_data}")
            except:
                print("⚠️ Employee search returned non-JSON response")
        else:
            print(f"❌ Employee search failed: {search_response.status_code}")
            
        # Test employee JSON (if employee exists)
        json_response = session.get(f'{base_url}/employes/1/json')
        if json_response.status_code == 200:
            try:
                json_data = json_response.json()
                print("✅ Employee JSON endpoint works")
            except:
                print("⚠️ Employee JSON returned non-JSON response")
        elif json_response.status_code == 404:
            print("⚠️ Employee ID 1 not found (normal if DB is empty)")
        else:
            print(f"❌ Employee JSON failed: {json_response.status_code}")
            
    except Exception as e:
        print(f"❌ JSON endpoints error: {e}")
    
    print("\n" + "=" * 50)
    print("Employee Module Test Complete")
    print("=" * 50)

if __name__ == "__main__":
    test_employee_module()
