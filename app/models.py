from . import db
from datetime import datetime, timedelta, date, time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import secrets

class Employee(db.Model):
    __tablename__ = 'employee'

    id = db.Column(db.Integer, primary_key=True)
    # Informations personnelles de base
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100))
    nom_complet = db.Column(db.String(200))
    date_naissance = db.Column(db.Date)
    lieu_naissance = db.Column(db.String(100))
    sexe = db.Column(db.String(10))  # Masculin, Féminin
    nationalite = db.Column(db.String(50), default='Camerounaise')
    situation_matrimoniale = db.Column(db.String(50))
    nombre_enfants = db.Column(db.Integer, default=0)
    
    # Contact et adresse
    email = db.Column(db.String(100), unique=True)
    telephone = db.Column(db.String(20))
    telephone_urgence = db.Column(db.String(20))
    adresse = db.Column(db.Text)
    ville = db.Column(db.String(50))
    
    # Informations professionnelles
    poste = db.Column(db.String(100))
    departement = db.Column(db.String(100))
    manager_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    type_contrat = db.Column(db.String(50))
    date_embauche = db.Column(db.Date)
    date_fin_contrat = db.Column(db.Date)
    salaire_base = db.Column(db.Float)
    statut = db.Column(db.String(50), default='Actif')
    
    # Documents et identité
    numero_cni = db.Column(db.String(20))
    numero_cnps = db.Column(db.String(20))
    numero_crtv = db.Column(db.String(20))
    numero_compte_bancaire = db.Column(db.String(30))
    banque = db.Column(db.String(50))
    
    # Fichiers et photos
    photo_profil = db.Column(db.String(200))  # chemin vers la photo
    cv_file = db.Column(db.String(200))
    contrat_file = db.Column(db.String(200))
    
    # Métadonnées
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cree_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    modifie_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    
    # Relations
    manager = db.relationship('Employee', remote_side=[id], backref='subordonne')
    createur = db.relationship('Utilisateur', foreign_keys=[cree_par])
    modificateur = db.relationship('Utilisateur', foreign_keys=[modifie_par])

    @property
    def age(self):
        """Calcule l'âge de l'employé"""
        if self.date_naissance:
            today = datetime.now().date()
            return today.year - self.date_naissance.year - ((today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
        return None
    
    @property
    def anciennete_jours(self):
        """Calcule l'ancienneté en jours"""
        if self.date_embauche:
            today = datetime.now().date()
            return (today - self.date_embauche).days
        return 0
    
    @property
    def anciennete_annees(self):
        """Calcule l'ancienneté en années"""
        return round(self.anciennete_jours / 365.25, 1)
    
    def __repr__(self):
        return f"<Employee {self.nom} {self.prenom or ''}>"

class Absence(db.Model):
    __tablename__ = 'absence'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    date_absence = db.Column(db.Date, nullable=False)
    motif = db.Column(db.String(100), nullable=False)
    justificatif = db.Column(db.String(200))  # fichier PDF/image
    etat = db.Column(db.String(50), default='En attente')  # En attente, Justifiée, Non justifiée
    impact_paie = db.Column(db.Boolean, default=False)
    date_enregistrement = db.Column(db.DateTime, default=datetime.utcnow)

    employe = db.relationship('Employee', backref='absences')

class Conge(db.Model):
    __tablename__ = 'conge'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    type_conge = db.Column(db.String(50), nullable=False)  # Congé annuel, Maladie, Maternité, etc.
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    nombre_jours = db.Column(db.Integer, nullable=False)
    motif = db.Column(db.Text)
    statut = db.Column(db.String(20), default='En attente')  # En attente, Approuvé, Rejeté
    demandeur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    approbateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_demande = db.Column(db.DateTime, default=datetime.utcnow)
    date_approbation = db.Column(db.DateTime)
    commentaire_approbateur = db.Column(db.Text)
    justificatif = db.Column(db.String(255))  # Chemin vers le fichier justificatif
    remplacant_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    
    # Relations
    employe = db.relationship("Employee", backref="conges", foreign_keys=[employe_id])
    demandeur = db.relationship("Utilisateur", foreign_keys=[demandeur_id], backref="conges_demandes")
    approbateur = db.relationship("Utilisateur", foreign_keys=[approbateur_id], backref="conges_approuves")
    remplacant = db.relationship("Employee", foreign_keys=[remplacant_id])
    
    @property
    def duree_en_jours(self):
        if self.date_debut and self.date_fin:
            return (self.date_fin - self.date_debut).days + 1
        return 0
    
    @property
    def est_en_cours(self):
        if self.statut == 'Approuvé' and self.date_debut and self.date_fin:
            today = date.today()
            return self.date_debut <= today <= self.date_fin
        return False
    
    @property
    def est_a_venir(self):
        if self.statut == 'Approuvé' and self.date_debut:
            return self.date_debut > date.today()
        return False

class OffreEmploi(db.Model):
    __tablename__ = 'offre_emploi'

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(150), nullable=False)
    departement = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    requirements = db.Column(db.Text)
    date_publication = db.Column(db.Date, default=datetime.utcnow)
    date_cloture = db.Column(db.Date)
    date_suppression = db.Column(db.Date)
    statut = db.Column(db.String(50), default='Brouillon')

    candidats = db.relationship('Candidat', backref='offre', cascade='all, delete-orphan', lazy=True)
    entretiens = db.relationship('Entretien', backref='offre', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f"<OffreEmploi {self.titre} ({self.statut})>"

class Candidat(db.Model):
    __tablename__ = 'candidat'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    cv = db.Column(db.String(200))  # Chemin fichier CV
    lettre_motivation = db.Column(db.String(200))  # Chemin fichier lettre
    date_soumission = db.Column(db.Date, default=datetime.utcnow)
    statut = db.Column(db.String(50), default='en cours d\'examen')

    offre_emploi_id = db.Column(db.Integer, db.ForeignKey('offre_emploi.id'), nullable=False)
    entretiens = db.relationship('Entretien', backref='candidat', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f"<Candidat {self.nom} ({self.statut})>"

class Entretien(db.Model):
    __tablename__ = 'entretien'

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(150), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    duree = db.Column(db.Integer)  # durée en minutes
    participants = db.Column(db.String(255))
    notes = db.Column(db.Text)

    offre_emploi_id = db.Column(db.Integer, db.ForeignKey('offre_emploi.id'), nullable=False)
    candidat_id = db.Column(db.Integer, db.ForeignKey('candidat.id'), nullable=False)

    def __repr__(self):
        return f"<Entretien {self.titre} pour candidat {self.candidat_id}>"

class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    evaluateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('template_evaluation.id'), nullable=True)
    
    # Période et type d'évaluation
    periode = db.Column(db.String(50), nullable=False)
    type_evaluation = db.Column(db.String(50), default='Annuelle')  # Annuelle, Semestrielle, Trimestrielle, Probation
    annee = db.Column(db.Integer, nullable=False)
    
    # Scores et évaluations
    score_global = db.Column(db.Float, nullable=False)
    score_max = db.Column(db.Float, default=100.0)
    note_finale = db.Column(db.String(20))  # Excellent, Très Bien, Bien, Satisfaisant, Insuffisant
    
    # Objectifs et développement
    objectifs_atteints = db.Column(db.Text)
    objectifs_non_atteints = db.Column(db.Text)
    objectifs_futurs = db.Column(db.Text)
    plan_developpement = db.Column(db.Text)
    formations_recommandees = db.Column(db.Text)
    
    # Commentaires
    commentaire_evaluateur = db.Column(db.Text)
    commentaire_employe = db.Column(db.Text)
    commentaire_rh = db.Column(db.Text)
    
    # Statut et workflow
    statut = db.Column(db.String(30), default='Brouillon')  # Brouillon, En cours, Validé, Finalisé
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_evaluation = db.Column(db.Date, nullable=False)
    date_validation = db.Column(db.DateTime)
    date_finalisation = db.Column(db.DateTime)
    
    # Métadonnées
    created_by = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    employe = db.relationship('Employee', backref='evaluations')
    evaluateur = db.relationship('Utilisateur', foreign_keys=[evaluateur_id], backref='evaluations_donnees')
    template = db.relationship('TemplateEvaluation', backref='evaluations')
    creator = db.relationship('Utilisateur', foreign_keys=[created_by])
    updater = db.relationship('Utilisateur', foreign_keys=[updated_by])

class TemplateEvaluation(db.Model):
    __tablename__ = 'template_evaluation'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type_evaluation = db.Column(db.String(50), nullable=False)
    
    # Configuration du template
    score_max = db.Column(db.Float, default=100.0)
    sections_json = db.Column(db.Text)  # Structure JSON des sections
    criteres_json = db.Column(db.Text)  # Critères d'évaluation en JSON
    
    # Status et métadonnées
    actif = db.Column(db.Boolean, default=True)
    par_defaut = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('Utilisateur', backref='templates_evaluation')

class CritereEvaluation(db.Model):
    __tablename__ = 'critere_evaluation'
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)
    section = db.Column(db.String(100), nullable=False)
    critere = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Notation
    score_obtenu = db.Column(db.Float, nullable=False)
    score_max = db.Column(db.Float, nullable=False)
    poids = db.Column(db.Float, default=1.0)  # Pondération du critère
    
    # Commentaires
    commentaire = db.Column(db.Text)
    recommandations = db.Column(db.Text)
    
    # Métadonnées
    ordre = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    evaluation = db.relationship('Evaluation', backref='criteres')

class ObjectifEmploye(db.Model):
    __tablename__ = 'objectif_employe'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=True)
    
    # Définition de l'objectif
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type_objectif = db.Column(db.String(50))  # Quantitatif, Qualitatif, Projet, Formation
    priorite = db.Column(db.String(20), default='Moyenne')  # Haute, Moyenne, Basse
    
    # Dates et échéances
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    date_realisation = db.Column(db.Date)
    
    # Suivi et résultats
    pourcentage_realisation = db.Column(db.Float, default=0.0)
    statut = db.Column(db.String(30), default='En cours')  # En cours, Atteint, Partiellement atteint, Non atteint
    resultat_obtenu = db.Column(db.Text)
    commentaires = db.Column(db.Text)
    
    # Mesures et indicateurs
    indicateur_mesure = db.Column(db.String(200))
    valeur_cible = db.Column(db.String(100))
    valeur_atteinte = db.Column(db.String(100))
    
    # Métadonnées
    created_by = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employe = db.relationship('Employee', backref='objectifs')
    evaluation = db.relationship('Evaluation', backref='objectifs_associes')
    creator = db.relationship('Utilisateur', backref='objectifs_crees')

