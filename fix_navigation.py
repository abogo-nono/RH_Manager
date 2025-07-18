#!/usr/bin/env python3
"""
Update navigation links in base.html to use url_for
"""

import re

def update_navigation_links():
    """Update all navigation links to use url_for"""
    
    base_template_path = 'app/templates/base.html'
    
    # Read the current content
    with open(base_template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define replacements
    replacements = [
        (r'href="/"', 'href="{{ url_for(\'dashboard.dashboard\') }}"'),
        (r'href="/employes"', 'href="{{ url_for(\'rh.list_employees\') }}"'),
        (r'href="/conges_temps"', 'href="{{ url_for(\'conges_temps.index\') }}"'),
        (r'href="/evaluations"', 'href="{{ url_for(\'evaluation.list_evaluations\') }}"'),
        (r'href="/paie"', 'href="{{ url_for(\'paie.dashboard\') }}"'),
        (r'href="/recrutement"', 'href="{{ url_for(\'recrutement.list_candidates\') }}"'),
        (r'href="/parametres"', 'href="{{ url_for(\'parametres.utilisateurs\') }}"'),
    ]
    
    # Apply replacements
    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)
        print(f"✅ Updated: {old_pattern} -> {new_pattern}")
    
    # Write back the updated content
    with open(base_template_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Navigation links updated in {base_template_path}")

if __name__ == "__main__":
    update_navigation_links()
