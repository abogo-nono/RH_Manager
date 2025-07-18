#!/usr/bin/env python3
"""
Comprehensive audit script for RH_Manager application
Tests all routes, templates, and navigation functionality
"""

import sys
import os
sys.path.insert(0, '.')

from app import create_app
from app.models import Utilisateur, Role, Permission
from flask import url_for
import traceback

def test_routes_and_templates():
    """Test all application routes and templates"""
    app = create_app()
    
    # Test routes that should be accessible
    test_routes = [
        # Dashboard routes
        ('dashboard.dashboard', {}),
        ('dashboard.reports', {}),
        ('dashboard.advanced', {}),
        
        # Auth routes
        ('auth.login', {}),
        ('auth.logout', {}),
        ('auth.reset_password_request', {}),
        
        # RH routes
        ('rh.list_employees', {}),
        ('rh.add_employee', {}),
        
        # Conges temps routes
        ('conges_temps.index', {}),
        ('conges_temps.presences', {}),
        ('conges_temps.absences', {}),
        ('conges_temps.conges', {}),
        
        # Evaluation routes
        ('evaluation.list_evaluations', {}),
        ('evaluation.create_evaluation', {}),
        
        # Paie routes
        ('paie.dashboard', {}),
        ('paie.bulletins', {}),
        ('paie.parametres', {}),
        
        # Recrutement routes
        ('recrutement.list_candidates', {}),
        ('recrutement.add_candidate', {}),
        
        # Parametres routes
        ('parametres.utilisateurs', {}),
        ('parametres.roles', {}),
        ('parametres.permissions', {}),
        ('parametres.paie', {}),
        ('parametres.conges', {}),
        ('parametres.presences', {}),
        
        # Public routes
        ('public.index', {}),
    ]
    
    print("🔍 Testing Route Generation:")
    print("=" * 50)
    
    with app.app_context():
        working_routes = []
        broken_routes = []
        
        for route_name, params in test_routes:
            try:
                url = url_for(route_name, **params)
                working_routes.append((route_name, url))
                print(f"✅ {route_name:<30} -> {url}")
            except Exception as e:
                broken_routes.append((route_name, str(e)))
                print(f"❌ {route_name:<30} -> ERROR: {str(e)}")
        
        print(f"\n📊 Route Generation Summary:")
        print(f"✅ Working routes: {len(working_routes)}")
        print(f"❌ Broken routes: {len(broken_routes)}")
        
        if broken_routes:
            print(f"\n🚨 Broken Routes Details:")
            for route_name, error in broken_routes:
                print(f"  - {route_name}: {error}")
    
    return working_routes, broken_routes

def test_template_existence():
    """Check if all template files exist"""
    print("\n🔍 Testing Template Existence:")
    print("=" * 50)
    
    template_paths = [
        'templates/base.html',
        'templates/dashboard.html',
        'templates/dashboard/reports.html',
        'templates/dashboard/advanced.html',
        'templates/auth/login.html',
        'templates/auth/reset_password_request.html',
        'templates/employes/list.html',
        'templates/employes/add.html',
        'templates/conges_temps/index.html',
        'templates/conges_temps/presences.html',
        'templates/conges_temps/absences.html',
        'templates/conges_temps/conges.html',
        'templates/evaluations/list.html',
        'templates/evaluations/create.html',
        'templates/paie/dashboard.html',
        'templates/paie/bulletins.html',
        'templates/paie/parametres.html',
        'templates/recrutement/list.html',
        'templates/recrutement/add.html',
        'templates/parametres/utilisateurs.html',
        'templates/parametres/roles.html',
        'templates/parametres/permissions.html',
        'templates/parametres/paie.html',
        'templates/parametres/conges.html',
        'templates/parametres/presences.html',
        'templates/public/index.html',
    ]
    
    existing_templates = []
    missing_templates = []
    
    for template_path in template_paths:
        full_path = os.path.join('app', template_path)
        if os.path.exists(full_path):
            existing_templates.append(template_path)
            print(f"✅ {template_path}")
        else:
            missing_templates.append(template_path)
            print(f"❌ {template_path}")
    
    print(f"\n📊 Template Existence Summary:")
    print(f"✅ Existing templates: {len(existing_templates)}")
    print(f"❌ Missing templates: {len(missing_templates)}")
    
    return existing_templates, missing_templates