class Utilisateur(db.Model, UserMixin):
    __tablename__ = 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(64), unique=True, nullable=False)
    nom_complet = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    actif = db.Column(db.Boolean, default=True)
    
    # Nouveaux champs pour la sécurité
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    role = db.relationship('Role', backref='utilisateurs')

    def set_password(self, mot_de_passe):
        self.mot_de_passe_hash = generate_password_hash(
            mot_de_passe,
            method='pbkdf2:sha256',
            salt_length=8
        )

    def check_password(self, mot_de_passe):
        return check_password_hash(self.mot_de_passe_hash, mot_de_passe)
    
    def generate_reset_token(self):
        """Génère un token de réinitialisation sécurisé"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)  # Expire dans 1 heure
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Vérifie si le token de réinitialisation est valide"""
        if not self.reset_token or not self.reset_token_expires:
            return False
        if datetime.utcnow() > self.reset_token_expires:
            return False
        return self.reset_token == token
    
    def clear_reset_token(self):
        """Supprime le token de réinitialisation"""
        self.reset_token = None
        self.reset_token_expires = None
    
    def is_account_locked(self):
        """Vérifie si le compte est verrouillé"""
        if not self.account_locked_until:
            return False
        return datetime.utcnow() < self.account_locked_until
    
    def increment_failed_login(self):
        """Incrémente les tentatives de connexion échouées"""
        if self.failed_login_attempts is None:
            self.failed_login_attempts = 0
        self.failed_login_attempts += 1
        # Verrouille le compte après 5 tentatives
        if self.failed_login_attempts >= 5:
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def reset_failed_login(self):
        """Remet à zéro les tentatives de connexion échouées"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.last_login = datetime.utcnow()

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.relationship('Permission', secondary='role_permission', backref='roles')

class Permission(db.Model):
    __tablename__ = 'permission'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)

# Table d'association entre rôle et permission
role_permission = db.Table('role_permission',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
)

class Presence(db.Model):
    __tablename__ = 'presence'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    heure_arrivee = db.Column(db.Time, nullable=True)
    heure_depart = db.Column(db.Time, nullable=True)
    retard_minutes = db.Column(db.Integer, default=0)

    employe = db.relationship("Employee", backref="presences")

class TypeConge(db.Model):
    """Types de congés configurables"""
    __tablename__ = 'type_conge'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    duree_max_jours = db.Column(db.Integer)  # Durée maximale en jours
    justificatif_requis = db.Column(db.Boolean, default=False)
    deductible_conge_annuel = db.Column(db.Boolean, default=True)  # Si ce type déduit du congé annuel
    couleur = db.Column(db.String(7), default='#007bff')  # Couleur pour l'affichage (format hex)
    actif = db.Column(db.Boolean, default=True)
    ordre_affichage = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<TypeConge {self.nom}>'

class SoldeConge(db.Model):
    """Soldes de congés par employé et par année"""
    __tablename__ = 'solde_conge'
    
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    annee = db.Column(db.Integer, nullable=False)
    jours_alloues = db.Column(db.Integer, default=0)  # Jours alloués pour l'année
    jours_pris = db.Column(db.Integer, default=0)     # Jours déjà pris
    jours_reports = db.Column(db.Integer, default=0)  # Jours reportés de l'année précédente
    jours_anticipes = db.Column(db.Integer, default=0) # Jours pris par anticipation
    date_maj = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    employe = db.relationship("Employee", backref="soldes_conges")
    
    # Contrainte unique : un seul solde par employé et par année
    __table_args__ = (db.UniqueConstraint('employe_id', 'annee', name='unique_solde_employe_annee'),)
    
    @property
    def jours_disponibles(self):
        """Calcule les jours de congé disponibles"""
        return (self.jours_alloues + self.jours_reports) - (self.jours_pris + self.jours_anticipes)
    
    @property
    def peut_prendre_conge(self, nb_jours):
        """Vérifie si l'employé peut prendre un certain nombre de jours"""
        return self.jours_disponibles >= nb_jours
    
    def __repr__(self):
        return f'<SoldeConge {self.employe.nom_complet if self.employe else "?"} - {self.annee}>'

