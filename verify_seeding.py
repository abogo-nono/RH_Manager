from app import create_app, db
from app.models import Permission, Role, Utilisateur, Employee, TypeConge

app = create_app()

def verify_seeding():
    """Vérifier que le seeding s'est bien passé"""
    with app.app_context():
        print("🔍 Vérification du seeding...")
        print()
        
        # Vérifier les permissions
        permissions = Permission.query.all()
        print(f"📋 Permissions créées: {len(permissions)}")
        for perm in permissions:
            print(f"  - {perm.nom} ({perm.code})")
        print()
        
        # Vérifier les rôles
        roles = Role.query.all()
        print(f"👥 Rôles créés: {len(roles)}")
        for role in roles:
            print(f"  - {role.nom} ({len(role.permissions)} permissions)")
        print()
        
        # Vérifier les utilisateurs
        users = Utilisateur.query.all()
        print(f"🔐 Utilisateurs créés: {len(users)}")
        for user in users:
            print(f"  - {user.nom_utilisateur} ({user.nom_complet}) - Rôle: {user.role.nom if user.role else 'Aucun'}")
        print()
        
        # Vérifier les employés
        employees = Employee.query.all()
        print(f"👨‍💼 Employés créés: {len(employees)}")
        for emp in employees:
            print(f"  - {emp.nom} ({emp.poste}) - {emp.departement}")
        print()
        
        # Vérifier les types de congés
        types_conges = TypeConge.query.all()
        print(f"🏖️ Types de congés créés: {len(types_conges)}")
        for type_conge in types_conges:
            print(f"  - {type_conge.nom} (max: {type_conge.duree_max_jours or 'illimité'} jours)")
        print()
        
        print("✅ Vérification terminée!")

if __name__ == "__main__":
    verify_seeding()
