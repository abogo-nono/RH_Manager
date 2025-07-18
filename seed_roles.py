from app import create_app, db
from app.models import (
    Permission, Role, Utilisateur, Employee, TypeConge, 
    ParametresPaie, CotisationSociale, ParametrePresence
)
from datetime import datetime, date, time
import random


app = create_app()

def seed_permissions():
    """Créer les permissions de base"""
    permissions = [
        {"nom": "Employés", "code": "employes"},
        {"nom": "Absences et Congés", "code": "absences_conges"},
        {"nom": "Évaluations", "code": "evaluations"},
        {"nom": "Paie", "code": "paie"},
        {"nom": "Recrutement", "code": "recrutement"},
        {"nom": "Paramètres", "code": "parametres"},
        {"nom": "Présences", "code": "presences"},
        {"nom": "Rapports", "code": "rapports"},
        {"nom": "Administration", "code": "administration"},
    ]
    
    created_permissions = []
    for perm in permissions:
        # Évite les doublons
        existing_perm = Permission.query.filter_by(code=perm["code"]).first()
        if not existing_perm:
            new_perm = Permission(nom=perm["nom"], code=perm["code"])
            db.session.add(new_perm)
            created_permissions.append(new_perm)
        else:
            created_permissions.append(existing_perm)
    
    # --- AJOUTER LES NOUVELLES PERMISSIONS POUR LES MODULES ---
    extra_permissions = [
        {"nom": "Voir les évaluations", "code": "voir_evaluations"},
        {"nom": "Créer des évaluations", "code": "creer_evaluations"},
        {"nom": "Modifier les évaluations", "code": "modifier_evaluations"},
        {"nom": "Supprimer les évaluations", "code": "supprimer_evaluations"},
        {"nom": "Administrer les évaluations", "code": "administrer_evaluations"},
        {"nom": "Gestion de la paie", "code": "gestion_paie"},
    ]
    for perm in extra_permissions:
        existing_perm = Permission.query.filter_by(code=perm["code"]).first()
        if not existing_perm:
            new_perm = Permission(nom=perm["nom"], code=perm["code"])
            db.session.add(new_perm)
    db.session.commit()
    print("✅ Permissions supplémentaires ajoutées.")

    # --- AJOUTER CES PERMISSIONS AU RÔLE ADMINISTRATEUR ---
    admin_role = Role.query.filter_by(nom="Administrateur").first()
    if admin_role:
        for perm in extra_permissions:
            permission = Permission.query.filter_by(code=perm["code"]).first()
            if permission and permission not in admin_role.permissions:
                admin_role.permissions.append(permission)
        db.session.commit()
        print("✅ Permissions avancées ajoutées au rôle Administrateur.")
    
    db.session.commit()
    print("✅ Permissions créées avec succès.")
    return created_permissions

def seed_roles(permissions):
    """Créer les rôles avec leurs permissions"""
    roles_data = [
        {
            "nom": "Administrateur",
            "permissions": ["employes", "absences_conges", "evaluations", "paie", 
                          "recrutement", "parametres", "presences", "rapports", "administration"]
        },
        {
            "nom": "Manager RH",
            "permissions": ["employes", "absences_conges", "evaluations", 
                          "recrutement", "presences", "rapports"]
        },
        {
            "nom": "Manager",
            "permissions": ["employes", "absences_conges", "evaluations", "presences"]
        },
        {
            "nom": "Employé",
            "permissions": ["absences_conges", "presences"]
        },
        {
            "nom": "Comptable",
            "permissions": ["paie", "rapports"]
        }
    ]
    
    created_roles = []
    for role_data in roles_data:
        # Évite les doublons
        existing_role = Role.query.filter_by(nom=role_data["nom"]).first()
        if not existing_role:
            new_role = Role(nom=role_data["nom"])
            
            # Ajouter les permissions au rôle
            for perm_code in role_data["permissions"]:
                permission = Permission.query.filter_by(code=perm_code).first()
                if permission:
                    new_role.permissions.append(permission)
            
            db.session.add(new_role)
            created_roles.append(new_role)
        else:
            created_roles.append(existing_role)
    
    db.session.commit()
    print("✅ Rôles créés avec succès.")
    return created_roles

