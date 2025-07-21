from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from app.forms import ModifierMonCompteForm
from flask_login import current_user

# Initialiser les extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()

from app.models import Utilisateur

login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return Utilisateur.query.get(int(user_id))


def create_app():
    app = Flask(__name__)
    login_manager.init_app(app)
    
    # Charger la configuration depuis config.py
    app.config.from_object('config.Config')

    # Initialiser les extensions avec l'application Flask
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    @app.context_processor
    def inject_form_profil():
        form = ModifierMonCompteForm()
        if current_user.is_authenticated:
            form.nom_utilisateur.data = current_user.nom_utilisateur
            form.nom_complet.data = current_user.nom_complet
            form.email.data = current_user.email
        return dict(form=form)
    
    @app.context_processor
    def inject_forms():
        if current_user.is_authenticated:
            return {'profil_form': ModifierMonCompteForm(obj=current_user)}
        return {}

    # Importer les modèles pour que Flask-Migrate les connaisse
    from . import models

    # Importer et enregistrer les Blueprints
    from .routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from .routes.recrutement import recrutement_bp
    app.register_blueprint(recrutement_bp)

    from .routes.rh import rh_bp
    app.register_blueprint(rh_bp)

    from .routes.public import public_bp
    app.register_blueprint(public_bp)

    from .routes.evaluation import evaluation_bp
    app.register_blueprint(evaluation_bp)

    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.parametres import parametres_bp
    app.register_blueprint(parametres_bp)

    from app.routes.conges_temps import conges_temps_bp
    app.register_blueprint(conges_temps_bp)

    from app.routes.paie import paie_bp
    app.register_blueprint(paie_bp)
    
    # Enregistrer les commandes CLI
    # from app.utils.cli_commands import register_commands
    # register_commands(app)

    return app



