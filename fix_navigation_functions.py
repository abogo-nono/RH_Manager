#!/usr/bin/env python3
"""
Find all route function names and update navigation links
"""

import re
import os

def find_route_functions():
    """Find all route function names in route files"""
    
    route_files = [
        'app/routes/dashboard.py',
        'app/routes/rh.py',
        'app/routes/conges_temps.py',
        'app/routes/evaluation.py',
        'app/routes/paie.py',
        'app/routes/recrutement.py',
        'app/routes/parametres.py',
    ]
    
    functions = {}
    
    for file_path in route_files:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find blueprint name
        bp_match = re.search(r'(\w+)_bp\s*=\s*Blueprint', content)
        if bp_match:
            bp_name = bp_match.group(1)
            
            # Find route definitions and their functions
            route_pattern = r'@' + bp_name + r'_bp\.route\([\'"]([^\'"]+)[\'"].*?\)\s*(?:@[^\n]*\n)*\s*def\s+(\w+)'
            
            for match in re.finditer(route_pattern, content, re.MULTILINE | re.DOTALL):
                route_path = match.group(1)
                function_name = match.group(2)
                
                if bp_name not in functions:
                    functions[bp_name] = {}
                
                functions[bp_name][route_path] = function_name
                
    return functions

def update_navigation_with_correct_functions():
    """Update navigation links with correct function names"""
    
    functions = find_route_functions()
    
    print("Found route functions:")
    for bp_name, routes in functions.items():
        print(f"\n{bp_name}:")
        for route_path, function_name in routes.items():
            print(f"  {route_path} -> {function_name}")
    
    # Define the correct mappings
    correct_mappings = {
        'dashboard.dashboard': 'dashboard.dashboard',  # Default route
        'rh.list_employees': 'rh.list_employes',
        'conges_temps.index': 'conges_temps.index',
        'evaluation.list_evaluations': 'evaluation.list_evaluations',
        'paie.dashboard': 'paie.dashboard',
        'recrutement.list_candidates': 'recrutement.list_offres',
        'parametres.utilisateurs': 'parametres.utilisateurs',
    }
    
    # Check the actual function names from our findings
    if 'dashboard' in functions:
        dashboard_functions = functions['dashboard']
        if '/' in dashboard_functions:
            correct_mappings['dashboard.dashboard'] = f"dashboard.{dashboard_functions['/']}"
    
    if 'rh' in functions:
        rh_functions = functions['rh']
        if '/employes' in rh_functions:
            correct_mappings['rh.list_employees'] = f"rh.{rh_functions['/employes']}"
    
    if 'conges_temps' in functions:
        conges_functions = functions['conges_temps']
        # Find the main index route
        for route in ['/conges_temps', '/']:
            if route in conges_functions:
                correct_mappings['conges_temps.index'] = f"conges_temps.{conges_functions[route]}"
                break
    
    if 'evaluation' in functions:
        eval_functions = functions['evaluation']
        if '/evaluations' in eval_functions:
            correct_mappings['evaluation.list_evaluations'] = f"evaluation.{eval_functions['/evaluations']}"
    
    if 'paie' in functions:
        paie_functions = functions['paie']
        if '/paie' in paie_functions:
            correct_mappings['paie.dashboard'] = f"paie.{paie_functions['/paie']}"
    
    if 'recrutement' in functions:
        rec_functions = functions['recrutement']
        if '/recrutement' in rec_functions:
            correct_mappings['recrutement.list_candidates'] = f"recrutement.{rec_functions['/recrutement']}"
    
    if 'parametres' in functions:
        param_functions = functions['parametres']
        # Find the main route
        for route in ['/parametres', '/parametres/utilisateurs']:
            if route in param_functions:
                correct_mappings['parametres.utilisateurs'] = f"parametres.{param_functions[route]}"
                break
    
    print("\nCorrect mappings:")
    for old, new in correct_mappings.items():
        print(f"  {old} -> {new}")
    
    # Update navigation template
    base_template_path = 'app/templates/base.html'
    with open(base_template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply corrections
    for old_mapping, new_mapping in correct_mappings.items():
        if old_mapping != new_mapping:
            old_pattern = f"url_for('{old_mapping}')"
            new_pattern = f"url_for('{new_mapping}')"
            content = content.replace(old_pattern, new_pattern)
            print(f"✅ Updated: {old_pattern} -> {new_pattern}")
    
    # Write back
    with open(base_template_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Navigation updated in {base_template_path}")

if __name__ == "__main__":
    update_navigation_with_correct_functions()
