#!/usr/bin/env python3
"""
Create missing templates for RH_Manager application
"""

import os

def create_missing_templates():
    """Create missing templates with basic structure"""
    
    missing_templates = [
        ('templates/employes/add.html', 'employes', 'Ajouter un employé'),
        ('templates/evaluations/create.html', 'evaluations', 'Créer une évaluation'),
        ('templates/paie/parametres.html', 'paie', 'Paramètres de paie'),
        ('templates/recrutement/add.html', 'recrutement', 'Ajouter un candidat'),
        ('templates/parametres/roles.html', 'parametres', 'Gestion des rôles'),
        ('templates/parametres/permissions.html', 'parametres', 'Gestion des permissions'),
        ('templates/public/index.html', 'public', 'Accueil'),
    ]
    
    for template_path, module, title in missing_templates:
        full_path = os.path.join('app', template_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Create template content
        template_content = f"""{{% extends "base.html" %}}

{{% block title %}}{title} - RH Manager{{% endblock %}}

{{% block content %}}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <i class="fas fa-users"></i>
                        {title}
                    </h3>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i>
                        Cette page est en cours de développement.
                    </div>
                    
                    <!-- Add your content here -->
                    
                </div>
            </div>
        </div>
    </div>
</div>
{{% endblock %}}

{{% block scripts %}}
<script>
    // Add your JavaScript here
</script>
{{% endblock %}}
"""
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print(f"✅ Created template: {template_path}")

if __name__ == "__main__":
    create_missing_templates()
    print("\n✅ All missing templates created successfully!")
