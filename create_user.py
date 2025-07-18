from app import create_app, db
from app.models import Utilisateur
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Supprimer tous les utilisateurs existants
    Utilisateur.query.delete()
    db.session.commit()

    # Créer un nouvel utilisateur avec un mot de passe bien hashé
    user = Utilisateur(
        nom_utilisateur="admin",
        nom_complet="Administrateur RH",
        email="admin@entreprise.com",
        actif=True
    )

    # Méthode 1 (appel direct méthode du modèle)
    user.set_password("admin123")

    # Méthode 2 (au cas où set_password ne fonctionnerait pas, décommenter cette ligne)
    # user.mot_de_passe_hash = generate_password_hash("admin123")

    db.session.add(user)
    db.session.commit()
    print("✅ Nouvel utilisateur 'admin' créé avec succès")
    print("🔐 Mot de passe hashé :", user.mot_de_passe_hash)