class HistoriqueConge(db.Model):
    """Historique des modifications de congés"""
    __tablename__ = 'historique_conge'
    
    id = db.Column(db.Integer, primary_key=True)
    conge_id = db.Column(db.Integer, db.ForeignKey('conge.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # CREATE, UPDATE, APPROVE, REJECT, CANCEL
    ancien_statut = db.Column(db.String(20))
    nouveau_statut = db.Column(db.String(20))
    commentaire = db.Column(db.Text)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_action = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    conge = db.relationship("Conge", backref="historique")
    utilisateur = db.relationship("Utilisateur", backref="actions_conges")
    
    def __repr__(self):
        return f'<HistoriqueConge {self.action} - {self.date_action}>'

class EmployeeHistory(db.Model):
    """Historique des modifications d'employé"""
    __tablename__ = 'employee_history'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # CREATE, UPDATE, DELETE
    champ_modifie = db.Column(db.String(100))
    ancienne_valeur = db.Column(db.Text)
    nouvelle_valeur = db.Column(db.Text)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow)
    commentaire = db.Column(db.Text)
    
    # Relations
    employee = db.relationship('Employee', backref='historique')
    user = db.relationship('Utilisateur', backref='modifications_employees')
    
    def __repr__(self):
        return f"<EmployeeHistory {self.action} on {self.employee.nom}>"

class EmployeeDocument(db.Model):
    """Documents associés aux employés"""
    __tablename__ = 'employee_document'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    nom_document = db.Column(db.String(100), nullable=False)
    type_document = db.Column(db.String(50), nullable=False)  # CV, Contrat, Diplome, etc.
    nom_fichier = db.Column(db.String(200), nullable=False)
    chemin_fichier = db.Column(db.String(200), nullable=False)
    taille_fichier = db.Column(db.Integer)
    date_upload = db.Column(db.DateTime, default=datetime.utcnow)
    uploade_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    
    # Relations
    employee = db.relationship('Employee', backref='documents')
    uploader = db.relationship('Utilisateur', backref='documents_uploades')
    
    def __repr__(self):
        return f"<EmployeeDocument {self.nom_document}>"

# ============= MODÈLES POUR LE MODULE PRÉSENCES AVANCÉ =============

class ParametrePresence(db.Model):
    """Configuration globale du système de présences"""
    __tablename__ = 'parametre_presence'
    
    id = db.Column(db.Integer, primary_key=True)
    # Heures de travail standard
    heure_arrivee_standard = db.Column(db.Time, default=time(8, 0), nullable=False)
    heure_depart_standard = db.Column(db.Time, default=time(17, 0), nullable=False)
    duree_pause_minutes = db.Column(db.Integer, default=60)  # Pause déjeuner
    
    # Tolérances et règles
    tolerance_retard_minutes = db.Column(db.Integer, default=15)
    tolerance_depart_anticipe_minutes = db.Column(db.Integer, default=15)
    heures_minimum_journee = db.Column(db.Float, default=7.0)  # Heures minimum pour valider une journée
    
    # Règles de calcul des heures supplémentaires
    seuil_hs_quotidien = db.Column(db.Float, default=8.0)    # Seuil quotidien pour HS
    seuil_hs_hebdomadaire = db.Column(db.Float, default=40.0) # Seuil hebdomadaire pour HS
    
    # Notifications et alertes
    notifier_retard = db.Column(db.Boolean, default=True)
    notifier_absence = db.Column(db.Boolean, default=True)
    notifier_depart_anticipe = db.Column(db.Boolean, default=True)
    notifier_heures_supplementaires = db.Column(db.Boolean, default=True)
    
    # Système de pointage
    methodes_pointage = db.Column(db.String(200), default='manuel,qr_code')  # manuel, qr_code, badge, biometrie
    validation_gps = db.Column(db.Boolean, default=False)
    rayon_presence_metres = db.Column(db.Integer, default=100)
    
    # Paramètres d'automatisation
    calcul_automatique = db.Column(db.Boolean, default=True)
    generation_rapport_automatique = db.Column(db.Boolean, default=True)
    
    # Métadonnées
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modifie_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    
    # Relations
    modificateur = db.relationship('Utilisateur', backref='modifications_presence')
    
    def __repr__(self):
        return f"<ParametrePresence {self.heure_arrivee_standard}-{self.heure_depart_standard}>"

class Pointage(db.Model):
    """Enregistrement des pointages (arrivées/départs)"""
    __tablename__ = 'pointage'
    
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    
    # Informations de pointage
    date_pointage = db.Column(db.Date, nullable=False)
    heure_pointage = db.Column(db.Time, nullable=False)
    type_pointage = db.Column(db.String(20), nullable=False)  # 'entree', 'sortie', 'pause_debut', 'pause_fin'
    
    # Méthode de pointage
    methode = db.Column(db.String(50), default='manuel')  # manuel, qr_code, badge, biometrie, gps
    
    # Localisation (optionnel)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    adresse = db.Column(db.String(200))
    
    # Métadonnées
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    commentaire = db.Column(db.Text)
    valide = db.Column(db.Boolean, default=True)
    
    # Horodatage
    timestamp_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    employe = db.relationship('Employee', backref='pointages')
    
    # Index pour optimisation
    __table_args__ = (
        db.Index('idx_pointage_employe_date', 'employe_id', 'date_pointage'),
        db.Index('idx_pointage_date_type', 'date_pointage', 'type_pointage'),
    )
    
    def __repr__(self):
        return f"<Pointage {self.employe.nom} {self.type_pointage} {self.date_pointage} {self.heure_pointage}>"

class HeuresTravail(db.Model):
    """Calcul des heures de travail journalières (table consolidée)"""
    __tablename__ = 'heures_travail'
    
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date_travail = db.Column(db.Date, nullable=False)
    
    # Heures effectives
    heure_arrivee = db.Column(db.Time)
    heure_depart = db.Column(db.Time)
    duree_pause_minutes = db.Column(db.Integer, default=0)
    
    # Calculs automatiques
    heures_presentes = db.Column(db.Float, default=0.0)      # Heures totales présent
    heures_travaillees = db.Column(db.Float, default=0.0)    # Heures travaillées (présent - pause)
    heures_normales = db.Column(db.Float, default=0.0)       # Heures normales
    heures_supplementaires = db.Column(db.Float, default=0.0) # Heures supplémentaires
    
    # Statuts et indicateurs
    retard_minutes = db.Column(db.Integer, default=0)
    depart_anticipe_minutes = db.Column(db.Integer, default=0)
    statut = db.Column(db.String(20), default='present')     # present, absent, retard, conge, maladie
    
    # Validation et approbation
    valide = db.Column(db.Boolean, default=False)
    valide_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_validation = db.Column(db.DateTime)
    commentaire_validation = db.Column(db.Text)
    
    # Calcul automatique ou manuel
    calcule_automatiquement = db.Column(db.Boolean, default=True)
    
    # Métadonnées
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    employe = db.relationship('Employee', backref='heures_travail')
    validateur = db.relationship('Utilisateur', backref='validations_heures')
    
    # Contrainte unique : une seule entrée par employé et par jour
    __table_args__ = (
        db.UniqueConstraint('employe_id', 'date_travail', name='unique_employe_date_travail'),
        db.Index('idx_heures_employe_date', 'employe_id', 'date_travail'),
        db.Index('idx_heures_date_statut', 'date_travail', 'statut'),
    )
    
    @property
    def est_retard(self):
        """Vérifie si l'employé était en retard"""
        return self.retard_minutes > 0
    
    @property
    def est_absent(self):
        """Vérifie si l'employé était absent"""
        return self.statut == 'absent'
    
    def __repr__(self):
        return f"<HeuresTravail {self.employe.nom} {self.date_travail} {self.heures_travaillees}h>"

class NotificationPresence(db.Model):
    """Notifications liées aux présences"""
    __tablename__ = 'notification_presence'
    
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    
    # Type et contenu de notification
    type_notification = db.Column(db.String(50), nullable=False)  # retard, absence, depart_anticipe, heures_sup
    titre = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priorite = db.Column(db.String(20), default='normale')  # faible, normale, haute, critique
    
    # Destinataires
    destinataire_employe = db.Column(db.Boolean, default=True)
    destinataire_manager = db.Column(db.Boolean, default=True)
    destinataire_rh = db.Column(db.Boolean, default=True)
    
    # Statut de la notification
    statut = db.Column(db.String(20), default='nouvelle')  # nouvelle, envoyee, lue, traitee
    date_envoi = db.Column(db.DateTime)
    date_lecture = db.Column(db.DateTime)
    
    # Référence aux données
    date_reference = db.Column(db.Date, nullable=False)
    donnees_reference = db.Column(db.JSON)  # Données contextuelles en JSON
    
    # Métadonnées
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    employe = db.relationship('Employee', backref='notifications_presence')
    
    # Index pour optimisation
    __table_args__ = (
        db.Index('idx_notif_employe_date', 'employe_id', 'date_reference'),
        db.Index('idx_notif_type_statut', 'type_notification', 'statut'),
    )
    
    def __repr__(self):
        return f"<NotificationPresence {self.type_notification} {self.employe.nom} {self.date_reference}>"

# Extension du modèle Presence existant pour compatibilité
# (Le modèle Presence existant est conservé pour la compatibilité ascendante)

# ============================================================================
# MODÈLES POUR LE MODULE GESTION DE LA PAIE
# ============================================================================

class ParametresPaie(db.Model):
    """Paramètres globaux de la paie"""
    __tablename__ = 'parametres_paie'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Paramètres salariaux de base
    smic_horaire = db.Column(db.Float, nullable=False, default=242.0)  # SMIC horaire Cameroun
    plafond_cnps = db.Column(db.Float, nullable=False, default=7500.0)  # Plafond CNPS
    taux_transport = db.Column(db.Float, default=0.0)  # Taux transport
    
    # Paramètres de calcul
    auto_calcule = db.Column(db.Boolean, default=True)
    jour_paiement = db.Column(db.Integer, default=28)  # Jour du mois de paiement
    
    # Configuration des heures
    heures_hebdo = db.Column(db.Integer, default=40)  # Heures standard par semaine
    hs_25 = db.Column(db.Integer, default=25)  # Majoration HS 25%
    hs_50 = db.Column(db.Integer, default=50)  # Majoration HS 50%
    
    # Paramètres fiscaux
    taux_impot_liberatoire = db.Column(db.Float, default=11.0)  # Taux impôt libératoire
    abattement_professionnel = db.Column(db.Float, default=0.30)  # 30% d'abattement
    
    # Paramètres de congés payés
    taux_conge_paye = db.Column(db.Float, default=8.33)  # 1/12 du salaire
    
    # Métadonnées
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modifie_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    
    # Relations
    modificateur = db.relationship('Utilisateur', backref='modifications_paie')
    
    def __repr__(self):
        return f"<ParametresPaie SMIC:{self.smic_horaire}>"

class CotisationSociale(db.Model):
    """Cotisations sociales configurables"""
    __tablename__ = 'cotisation_sociale'
    
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.String(20), unique=True)  # Code interne
    description = db.Column(db.Text)
    
    # Taux de cotisation
    taux_salarial = db.Column(db.Float, nullable=False, default=0.0)  # Part employé
    taux_patronal = db.Column(db.Float, nullable=False, default=0.0)  # Part employeur
    
    # Paramètres de calcul
    base_calcul = db.Column(db.String(50), default='salaire_brut')  # salaire_brut, salaire_plafonné, etc.
    plafond_application = db.Column(db.Float)  # Plafond si applicable
    minimum_cotisation = db.Column(db.Float, default=0.0)
    maximum_cotisation = db.Column(db.Float)
    
    # Configuration
    obligatoire = db.Column(db.Boolean, default=True)
    actif = db.Column(db.Boolean, default=True)
    ordre_affichage = db.Column(db.Integer, default=0)
    
    # Catégorie pour regroupement
    categorie = db.Column(db.String(50), default='sociale')  # sociale, fiscale, autre
    
    # Métadonnées
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CotisationSociale {self.libelle}>"