def seed_users(roles):
    """Créer des utilisateurs de test"""
    users_data = [
        {
            "nom_utilisateur": "admin",
            "nom_complet": "Administrateur Système",
            "email": "admin@rhmanager.com",
            "mot_de_passe": "admin123",
            "role": "Administrateur"
        },
        {
            "nom_utilisateur": "rh_manager",
            "nom_complet": "Marie Dupont",
            "email": "marie.dupont@rhmanager.com",
            "mot_de_passe": "rh123",
            "role": "Manager RH"
        },
        {
            "nom_utilisateur": "manager1",
            "nom_complet": "Jean Kouam",
            "email": "jean.kouam@rhmanager.com",
            "mot_de_passe": "manager123",
            "role": "Manager"
        },
        {
            "nom_utilisateur": "employe1",
            "nom_complet": "Alice Mbarga",
            "email": "alice.mbarga@rhmanager.com",
            "mot_de_passe": "employe123",
            "role": "Employé"
        },
        {
            "nom_utilisateur": "comptable",
            "nom_complet": "Paul Nkomo",
            "email": "paul.nkomo@rhmanager.com",
            "mot_de_passe": "compta123",
            "role": "Comptable"
        }
    ]
    
    for user_data in users_data:
        # Évite les doublons
        if not Utilisateur.query.filter_by(nom_utilisateur=user_data["nom_utilisateur"]).first():
            role = Role.query.filter_by(nom=user_data["role"]).first()
            
            new_user = Utilisateur(
                nom_utilisateur=user_data["nom_utilisateur"],
                nom_complet=user_data["nom_complet"],
                email=user_data["email"],
                role=role
            )
            new_user.set_password(user_data["mot_de_passe"])
            
            db.session.add(new_user)
    
    db.session.commit()
    print("✅ Utilisateurs créés avec succès.")

def seed_employees():
    """Créer des employés de test"""
    employees_data = [
        {
            "nom": "Marie Dupont",
            "poste": "Manager RH",
            "departement": "Ressources Humaines",
            "email": "marie.dupont@rhmanager.com",
            "telephone": "+237 698 123 456",
            "type_contrat": "CDI",
            "date_embauche": date(2020, 1, 15),
            "statut": "Actif"
        },
        {
            "nom": "Jean Kouam",
            "poste": "Manager Technique",
            "departement": "IT",
            "email": "jean.kouam@rhmanager.com",
            "telephone": "+237 698 234 567",
            "type_contrat": "CDI",
            "date_embauche": date(2019, 6, 10),
            "statut": "Actif"
        },
        {
            "nom": "Alice Mbarga",
            "poste": "Développeuse Web",
            "departement": "IT",
            "email": "alice.mbarga@rhmanager.com",
            "telephone": "+237 698 345 678",
            "type_contrat": "CDD",
            "date_embauche": date(2022, 3, 20),
            "statut": "Actif"
        },
        {
            "nom": "Paul Nkomo",
            "poste": "Comptable",
            "departement": "Finance",
            "email": "paul.nkomo@rhmanager.com",
            "telephone": "+237 698 456 789",
            "type_contrat": "CDI",
            "date_embauche": date(2021, 8, 5),
            "statut": "Actif"
        },
        {
            "nom": "Sophie Biya",
            "poste": "Assistante Administrative",
            "departement": "Administration",
            "email": "sophie.biya@rhmanager.com",
            "telephone": "+237 698 567 890",
            "type_contrat": "CDI",
            "date_embauche": date(2023, 1, 12),
            "statut": "Actif"
        }
    ]
    
    for emp_data in employees_data:
        # Évite les doublons
        if not Employee.query.filter_by(email=emp_data["email"]).first():
            new_employee = Employee(**emp_data)
            db.session.add(new_employee)
    
    db.session.commit()
    print("✅ Employés créés avec succès.")

