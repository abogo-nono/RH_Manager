from app import create_app, db
from app.models import Utilisateur

def test_security_features():
    """Test des nouvelles fonctionnalités de sécurité"""
    app = create_app()
    
    with app.app_context():
        print("🔒 Test des fonctionnalités de sécurité...")
        
        # Obtenir un utilisateur de test
        admin = Utilisateur.query.filter_by(nom_utilisateur='admin').first()
        
        if admin:
            print(f"✅ Utilisateur trouvé: {admin.nom_utilisateur}")
            
            # Test 1: Générer un token de réinitialisation
            token = admin.generate_reset_token()
            print(f"✅ Token généré: {token[:20]}...")
            
            # Test 2: Vérifier le token
            is_valid = admin.verify_reset_token(token)
            print(f"✅ Token valide: {is_valid}")
            
            # Test 3: Test de verrouillage de compte
            print(f"✅ Tentatives échouées avant: {admin.failed_login_attempts}")
            
            # Simuler des tentatives échouées
            for i in range(3):
                admin.increment_failed_login()
            
            print(f"✅ Tentatives échouées après: {admin.failed_login_attempts}")
            print(f"✅ Compte verrouillé: {admin.is_account_locked()}")
            
            # Réinitialiser pour les tests
            admin.reset_failed_login()
            admin.clear_reset_token()
            db.session.commit()
            
            print("✅ Tests de sécurité terminés avec succès!")
            
        else:
            print("❌ Aucun utilisateur admin trouvé. Exécutez d'abord le seeder.")

if __name__ == "__main__":
    test_security_features()