class BulletinPaie(db.Model):
    """Bulletins de paie des employés"""
    __tablename__ = 'bulletin_paie'
    
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    
    # Période de paie
    periode_debut = db.Column(db.Date, nullable=False)
    periode_fin = db.Column(db.Date, nullable=False)
    mois = db.Column(db.Integer, nullable=False)
    annee = db.Column(db.Integer, nullable=False)
    
    # Informations de base
    numero_bulletin = db.Column(db.String(50), unique=True, nullable=False)
    salaire_base = db.Column(db.Float, nullable=False)
    
    # Éléments de temps
    nb_jours_travailles = db.Column(db.Float, default=0.0)
    nb_jours_ouvres = db.Column(db.Integer, default=22)  # Jours ouvrés standard
    nb_heures_normales = db.Column(db.Float, default=0.0)
    nb_heures_supplementaires = db.Column(db.Float, default=0.0)
    nb_jours_conges = db.Column(db.Float, default=0.0)
    nb_jours_absences = db.Column(db.Float, default=0.0)
    
    # Calculs de salaire
    salaire_brut = db.Column(db.Float, nullable=False)
    total_cotisations_salariales = db.Column(db.Float, default=0.0)
    total_cotisations_patronales = db.Column(db.Float, default=0.0)
    salaire_imposable = db.Column(db.Float, default=0.0)
    impot_sur_salaire = db.Column(db.Float, default=0.0)
    salaire_net = db.Column(db.Float, nullable=False)
    
    # Éléments variables
    primes_bonus = db.Column(db.Float, default=0.0)
    indemnites = db.Column(db.Float, default=0.0)
    avantages_nature = db.Column(db.Float, default=0.0)
    retenues_diverses = db.Column(db.Float, default=0.0)
    
    # Congés payés
    provision_conges_payes = db.Column(db.Float, default=0.0)
    solde_conges_payes = db.Column(db.Float, default=0.0)
    
    # Statut et validation
    statut = db.Column(db.String(20), default='brouillon')  # brouillon, validé, payé, archivé
    valide = db.Column(db.Boolean, default=False)
    date_validation = db.Column(db.DateTime)
    valide_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    
    # Paiement
    date_paiement = db.Column(db.Date)
    mode_paiement = db.Column(db.String(50), default='virement')  # virement, especes, cheque
    reference_paiement = db.Column(db.String(100))
    
    # Métadonnées
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cree_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    
    # Relations
    employe = db.relationship('Employee', backref='bulletins_paie')
    validateur = db.relationship('Utilisateur', foreign_keys=[valide_par], backref='bulletins_valides')
    createur = db.relationship('Utilisateur', foreign_keys=[cree_par], backref='bulletins_crees')
    
    # Contrainte unique par employé et période
    __table_args__ = (
        db.UniqueConstraint('employe_id', 'mois', 'annee', name='unique_bulletin_employe_periode'),
        db.Index('idx_bulletin_periode', 'mois', 'annee'),
        db.Index('idx_bulletin_employe', 'employe_id'),
    )
    
    @property
    def periode_str(self):
        """Retourne la période sous forme de string"""
        months = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        return f"{months[self.mois]} {self.annee}"
    
    @property
    def taux_activite(self):
        """Calcule le taux d'activité (jours travaillés / jours ouvrés)"""
        if self.nb_jours_ouvres > 0:
            return round((self.nb_jours_travailles / self.nb_jours_ouvres) * 100, 2)
        return 0.0
    
    def __repr__(self):
        return f"<BulletinPaie {self.numero_bulletin} - {self.employe.nom} {self.periode_str}>"