def seed_type_conges():
    """Créer les types de congés"""
    types_conges = [
        {"nom": "Congé annuel", "duree_max_jours": 30},
        {"nom": "Congé maladie", "duree_max_jours": 90},
        {"nom": "Congé maternité", "duree_max_jours": 98},
        {"nom": "Congé paternité", "duree_max_jours": 10},
        {"nom": "Congé sans solde", "duree_max_jours": None},
        {"nom": "Permission exceptionnelle", "duree_max_jours": 3}
    ]
    
    for type_data in types_conges:
        if not TypeConge.query.filter_by(nom=type_data["nom"]).first():
            new_type = TypeConge(**type_data)
            db.session.add(new_type)
    
    db.session.commit()
    print("✅ Types de congés créés avec succès.")

def seed_parametres_paie():
    """Créer les paramètres de paie"""
    if not ParametresPaie.query.first():
        parametres = ParametresPaie(
            smic_horaire=400.0,
            plafond_cnps=1500000.0,
            taux_transport=0.02,
            auto_calcule=True,
            jour_paiement=30,
            heures_hebdo=40,
            hs_25=8,
            hs_50=16
        )
        db.session.add(parametres)
        db.session.commit()
        print("✅ Paramètres de paie créés avec succès.")

def seed_cotisations():
    """Créer les cotisations sociales"""
    cotisations = [
        {"libelle": "CNPS", "taux_salarial": 2.8, "taux_patronal": 7.0},
        {"libelle": "CRTV", "taux_salarial": 1.0, "taux_patronal": 1.0},
        {"libelle": "CFE", "taux_salarial": 1.0, "taux_patronal": 2.0},
        {"libelle": "FAC", "taux_salarial": 0.0, "taux_patronal": 2.5}
    ]
    
    for cotis_data in cotisations:
        if not CotisationSociale.query.filter_by(libelle=cotis_data["libelle"]).first():
            new_cotis = CotisationSociale(**cotis_data)
            db.session.add(new_cotis)
    
    db.session.commit()
    print("✅ Cotisations sociales créées avec succès.")

def seed_parametres_presence():
    """Créer les paramètres de présence"""
    if not ParametrePresence.query.first():
        parametres = ParametrePresence(
            heure_arrivee_standard=time(8, 0),
            heure_depart_standard=time(17, 0),
            tolerance_retard_minutes=15,
            notifier_retard=True,
            notifier_absence=True
        )
        db.session.add(parametres)
        db.session.commit()
        print("✅ Paramètres de présence créés avec succès.")

def main():
    """Fonction principale pour exécuter le seeding"""
    with app.app_context():
        print("🌱 Début du seeding de la base de données...")
        
        # Créer les permissions
        permissions = seed_permissions()
        
        # Créer les rôles
        roles = seed_roles(permissions)
        
        # Créer les utilisateurs
        seed_users(roles)
        
        # Créer les employés
        seed_employees()
        
        # Créer les types de congés
        seed_type_conges()
        
        # Créer les paramètres de paie
        seed_parametres_paie()
        
        # Créer les cotisations sociales
        seed_cotisations()
        
        # Créer les paramètres de présence
        seed_parametres_presence()
        
        print("🎉 Seeding terminé avec succès!")
        print("\n📋 Comptes utilisateurs créés:")
        print("- admin / admin123 (Administrateur)")
        print("- rh_manager / rh123 (Manager RH)")
        print("- manager1 / manager123 (Manager)")
        print("- employe1 / employe123 (Employé)")
        print("- comptable / compta123 (Comptable)")

if __name__ == "__main__":
    main()