def test_navigation_links():
    """Test navigation links in base template"""
    print("\n🔍 Testing Navigation Links:")
    print("=" * 50)
    
    base_template_path = 'app/templates/base.html'
    if os.path.exists(base_template_path):
        with open(base_template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for common navigation patterns
        nav_patterns = [
            'href="{{ url_for(\'dashboard.dashboard\') }}"',
            'href="{{ url_for(\'rh.list_employees\') }}"',
            'href="{{ url_for(\'conges_temps.index\') }}"',
            'href="{{ url_for(\'evaluation.list_evaluations\') }}"',
            'href="{{ url_for(\'paie.dashboard\') }}"',
            'href="{{ url_for(\'recrutement.list_candidates\') }}"',
            'href="{{ url_for(\'parametres.utilisateurs\') }}"',
        ]
        
        found_patterns = []
        missing_patterns = []
        
        for pattern in nav_patterns:
            if pattern in content:
                found_patterns.append(pattern)
                print(f"✅ {pattern}")
            else:
                missing_patterns.append(pattern)
                print(f"❌ {pattern}")
        
        print(f"\n📊 Navigation Links Summary:")
        print(f"✅ Found patterns: {len(found_patterns)}")
        print(f"❌ Missing patterns: {len(missing_patterns)}")
    else:
        print("❌ Base template not found!")

def check_blueprint_registration():
    """Check if all blueprints are properly registered"""
    print("\n🔍 Checking Blueprint Registration:")
    print("=" * 50)
    
    app = create_app()
    
    expected_blueprints = [
        'dashboard',
        'auth',
        'rh',
        'conges_temps',
        'evaluation',
        'paie',
        'recrutement',
        'parametres',
        'public'
    ]
    
    registered_blueprints = list(app.blueprints.keys())
    
    print("Registered blueprints:")
    for bp_name in registered_blueprints:
        bp = app.blueprints[bp_name]
        print(f"✅ {bp_name:<20} -> {bp.url_prefix or '/'}")
    
    missing_blueprints = set(expected_blueprints) - set(registered_blueprints)
    extra_blueprints = set(registered_blueprints) - set(expected_blueprints)
    
    if missing_blueprints:
        print(f"\n❌ Missing blueprints: {missing_blueprints}")
    
    if extra_blueprints:
        print(f"\n🔄 Extra blueprints: {extra_blueprints}")
    
    print(f"\n📊 Blueprint Registration Summary:")
    print(f"✅ Expected blueprints found: {len(set(expected_blueprints) & set(registered_blueprints))}")
    print(f"❌ Missing blueprints: {len(missing_blueprints)}")

def check_recent_changes():
    """Check for recent changes mentioned in the conversation"""
    print("\n🔍 Checking Recent Changes:")
    print("=" * 50)
    
    # Check the manually edited paie dashboard template
    paie_dashboard_path = 'app/templates/paie/dashboard.html'
    if os.path.exists(paie_dashboard_path):
        print(f"✅ Paie dashboard template exists: {paie_dashboard_path}")
        # Check for common template issues
        with open(paie_dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for template syntax
        issues = []
        if '{{' in content and '}}' in content:
            print("✅ Template has Jinja2 syntax")
        else:
            issues.append("No Jinja2 syntax found")
            
        if 'extends' in content:
            print("✅ Template extends base template")
        else:
            issues.append("Template doesn't extend base template")
            
        if issues:
            print("❌ Template issues found:")
            for issue in issues:
                print(f"  - {issue}")
    else:
        print(f"❌ Paie dashboard template not found: {paie_dashboard_path}")

def main():
    """Run comprehensive audit"""
    print("🔍 RH_Manager Comprehensive Audit")
    print("=" * 50)
    
    try:
        # Test route generation
        working_routes, broken_routes = test_routes_and_templates()
        
        # Test template existence
        existing_templates, missing_templates = test_template_existence()
        
        # Test navigation links
        test_navigation_links()
        
        # Check blueprint registration
        check_blueprint_registration()
        
        # Check recent changes
        check_recent_changes()
        
        print("\n" + "=" * 50)
        print("📊 FINAL AUDIT SUMMARY")
        print("=" * 50)
        print(f"✅ Working routes: {len(working_routes)}")
        print(f"❌ Broken routes: {len(broken_routes)}")
        print(f"✅ Existing templates: {len(existing_templates)}")
        print(f"❌ Missing templates: {len(missing_templates)}")
        
        if broken_routes or missing_templates:
            print("\n🚨 ISSUES FOUND - Action needed!")
            return 1
        else:
            print("\n✅ ALL CHECKS PASSED!")
            return 0
            
    except Exception as e:
        print(f"\n❌ Audit failed with error: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