class ElementPaie(db.Model):
    """Éléments de paie détaillés par bulletin"""
    __tablename__ = 'element_paie'
    
    id = db.Column(db.Integer, primary_key=True)
    bulletin_id = db.Column(db.Integer, db.ForeignKey('bulletin_paie.id'), nullable=False)
    
    # Identification de l'élément
    libelle = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20))
    categorie = db.Column(db.String(50), nullable=False)  # salaire, prime, cotisation, retenue, etc.
    type_element = db.Column(db.String(20), nullable=False)  # gain, retenue
    
    # Calculs
    base_calcul = db.Column(db.Float, default=0.0)
    taux = db.Column(db.Float, default=0.0)
    quantite = db.Column(db.Float, default=1.0)
    montant = db.Column(db.Float, nullable=False)
    
    # Répartition employé/employeur
    part_salariale = db.Column(db.Float, default=0.0)
    part_patronale = db.Column(db.Float, default=0.0)
    
    # Configuration
    imposable = db.Column(db.Boolean, default=True)
    soumis_cotisations = db.Column(db.Boolean, default=True)
    
    # Métadonnées
    ordre_affichage = db.Column(db.Integer, default=0)
    commentaire = db.Column(db.Text)
    
    # Relations
    bulletin = db.relationship('BulletinPaie', backref='elements_paie')
    
    def __repr__(self):
        return f"<ElementPaie {self.libelle}: {self.montant}>"

class HistoriquePaie(db.Model):
    """Historique des modifications de paie"""
    __tablename__ = 'historique_paie'
    
    id = db.Column(db.Integer, primary_key=True)
    bulletin_id = db.Column(db.Integer, db.ForeignKey('bulletin_paie.id'), nullable=False)
    
    # Action effectuée
    action = db.Column(db.String(50), nullable=False)  # creation, modification, validation, paiement
    ancien_statut = db.Column(db.String(20))
    nouveau_statut = db.Column(db.String(20))
    
    # Détails des modifications
    champs_modifies = db.Column(db.JSON)  # Détails des champs modifiés
    anciennes_valeurs = db.Column(db.JSON)
    nouvelles_valeurs = db.Column(db.JSON)
    
    # Métadonnées
    commentaire = db.Column(db.Text)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_action = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    bulletin = db.relationship('BulletinPaie', backref='historique_paie')
    utilisateur = db.relationship('Utilisateur', backref='actions_paie')
    
    def __repr__(self):
        return f"<HistoriquePaie {self.action} - {self.date_action}>"

class AvanceSalaire(db.Model):
    """Avances sur salaire"""
    __tablename__ = 'avance_salaire'
    
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    
    # Détails de l'avance
    montant_demande = db.Column(db.Float, nullable=False)
    montant_accorde = db.Column(db.Float, nullable=False)
    motif = db.Column(db.Text)
    
    # Dates
    date_demande = db.Column(db.Date, nullable=False)
    date_accord = db.Column(db.Date)
    date_versement = db.Column(db.Date)
    
    # Remboursement
    nb_mensualites = db.Column(db.Integer, default=1)
    montant_mensualite = db.Column(db.Float)
    montant_rembourse = db.Column(db.Float, default=0.0)
    solde_restant = db.Column(db.Float)
    
    # Statut
    statut = db.Column(db.String(20), default='demande')  # demande, accorde, verse, rembourse
    
    # Approbation
    demandeur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    approbateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    commentaire_approbation = db.Column(db.Text)
    
    # Relations
    employe = db.relationship('Employee', backref='avances_salaire')
    demandeur = db.relationship('Utilisateur', foreign_keys=[demandeur_id])
    approbateur = db.relationship('Utilisateur', foreign_keys=[approbateur_id])
    
    @property
    def est_soldee(self):
        """Vérifie si l'avance est entièrement remboursée"""
        return abs(self.montant_rembourse - self.montant_accorde) < 0.01
    
    def __repr__(self):
        return f"<AvanceSalaire {self.employe.nom} - {self.montant_accorde} FCFA>"

class RemboursementAvance(db.Model):
    """Remboursements d'avances sur salaire"""
    __tablename__ = 'remboursement_avance'
    
    id = db.Column(db.Integer, primary_key=True)
    avance_id = db.Column(db.Integer, db.ForeignKey('avance_salaire.id'), nullable=False)
    bulletin_id = db.Column(db.Integer, db.ForeignKey('bulletin_paie.id'), nullable=False)
    
    # Détails du remboursement
    montant = db.Column(db.Float, nullable=False)
    numero_echeance = db.Column(db.Integer, nullable=False)
    
    # Métadonnées
    date_remboursement = db.Column(db.Date, nullable=False)
    commentaire = db.Column(db.Text)
    
    # Relations
    avance = db.relationship('AvanceSalaire', backref='remboursements')
    bulletin = db.relationship('BulletinPaie', backref='remboursements_avances')
    
    def __repr__(self):
        return f"<RemboursementAvance {self.montant} FCFA>"

class TypeElementPaie(db.Model):
    """Types d'éléments de paie configurables"""
    __tablename__ = 'type_element_paie'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    libelle = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Configuration
    categorie = db.Column(db.String(50), nullable=False)  # salaire, prime, cotisation, retenue
    type_element = db.Column(db.String(20), nullable=False)  # gain, retenue
    mode_calcul = db.Column(db.String(50), default='montant_fixe')  # montant_fixe, pourcentage, formule
    
    # Paramètres par défaut
    taux_defaut = db.Column(db.Float, default=0.0)
    montant_defaut = db.Column(db.Float, default=0.0)
    base_calcul_defaut = db.Column(db.String(50), default='salaire_brut')
    
    # Propriétés
    imposable = db.Column(db.Boolean, default=True)
    soumis_cotisations = db.Column(db.Boolean, default=True)
    obligatoire = db.Column(db.Boolean, default=False)
    actif = db.Column(db.Boolean, default=True)
    
    # Affichage
    ordre_affichage = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f"<TypeElementPaie {self.code} - {self.libelle}>"

class ParametreCalculPaie(db.Model):
    """Paramètres de calcul spécifiques par employé"""
    __tablename__ = 'parametre_calcul_paie'
    
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    
    # Paramètres individuels
    salaire_base_mensuel = db.Column(db.Float)
    taux_horaire = db.Column(db.Float)
    coefficient_anciennete = db.Column(db.Float, default=1.0)
    
    # Primes et indemnités régulières
    prime_anciennete = db.Column(db.Float, default=0.0)
    prime_fonction = db.Column(db.Float, default=0.0)
    prime_transport = db.Column(db.Float, default=0.0)
    indemnite_logement = db.Column(db.Float, default=0.0)
    
    # Avantages en nature
    avantage_voiture = db.Column(db.Float, default=0.0)
    avantage_logement = db.Column(db.Float, default=0.0)
    avantage_telephone = db.Column(db.Float, default=0.0)
    
    # Paramètres fiscaux
    nombre_parts = db.Column(db.Float, default=1.0)
    exoneration_impot = db.Column(db.Boolean, default=False)
    taux_impot_specifique = db.Column(db.Float)
    
    # Paramètres de cotisation
    exoneration_cnps = db.Column(db.Boolean, default=False)
    cotisations_specifiques = db.Column(db.JSON)  # Cotisations spécifiques en JSON
    
    # Métadonnées
    date_effet = db.Column(db.Date, default=date.today)
    date_fin = db.Column(db.Date)
    actif = db.Column(db.Boolean, default=True)
    
    # Relations
    employe = db.relationship('Employee', backref='parametres_paie')
    
    # Contrainte unique par employé actif
    __table_args__ = (
        db.Index('idx_parametre_paie_employe', 'employe_id'),
    )
    
    def __repr__(self):
        return f"<ParametreCalculPaie {self.employe.nom} - {self.salaire_base_mensuel} FCFA>"
