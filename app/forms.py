from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, BooleanField, TextAreaField, SelectField, PasswordField, IntegerField, FloatField, TimeField, DecimalField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from flask_wtf.file import FileField, FileAllowed
from wtforms_sqlalchemy.fields import QuerySelectField
from datetime import date, datetime

class AbsenceForm(FlaskForm):
    employe_id = SelectField("Employé", coerce=int, validators=[DataRequired()])
    date_absence = DateField("Date de l'absence", format='%Y-%m-%d', validators=[DataRequired()])
    motif = StringField("Motif", validators=[DataRequired()])
    justificatif = FileField("Justificatif (PDF ou image)", validators=[FileAllowed(['pdf', 'jpg', 'png', 'jpeg'], 'Fichier invalide')])
    impact_paie = BooleanField("Impacter la paie ?")
    submit = SubmitField("Enregistrer")

class CongeForm(FlaskForm):
    employe_id = SelectField("Employé", coerce=int, validators=[DataRequired()])
    type_conge = SelectField("Type de congé", validators=[DataRequired()])
    date_debut = DateField("Date de début", validators=[DataRequired()])
    date_fin = DateField("Date de fin", validators=[DataRequired()])
    motif = TextAreaField("Motif/Description", validators=[Optional()])
    remplacant_id = SelectField("Remplaçant", coerce=int, validators=[Optional()])
    justificatif = FileField("Justificatif", validators=[FileAllowed(['pdf', 'jpg', 'png', 'jpeg', 'doc', 'docx'], 'Fichier invalide')])
    submit = SubmitField("Soumettre la demande")
    
    def validate_date_fin(self, field):
        if self.date_debut.data and field.data:
            if field.data < self.date_debut.data:
                raise ValidationError("La date de fin doit être postérieure à la date de début")

class ApprovalCongeForm(FlaskForm):
    statut = SelectField("Décision", choices=[
        ('Approuvé', 'Approuver'),
        ('Rejeté', 'Rejeter')
    ], validators=[DataRequired()])
    commentaire = TextAreaField("Commentaire", validators=[Optional()])
    submit = SubmitField("Valider")

class TypeCongeForm(FlaskForm):
    nom = StringField("Nom du type de congé", validators=[DataRequired(), Length(max=50)])
    description = TextAreaField("Description", validators=[Optional()])
    duree_max_jours = IntegerField("Durée maximale (jours)", validators=[Optional(), NumberRange(min=1)])
    justificatif_requis = BooleanField("Justificatif requis")
    deductible_conge_annuel = BooleanField("Déductible du congé annuel", default=True)
    couleur = StringField("Couleur (hex)", validators=[Optional()], default='#007bff')
    actif = BooleanField("Actif", default=True)
    ordre_affichage = IntegerField("Ordre d'affichage", validators=[Optional()], default=0)
    submit = SubmitField("Enregistrer")

class SoldeCongeForm(FlaskForm):
    employe_id = SelectField("Employé", coerce=int, validators=[DataRequired()])
    annee = IntegerField("Année", validators=[DataRequired(), NumberRange(min=2020, max=2030)])
    jours_alloues = IntegerField("Jours alloués", validators=[DataRequired(), NumberRange(min=0)])
    jours_reports = IntegerField("Jours reportés", validators=[Optional(), NumberRange(min=0)], default=0)
    submit = SubmitField("Enregistrer")

class DemandeCongeForm(FlaskForm):
    employe_id = SelectField("Employé", coerce=int, validators=[DataRequired()])
    type_conge = SelectField("Type de congé", validators=[DataRequired()])
    date_debut = DateField("Date de début", validators=[DataRequired()])
    date_fin = DateField("Date de fin", validators=[DataRequired()])
    motif = TextAreaField("Motif", validators=[Optional()])
    submit = SubmitField("Soumettre la demande")
    
    def validate_date_fin(self, field):
        if self.date_debut.data and field.data:
            if field.data < self.date_debut.data:
                raise ValidationError("La date de fin doit être postérieure à la date de début")

class EmployeeForm(FlaskForm):
    # Informations personnelles
    nom = StringField('Nom de famille', validators=[DataRequired()])
    prenom = StringField('Prénom')
    date_naissance = DateField('Date de naissance', format='%Y-%m-%d', validators=[Optional()])
    lieu_naissance = StringField('Lieu de naissance')
    sexe = SelectField('Sexe', choices=[('', 'Sélectionner'), ('Masculin', 'Masculin'), ('Féminin', 'Féminin')])
    nationalite = StringField('Nationalité', default='Camerounaise')
    situation_matrimoniale = SelectField('Situation matrimoniale', 
                                       choices=[('', 'Sélectionner'), ('Célibataire', 'Célibataire'), 
                                               ('Marié(e)', 'Marié(e)'), ('Divorcé(e)', 'Divorcé(e)'), ('Veuf(ve)', 'Veuf(ve)')])
    nombre_enfants = IntegerField('Nombre d\'enfants', default=0)
    
    # Contact
    email = StringField('Email', validators=[Email(), Optional()])
    telephone = StringField('Téléphone')
    telephone_urgence = StringField('Téléphone d\'urgence')
    adresse = TextAreaField('Adresse complète')
    ville = StringField('Ville')
    
    # Informations professionnelles
    poste = StringField('Poste')
    departement = SelectField('Département', 
                             choices=[('', 'Sélectionner'), ('Ressources Humaines', 'Ressources Humaines'),
                                     ('IT', 'IT'), ('Finance', 'Finance'), ('Administration', 'Administration'),
                                     ('Commercial', 'Commercial'), ('Production', 'Production')])
    manager_id = SelectField('Manager', coerce=int, validators=[Optional()])
    type_contrat = SelectField('Type de contrat', 
                              choices=[('', 'Sélectionner'), ('CDI', 'CDI'), ('CDD', 'CDD'), 
                                      ('Stage', 'Stage'), ('Freelance', 'Freelance')])
    date_embauche = DateField('Date d\'embauche', format='%Y-%m-%d', validators=[Optional()])
    date_fin_contrat = DateField('Date fin de contrat', format='%Y-%m-%d', validators=[Optional()])
    salaire_base = FloatField('Salaire de base (FCFA)', validators=[Optional(), NumberRange(min=0)])
    statut = SelectField('Statut', 
                        choices=[('Actif', 'Actif'), ('Inactif', 'Inactif'), ('Suspendu', 'Suspendu'), 
                                ('En congé', 'En congé'), ('Démissionné', 'Démissionné')])
    
    # Documents d'identité
    numero_cni = StringField('Numéro CNI')
    numero_cnps = StringField('Numéro CNPS')
    numero_crtv = StringField('Numéro CRTV')
    numero_compte_bancaire = StringField('Numéro de compte bancaire')
    banque = StringField('Banque')
    
    # Fichiers
    photo_profil = FileField('Photo de profil', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images uniquement')])
    cv_file = FileField('CV', validators=[FileAllowed(['pdf', 'doc', 'docx'], 'Documents uniquement')])
    contrat_file = FileField('Contrat', validators=[FileAllowed(['pdf', 'doc', 'docx'], 'Documents uniquement')])
    
    submit = SubmitField('Enregistrer')
    
    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)
        # Charger dynamiquement les managers (employés existants)
        from app.models import Employee
        try:
            self.manager_id.choices = [(0, 'Aucun manager')] + [(emp.id, f"{emp.nom} {emp.prenom or ''}") for emp in Employee.query.all()]
        except:
            self.manager_id.choices = [(0, 'Aucun manager')]

class CongeForm(FlaskForm):
    employee_id = StringField('ID Employé', validators=[DataRequired()])
    type_conge = StringField('Type de congé')
    date_debut = DateField('Date de début', format='%Y-%m-%d')
    date_fin = DateField('Date de fin', format='%Y-%m-%d')
    motif = TextAreaField('Motif')
    statut = StringField('Statut')
    submit = SubmitField('Enregistrer')

class RecrutementForm(FlaskForm):
    titre_poste = StringField('Titre du poste')
    departement = StringField('Département')
    description_poste = TextAreaField('Description du poste')
    prerequis = TextAreaField('Prérequis')
    date_cloture = DateField('Date de clôture', format='%Y-%m-%d')
    statut = StringField('Statut')
    submit = SubmitField('Enregistrer')

class FormUtilisateur(FlaskForm):
    nom_utilisateur = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(max=50)])
    nom_complet = StringField('Nom complet', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = QuerySelectField('Rôle', get_label='nom', allow_blank=False)
    mot_de_passe = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    actif = BooleanField('Compte actif', default=True)
    submit = SubmitField('Ajouter')

class AjouterRoleForm(FlaskForm):
    nom = StringField('Nom du rôle', validators=[DataRequired()])
    submit = SubmitField("Ajouter")

class ModifierMonCompteForm(FlaskForm):
    nom_utilisateur = StringField('Nom d’utilisateur', validators=[DataRequired()])
    nom_complet = StringField('Nom complet')
    email = StringField('Email', validators=[DataRequired(), Email()])
    mot_de_passe = PasswordField('Nouveau mot de passe', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class AjouterTypeCongeForm(FlaskForm):
    nom = StringField('Nom du congé', validators=[DataRequired()])
    duree_max_jours = IntegerField('Durée maximale (en jours)', validators=[DataRequired()])
    validation_requise = BooleanField('Validation requise ?')
    submit = SubmitField('Ajouter')

class FormParametresPaie(FlaskForm):
    smic_horaire = DecimalField("SMIC horaire (fcfa)", validators=[DataRequired(), NumberRange(min=0)], places=0)
    plafond_cnps = DecimalField("Plafond CNPS (fcfa)", validators=[DataRequired(), NumberRange(min=0)], places=0)
    #taux_transport = DecimalField("Taux versement transport (fcfa)", validators=[DataRequired(), NumberRange(min=0)], places=2)

    auto_calcule = BooleanField("Calcul automatique des bulletins")
    jour_paiement = SelectField("Jour de versement de la paie", coerce=int, choices=[(i, str(i)) for i in range(1, 32)])

    heures_hebdo = IntegerField("Heures hebdomadaires", validators=[DataRequired()])
    hs_25 = IntegerField("Taux majoration HS 25%", validators=[DataRequired()])
    hs_50 = IntegerField("Taux majoration HS 50%", validators=[DataRequired()])

    submit = SubmitField("Enregistrer les modifications")

class FormAjouterCotisation(FlaskForm):
    libelle = StringField("Libellé", validators=[DataRequired()])
    taux_salarial = FloatField("Taux salarial (%)", validators=[DataRequired()])
    taux_patronal = FloatField("Taux patronal (%)", validators=[DataRequired()])
    submit = SubmitField("Ajouter")

class FormParametrePresence(FlaskForm):
    heure_arrivee = TimeField("Heure d'arrivée", validators=[DataRequired()])
    heure_depart = TimeField("Heure de départ", validators=[DataRequired()])
    tolerance_retard = IntegerField("Tolérance de retard (minutes)", validators=[DataRequired()])
    notifier_retard = BooleanField("Notifier en cas de retard")
    notifier_absence = BooleanField("Notifier en cas d'absence")
    submit = SubmitField("Enregistrer")

class ParametrePresenceForm(FlaskForm):
    """Formulaire pour les paramètres de présence"""
    heure_debut = TimeField("Heure de début", validators=[DataRequired()],
                           render_kw={'class': 'form-control'})
    heure_fin = TimeField("Heure de fin", validators=[DataRequired()],
                         render_kw={'class': 'form-control'})
    pause_debut = TimeField("Début de pause", validators=[Optional()],
                           render_kw={'class': 'form-control'})
    pause_fin = TimeField("Fin de pause", validators=[Optional()],
                         render_kw={'class': 'form-control'})
    tolerance_retard = IntegerField("Tolérance retard (minutes)", validators=[Optional()],
                                   render_kw={'class': 'form-control'})
    tolerance_absence = IntegerField("Tolérance absence (minutes)", validators=[Optional()],
                                    render_kw={'class': 'form-control'})
    submit = SubmitField("Enregistrer", render_kw={'class': 'btn btn-primary'})

# ============================================================================
# FORMULAIRES POUR LE MODULE GESTION DE LA PAIE
# ============================================================================

# Constantes pour les mois
MONTHS = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}

class BulletinPaieForm(FlaskForm):
    """Formulaire principal pour créer/modifier un bulletin de paie"""
    employe_id = SelectField("Employé", coerce=int, validators=[DataRequired()],
                            render_kw={'class': 'form-select'})
    mois = SelectField("Mois", coerce=int, validators=[DataRequired()],
                      choices=[(i, MONTHS[i]) for i in range(1, 13)],
                      render_kw={'class': 'form-select'})
    annee = SelectField("Année", coerce=int, validators=[DataRequired()],
                       choices=[(i, str(i)) for i in range(2020, 2030)],
                       render_kw={'class': 'form-select'})
    
    # Période de travail
    periode_debut = DateField("Date de début", validators=[DataRequired()],
                             render_kw={'class': 'form-control'})
    periode_fin = DateField("Date de fin", validators=[DataRequired()],
                           render_kw={'class': 'form-control'})
    
    # Éléments de temps
    nb_jours_ouvres = IntegerField("Jours ouvrés", validators=[DataRequired(), NumberRange(min=1, max=31)],
                                  default=22, render_kw={'class': 'form-control'})
    nb_jours_travailles = FloatField("Jours travaillés", validators=[DataRequired(), NumberRange(min=0)],
                                    render_kw={'class': 'form-control', 'step': '0.5'})
    nb_heures_normales = FloatField("Heures normales", validators=[Optional(), NumberRange(min=0)],
                                   render_kw={'class': 'form-control', 'step': '0.25'})
    nb_heures_supplementaires = FloatField("Heures supplémentaires", validators=[Optional(), NumberRange(min=0)],
                                          render_kw={'class': 'form-control', 'step': '0.25'})
    nb_jours_conges = FloatField("Jours de congés", validators=[Optional(), NumberRange(min=0)],
                                render_kw={'class': 'form-control', 'step': '0.5'})
    nb_jours_absences = FloatField("Jours d'absences", validators=[Optional(), NumberRange(min=0)],
                                  render_kw={'class': 'form-control', 'step': '0.5'})
    
    # Éléments variables
    primes_bonus = FloatField("Primes et bonus", validators=[Optional(), NumberRange(min=0)],
                             render_kw={'class': 'form-control'})
    indemnites = FloatField("Indemnités", validators=[Optional(), NumberRange(min=0)],
                           render_kw={'class': 'form-control'})
    avantages_nature = FloatField("Avantages en nature", validators=[Optional(), NumberRange(min=0)],
                                 render_kw={'class': 'form-control'})
    retenues_diverses = FloatField("Retenues diverses", validators=[Optional(), NumberRange(min=0)],
                                  render_kw={'class': 'form-control'})
    
    # Paiement
    mode_paiement = SelectField("Mode de paiement", 
                               choices=[
                                   ('virement', 'Virement bancaire'),
                                   ('especes', 'Espèces'),
                                   ('cheque', 'Chèque')
                               ],
                               render_kw={'class': 'form-select'})
    reference_paiement = StringField("Référence de paiement", validators=[Optional()],
                                    render_kw={'class': 'form-control'})
    
    # Actions
    calculer = SubmitField("Calculer", render_kw={'class': 'btn btn-primary'})
    valider = SubmitField("Valider", render_kw={'class': 'btn btn-success'})
    enregistrer = SubmitField("Enregistrer", render_kw={'class': 'btn btn-outline-primary'})
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Utiliser les mois définis comme constante
        self.mois.choices = [(i, MONTHS[i]) for i in range(1, 13)]

class ElementPaieForm(FlaskForm):
    """Formulaire pour ajouter/modifier un élément de paie"""
    libelle = StringField("Libellé", validators=[DataRequired()],
                         render_kw={'class': 'form-control'})
    code = StringField("Code", validators=[Optional()],
                      render_kw={'class': 'form-control'})
    categorie = SelectField("Catégorie", validators=[DataRequired()],
                           choices=[
                               ('salaire', 'Salaire'),
                               ('prime', 'Prime'),
                               ('indemnite', 'Indemnité'),
                               ('avantage', 'Avantage en nature'),
                               ('cotisation', 'Cotisation'),
                               ('retenue', 'Retenue'),
                               ('autre', 'Autre')
                           ],
                           render_kw={'class': 'form-select'})
    type_element = SelectField("Type", validators=[DataRequired()],
                              choices=[
                                  ('gain', 'Gain'),
                                  ('retenue', 'Retenue')
                              ],
                              render_kw={'class': 'form-select'})
    
    # Calculs
    base_calcul = FloatField("Base de calcul", validators=[Optional(), NumberRange(min=0)],
                            render_kw={'class': 'form-control'})
    taux = FloatField("Taux (%)", validators=[Optional(), NumberRange(min=0)],
                     render_kw={'class': 'form-control', 'step': '0.01'})
    quantite = FloatField("Quantité", validators=[Optional(), NumberRange(min=0)],
                         default=1.0, render_kw={'class': 'form-control'})
    montant = FloatField("Montant", validators=[DataRequired(), NumberRange(min=0)],
                        render_kw={'class': 'form-control'})
    
    # Configuration
    imposable = BooleanField("Imposable", default=True,
                            render_kw={'class': 'form-check-input'})
    soumis_cotisations = BooleanField("Soumis aux cotisations", default=True,
                                     render_kw={'class': 'form-check-input'})
    
    commentaire = TextAreaField("Commentaire", validators=[Optional()],
                               render_kw={'class': 'form-control', 'rows': 3})
    
    submit = SubmitField("Enregistrer", render_kw={'class': 'btn btn-primary'})

class AvanceSalaireForm(FlaskForm):
    """Formulaire pour les avances sur salaire"""
    employe_id = SelectField("Employé", coerce=int, validators=[DataRequired()],
                            render_kw={'class': 'form-select'})
    montant_demande = FloatField("Montant demandé", validators=[DataRequired(), NumberRange(min=1)],
                                render_kw={'class': 'form-control'})
    montant_accorde = FloatField("Montant accordé", validators=[Optional(), NumberRange(min=0)],
                                render_kw={'class': 'form-control'})
    motif = TextAreaField("Motif", validators=[DataRequired()],
                         render_kw={'class': 'form-control', 'rows': 3})
    
    # Dates
    date_demande = DateField("Date de demande", validators=[DataRequired()],
                            default=date.today,
                            render_kw={'class': 'form-control'})
    date_accord = DateField("Date d'accord", validators=[Optional()],
                           render_kw={'class': 'form-control'})
    date_versement = DateField("Date de versement", validators=[Optional()],
                              render_kw={'class': 'form-control'})
    
    # Remboursement
    nb_mensualites = IntegerField("Nombre de mensualités", validators=[DataRequired(), NumberRange(min=1, max=12)],
                                 default=1, render_kw={'class': 'form-control'})
    
    # Approbation
    statut = SelectField("Statut", 
                        choices=[
                            ('demande', 'Demande'),
                            ('accorde', 'Accordé'),
                            ('verse', 'Versé'),
                            ('rembourse', 'Remboursé')
                        ],
                        render_kw={'class': 'form-select'})
    commentaire_approbation = TextAreaField("Commentaire d'approbation", validators=[Optional()],
                                           render_kw={'class': 'form-control', 'rows': 3})
    
    submit = SubmitField("Enregistrer", render_kw={'class': 'btn btn-primary'})

class TypeElementPaieForm(FlaskForm):
    """Formulaire pour configurer les types d'éléments de paie"""
    code = StringField("Code", validators=[DataRequired()],
                      render_kw={'class': 'form-control'})
    libelle = StringField("Libellé", validators=[DataRequired()],
                         render_kw={'class': 'form-control'})
    description = TextAreaField("Description", validators=[Optional()],
                               render_kw={'class': 'form-control', 'rows': 3})
    
    # Configuration
    categorie = SelectField("Catégorie", validators=[DataRequired()],
                           choices=[
                               ('salaire', 'Salaire'),
                               ('prime', 'Prime'),
                               ('indemnite', 'Indemnité'),
                               ('avantage', 'Avantage en nature'),
                               ('cotisation', 'Cotisation'),
                               ('retenue', 'Retenue'),
                               ('autre', 'Autre')
                           ],
                           render_kw={'class': 'form-select'})
    type_element = SelectField("Type", validators=[DataRequired()],
                              choices=[
                                  ('gain', 'Gain'),
                                  ('retenue', 'Retenue')
                              ],
                              render_kw={'class': 'form-select'})
    mode_calcul = SelectField("Mode de calcul", validators=[DataRequired()],
                             choices=[
                                 ('montant_fixe', 'Montant fixe'),
                                 ('pourcentage', 'Pourcentage'),
                                 ('formule', 'Formule')
                             ],
                             render_kw={'class': 'form-select'})
    
    # Paramètres par défaut
    taux_defaut = FloatField("Taux par défaut (%)", validators=[Optional(), NumberRange(min=0)],
                            render_kw={'class': 'form-control', 'step': '0.01'})
    montant_defaut = FloatField("Montant par défaut", validators=[Optional(), NumberRange(min=0)],
                               render_kw={'class': 'form-control'})
    base_calcul_defaut = SelectField("Base de calcul par défaut",
                                    choices=[
                                        ('salaire_brut', 'Salaire brut'),
                                        ('salaire_base', 'Salaire de base'),
                                        ('salaire_net', 'Salaire net'),
                                        ('salaire_imposable', 'Salaire imposable')
                                    ],
                                    render_kw={'class': 'form-select'})
    
    # Propriétés
    imposable = BooleanField("Imposable", default=True,
                            render_kw={'class': 'form-check-input'})
    soumis_cotisations = BooleanField("Soumis aux cotisations", default=True,
                                     render_kw={'class': 'form-check-input'})
    obligatoire = BooleanField("Obligatoire", default=False,
                              render_kw={'class': 'form-check-input'})
    actif = BooleanField("Actif", default=True,
                        render_kw={'class': 'form-check-input'})
    
    ordre_affichage = IntegerField("Ordre d'affichage", validators=[Optional(), NumberRange(min=0)],
                                  default=0, render_kw={'class': 'form-control'})
    
    submit = SubmitField("Enregistrer", render_kw={'class': 'btn btn-primary'})

class ParametreCalculPaieForm(FlaskForm):
    """Formulaire pour les paramètres de calcul individuels"""
    employe_id = SelectField("Employé", coerce=int, validators=[DataRequired()],
                            render_kw={'class': 'form-select'})
    
    # Paramètres salariaux
    salaire_base_mensuel = FloatField("Salaire de base mensuel", validators=[Optional(), NumberRange(min=0)],
                                     render_kw={'class': 'form-control'})
    taux_horaire = FloatField("Taux horaire", validators=[Optional(), NumberRange(min=0)],
                             render_kw={'class': 'form-control'})
    coefficient_anciennete = FloatField("Coefficient d'ancienneté", validators=[Optional(), NumberRange(min=0)],
                                       default=1.0, render_kw={'class': 'form-control', 'step': '0.01'})
    
    # Primes régulières
    prime_anciennete = FloatField("Prime d'ancienneté", validators=[Optional(), NumberRange(min=0)],
                                 default=0.0, render_kw={'class': 'form-control'})
    prime_fonction = FloatField("Prime de fonction", validators=[Optional(), NumberRange(min=0)],
                               default=0.0, render_kw={'class': 'form-control'})
    prime_transport = FloatField("Prime de transport", validators=[Optional(), NumberRange(min=0)],
                                default=0.0, render_kw={'class': 'form-control'})
    indemnite_logement = FloatField("Indemnité de logement", validators=[Optional(), NumberRange(min=0)],
                                   default=0.0, render_kw={'class': 'form-control'})
    
    # Avantages en nature
    avantage_voiture = FloatField("Avantage voiture", validators=[Optional(), NumberRange(min=0)],
                                 default=0.0, render_kw={'class': 'form-control'})
    avantage_logement = FloatField("Avantage logement", validators=[Optional(), NumberRange(min=0)],
                                  default=0.0, render_kw={'class': 'form-control'})
    avantage_telephone = FloatField("Avantage téléphone", validators=[Optional(), NumberRange(min=0)],
                                   default=0.0, render_kw={'class': 'form-control'})
    
    # Paramètres fiscaux
    nombre_parts = FloatField("Nombre de parts fiscales", validators=[Optional(), NumberRange(min=0.5)],
                             default=1.0, render_kw={'class': 'form-control', 'step': '0.5'})
    exoneration_impot = BooleanField("Exonération d'impôt", default=False,
                                    render_kw={'class': 'form-check-input'})
    taux_impot_specifique = FloatField("Taux d'impôt spécifique (%)", validators=[Optional(), NumberRange(min=0, max=100)],
                                      render_kw={'class': 'form-control', 'step': '0.01'})
    
    # Paramètres de cotisation
    exoneration_cnps = BooleanField("Exonération CNPS", default=False,
                                   render_kw={'class': 'form-check-input'})
    
    # Dates d'effet
    date_effet = DateField("Date d'effet", validators=[DataRequired()],
                          default=date.today,
                          render_kw={'class': 'form-control'})
    date_fin = DateField("Date de fin", validators=[Optional()],
                        render_kw={'class': 'form-control'})
    
    submit = SubmitField("Enregistrer", render_kw={'class': 'btn btn-primary'})

class RapportPaieForm(FlaskForm):
    """Formulaire pour la génération de rapports de paie"""
    type_rapport = SelectField("Type de rapport", validators=[DataRequired()],
                              choices=[
                                  ('bulletin_individuel', 'Bulletin individuel'),
                                  ('liste_paie', 'Liste de paie'),
                                  ('synthese_mensuelle', 'Synthèse mensuelle'),
                                  ('cotisations', 'Rapport des cotisations'),
                                  ('charges_sociales', 'Charges sociales'),
                                  ('masse_salariale', 'Masse salariale'),
                                  ('historique_paie', 'Historique des paies'),
                                  ('avances_salaires', 'Avances sur salaires'),
                                  ('comparatif_periodes', 'Comparatif entre périodes')
                              ],
                              render_kw={'class': 'form-select'})
    
    # Période
    mois = SelectField("Mois", coerce=int, validators=[DataRequired()],
                      choices=[(i, MONTHS[i]) for i in range(1, 13)],
                      render_kw={'class': 'form-select'})
    annee = SelectField("Année", coerce=int, validators=[DataRequired()],
                       choices=[(i, str(i)) for i in range(2020, 2030)],
                       render_kw={'class': 'form-select'})
    
    # Filtres
    employes = SelectMultipleField("Employés", coerce=int, validators=[Optional()],
                                  render_kw={'class': 'form-select', 'multiple': True})
    departements = SelectMultipleField("Départements", validators=[Optional()],
                                      render_kw={'class': 'form-select', 'multiple': True})
    statuts = SelectMultipleField("Statuts", validators=[Optional()],
                                 choices=[
                                     ('', 'Tous les statuts'),
                                     ('actif', 'Actif'),
                                     ('inactif', 'Inactif'),
                                     ('conge', 'En congé')
                                 ],
                                 render_kw={'class': 'form-select', 'multiple': True})
    
    # Format d'export
    format_export = SelectField("Format d'export", validators=[DataRequired()],
                               choices=[
                                   ('pdf', 'PDF'),
                                   ('excel', 'Excel'),
                                   ('csv', 'CSV')
                               ],
                               render_kw={'class': 'form-select'})
    
    # Options avancées
    inclure_details = BooleanField("Inclure les détails", default=True,
                                  render_kw={'class': 'form-check-input'})
    inclure_cotisations = BooleanField("Inclure les cotisations", default=True,
                                      render_kw={'class': 'form-check-input'})
    inclure_avances = BooleanField("Inclure les avances", default=False,
                                  render_kw={'class': 'form-check-input'})
    
    submit = SubmitField("Générer le rapport", render_kw={'class': 'btn btn-primary'})
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Utiliser les mois définis comme constante
        self.mois.choices = [(i, MONTHS[i]) for i in range(1, 13)]

class CalculPaieForm(FlaskForm):
    """Formulaire pour le calcul automatique des paies"""
    periode = SelectField("Période", validators=[DataRequired()],
                         choices=[
                             ('mensuelle', 'Mensuelle'),
                             ('bimensuelle', 'Bimensuelle'),
                             ('hebdomadaire', 'Hebdomadaire')
                         ],
                         render_kw={'class': 'form-select'})
    
    mois = SelectField("Mois", coerce=int, validators=[DataRequired()],
                      choices=[(i, MONTHS[i]) for i in range(1, 13)],
                      render_kw={'class': 'form-select'})
    annee = SelectField("Année", coerce=int, validators=[DataRequired()],
                       choices=[(i, str(i)) for i in range(2020, 2030)],
                       render_kw={'class': 'form-select'})
    
    # Filtres
    employes = SelectMultipleField("Employés", coerce=int, validators=[Optional()],
                                  render_kw={'class': 'form-select', 'multiple': True})
    departements = SelectMultipleField("Départements", validators=[Optional()],
                                      render_kw={'class': 'form-select', 'multiple': True})
    
    # Options de calcul
    recalculer_existants = BooleanField("Recalculer les bulletins existants", default=False,
                                       render_kw={'class': 'form-check-input'})
    inclure_heures_sup = BooleanField("Inclure les heures supplémentaires", default=True,
                                     render_kw={'class': 'form-check-input'})
    inclure_absences = BooleanField("Déduire les absences", default=True,
                                   render_kw={'class': 'form-check-input'})
    inclure_avances = BooleanField("Déduire les avances", default=True,
                                  render_kw={'class': 'form-check-input'})
    
    submit = SubmitField("Calculer les paies", render_kw={'class': 'btn btn-primary'})
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Utiliser les mois définis comme constante
        self.mois.choices = [(i, MONTHS[i]) for i in range(1, 13)]

class EmployeeDocumentForm(FlaskForm):
    """Formulaire pour ajouter/modifier des documents d'employé"""
    type_document = SelectField("Type de document", validators=[DataRequired()],
                               choices=[
                                   ('cv', 'CV'),
                                   ('contrat', 'Contrat'),
                                   ('diplome', 'Diplôme'),
                                   ('attestation', 'Attestation'),
                                   ('autre', 'Autre')
                               ],
                               render_kw={'class': 'form-select'})
    nom_document = StringField("Nom du document", validators=[DataRequired()],
                              render_kw={'class': 'form-control'})
    description = TextAreaField("Description", validators=[Optional()],
                               render_kw={'class': 'form-control', 'rows': 3})
    document = FileField("Fichier", validators=[Optional()],
                        render_kw={'class': 'form-control'})
    submit = SubmitField("Enregistrer", render_kw={'class': 'btn btn-primary'})

class EmployeeSearchForm(FlaskForm):
    """Formulaire de recherche d'employés"""
    search = StringField("Rechercher", validators=[Optional()],
                        render_kw={'class': 'form-control', 'placeholder': 'Nom, prénom, matricule...'})
    departement = SelectField("Département", validators=[Optional()],
                             choices=[('', 'Tous les départements')],
                             render_kw={'class': 'form-select'})
    poste = SelectField("Poste", validators=[Optional()],
                       choices=[('', 'Tous les postes')],
                       render_kw={'class': 'form-select'})
    statut = SelectField("Statut", validators=[Optional()],
                        choices=[
                            ('', 'Tous les statuts'),
                            ('actif', 'Actif'),
                            ('inactif', 'Inactif'),
                            ('conge', 'En congé')
                        ],
                        render_kw={'class': 'form-select'})
    submit = SubmitField("Rechercher", render_kw={'class': 'btn btn-primary'})

class EvaluationForm(FlaskForm):
    """Formulaire pour créer/modifier une évaluation"""
    employe_id = SelectField("Employé", coerce=int, validators=[DataRequired()],
                            render_kw={'class': 'form-select'})
    evaluateur_id = SelectField("Évaluateur", coerce=int, validators=[DataRequired()],
                               render_kw={'class': 'form-select'})
    template_id = SelectField("Template", coerce=int, validators=[DataRequired()],
                             render_kw={'class': 'form-select'})
    periode_debut = DateField("Date de début", validators=[DataRequired()],
                             render_kw={'class': 'form-control'})
    periode_fin = DateField("Date de fin", validators=[DataRequired()],
                           render_kw={'class': 'form-control'})
    type_evaluation = SelectField("Type d'évaluation", validators=[DataRequired()],
                                 choices=[
                                     ('annuelle', 'Annuelle'),
                                     ('semestrielle', 'Semestrielle'),
                                     ('trimestrielle', 'Trimestrielle'),
                                     ('probatoire', 'Probatoire'),
                                     ('autre', 'Autre')
                                 ],
                                 render_kw={'class': 'form-select'})
    commentaires = TextAreaField("Commentaires", validators=[Optional()],
                                render_kw={'class': 'form-control', 'rows': 5})
    submit = SubmitField("Enregistrer", render_kw={'class': 'btn btn-primary'})

class TemplateEvaluationForm(FlaskForm):
    """Formulaire pour créer/modifier un template d'évaluation"""
    nom = StringField("Nom du template", validators=[DataRequired()],
                     render_kw={'class': 'form-control'})
    description = TextAreaField("Description", validators=[Optional()],
                               render_kw={'class': 'form-control', 'rows': 3})
    type_template = SelectField("Type de template", validators=[DataRequired()],
                               choices=[
                                   ('annuelle', 'Annuelle'),
                                   ('semestrielle', 'Semestrielle'),
                                   ('trimestrielle', 'Trimestrielle'),
                                   ('probatoire', 'Probatoire'),
                                   ('autre', 'Autre')
                               ],
                               render_kw={'class': 'form-select'})
    actif = BooleanField("Template actif", render_kw={'class': 'form-check-input'})
    submit = SubmitField("Enregistrer", render_kw={'class': 'btn btn-primary'})

class CritereEvaluationForm(FlaskForm):
    """Formulaire pour créer/modifier un critère d'évaluation"""
    nom = StringField("Nom du critère", validators=[DataRequired()],
                     render_kw={'class': 'form-control'})
    description = TextAreaField("Description", validators=[Optional()],
                               render_kw={'class': 'form-control', 'rows': 3})
    poids = IntegerField("Poids (%)", validators=[DataRequired(), NumberRange(min=0, max=100)],
                        render_kw={'class': 'form-control', 'min': 0, 'max': 100})
    template_id = SelectField("Template", coerce=int, validators=[DataRequired()],
                             render_kw={'class': 'form-select'})
    type_critere = SelectField("Type de critère", validators=[DataRequired()],
                              choices=[
                                  ('competence', 'Compétence'),
                                  ('performance', 'Performance'),
                                  ('comportement', 'Comportement'),
                                  ('objectif', 'Objectif'),
                                  ('autre', 'Autre')
                              ],
                              render_kw={'class': 'form-select'})
    submit = SubmitField("Enregistrer", render_kw={'class': 'btn btn-primary'})

class ObjectifEmployeForm(FlaskForm):
    """Formulaire pour créer/modifier un objectif d'employé"""
    employe_id = SelectField("Employé", coerce=int, validators=[DataRequired()],
                            render_kw={'class': 'form-select'})
    titre = StringField("Titre de l'objectif", validators=[DataRequired()],
                       render_kw={'class': 'form-control'})
    description = TextAreaField("Description", validators=[DataRequired()],
                               render_kw={'class': 'form-control', 'rows': 4})
    date_limite = DateField("Date limite", validators=[DataRequired()],
                           render_kw={'class': 'form-control'})
    priorite = SelectField("Priorité", validators=[DataRequired()],
                          choices=[
                              ('basse', 'Basse'),
                              ('moyenne', 'Moyenne'),
                              ('haute', 'Haute'),
                              ('critique', 'Critique')
                          ],
                          render_kw={'class': 'form-select'})
    statut = SelectField("Statut", validators=[DataRequired()],
                        choices=[
                            ('en_cours', 'En cours'),
                            ('terminé', 'Terminé'),
                            ('reporté', 'Reporté'),
                            ('annulé', 'Annulé')
                        ],
                        render_kw={'class': 'form-select'})
    commentaires = TextAreaField("Commentaires", validators=[Optional()],
                                render_kw={'class': 'form-control', 'rows': 3})
    submit = SubmitField("Enregistrer", render_kw={'class': 'btn btn-primary'})

class RapportEvaluationForm(FlaskForm):
    """Formulaire pour générer des rapports d'évaluation"""
    periode_debut = DateField("Date de début", validators=[DataRequired()],
                             render_kw={'class': 'form-control'})
    periode_fin = DateField("Date de fin", validators=[DataRequired()],
                           render_kw={'class': 'form-control'})
    type_evaluation = SelectField("Type d'évaluation", validators=[Optional()],
                                 choices=[
                                     ('', 'Tous les types'),
                                     ('annuelle', 'Annuelle'),
                                     ('semestrielle', 'Semestrielle'),
                                     ('trimestrielle', 'Trimestrielle'),
                                     ('probatoire', 'Probatoire'),
                                     ('autre', 'Autre')
                                 ],
                                 render_kw={'class': 'form-select'})
    departement = SelectField("Département", validators=[Optional()],
                             choices=[('', 'Tous les départements')],
                             render_kw={'class': 'form-select'})
    format_rapport = SelectField("Format", validators=[DataRequired()],
                                choices=[
                                    ('pdf', 'PDF'),
                                    ('excel', 'Excel'),
                                    ('csv', 'CSV')
                                ],
                                render_kw={'class': 'form-select'})
    submit = SubmitField("Générer le rapport", render_kw={'class': 'btn btn-primary'})

class ResetPasswordRequestForm(FlaskForm):
    """Formulaire de demande de réinitialisation du mot de passe"""
    email = StringField("Email", validators=[DataRequired(), Email()],
                       render_kw={'class': 'form-control', 'placeholder': 'Votre adresse email'})
    submit = SubmitField("Envoyer", render_kw={'class': 'btn btn-primary'})

class ResetPasswordForm(FlaskForm):
    """Formulaire de réinitialisation du mot de passe"""
    password = PasswordField("Nouveau mot de passe", validators=[DataRequired()],
                            render_kw={'class': 'form-control', 'placeholder': 'Nouveau mot de passe'})
    confirm_password = PasswordField("Confirmer le mot de passe", 
                                   validators=[DataRequired(), EqualTo('password')],
                                   render_kw={'class': 'form-control', 'placeholder': 'Confirmer le mot de passe'})
    submit = SubmitField("Réinitialiser", render_kw={'class': 'btn btn-primary'})

class ChangePasswordForm(FlaskForm):
    """Formulaire de changement de mot de passe"""
    current_password = PasswordField("Mot de passe actuel", validators=[DataRequired()],
                                    render_kw={'class': 'form-control', 'placeholder': 'Mot de passe actuel'})
    new_password = PasswordField("Nouveau mot de passe", validators=[DataRequired()],
                                render_kw={'class': 'form-control', 'placeholder': 'Nouveau mot de passe'})
    confirm_password = PasswordField("Confirmer le nouveau mot de passe", 
                                   validators=[DataRequired(), EqualTo('new_password')],
                                   render_kw={'class': 'form-control', 'placeholder': 'Confirmer le nouveau mot de passe'})
    submit = SubmitField("Changer", render_kw={'class': 'btn btn-primary'})

class PointageForm(FlaskForm):
    """Formulaire pour l'enregistrement des pointages"""
    employe_id = SelectField("Employé", coerce=int, validators=[DataRequired()],
                            render_kw={'class': 'form-select'})
    date_pointage = DateField("Date", validators=[DataRequired()],
                             render_kw={'class': 'form-control'})
    heure_pointage = TimeField("Heure", validators=[DataRequired()],
                              render_kw={'class': 'form-control'})
    type_pointage = SelectField("Type de pointage", 
                               choices=[('entree', 'Entrée'), ('sortie', 'Sortie'), 
                                       ('pause_debut', 'Début pause'), ('pause_fin', 'Fin pause')],
                               validators=[DataRequired()],
                               render_kw={'class': 'form-select'})
    methode = SelectField("Méthode", 
                         choices=[('manuel', 'Manuel'), ('qr_code', 'QR Code'), 
                                 ('badge', 'Badge'), ('biometrie', 'Biométrie'), ('gps', 'GPS')],
                         default='manuel',
                         render_kw={'class': 'form-select'})
    commentaire = TextAreaField("Commentaire", render_kw={'class': 'form-control', 'rows': 3})
    submit = SubmitField("Enregistrer", render_kw={'class': 'btn btn-primary'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import Employee
        self.employe_id.choices = [(e.id, f"{e.nom} {e.prenom or ''}") 
                                  for e in Employee.query.filter_by(statut='Actif').order_by(Employee.nom).all()]

class HeuresTravailForm(FlaskForm):
    """Formulaire pour la gestion des heures de travail"""
    employe_id = SelectField("Employé", coerce=int, validators=[DataRequired()],
                            render_kw={'class': 'form-select'})
    date_travail = DateField("Date", validators=[DataRequired()],
                            render_kw={'class': 'form-control'})
    heure_arrivee = TimeField("Heure d'arrivée", 
                             render_kw={'class': 'form-control'})
    heure_depart = TimeField("Heure de départ", 
                            render_kw={'class': 'form-control'})
    pause_duree = IntegerField("Durée pause (minutes)", default=0,
                              render_kw={'class': 'form-control'})
    heures_travaillees = FloatField("Heures travaillées", 
                                   render_kw={'class': 'form-control'})
    heures_supplementaires = FloatField("Heures supplémentaires", default=0,
                                       render_kw={'class': 'form-control'})
    justification = TextAreaField("Justification", render_kw={'class': 'form-control', 'rows': 3})
    submit = SubmitField("Enregistrer", render_kw={'class': 'btn btn-primary'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import Employee
        self.employe_id.choices = [(e.id, f"{e.nom} {e.prenom or ''}") 
                                  for e in Employee.query.filter_by(statut='Actif').order_by(Employee.nom).all()]

class RapportPresenceForm(FlaskForm):
    """Formulaire pour la génération de rapports de présence"""
    employe_id = SelectField("Employé", coerce=int, validators=[Optional()],
                            render_kw={'class': 'form-select'})
    date_debut = DateField("Date de début", validators=[DataRequired()],
                          render_kw={'class': 'form-control'})
    date_fin = DateField("Date de fin", validators=[DataRequired()],
                        render_kw={'class': 'form-control'})
    departement = SelectField("Département", validators=[Optional()],
                             render_kw={'class': 'form-select'})
    type_rapport = SelectField("Type de rapport",
                              choices=[('resume', 'Résumé'), ('detaille', 'Détaillé'), 
                                      ('retards', 'Retards'), ('absences', 'Absences'),
                                      ('heures_sup', 'Heures supplémentaires')],
                              validators=[DataRequired()],
                              render_kw={'class': 'form-select'})
    format_export = SelectField("Format d'export",
                               choices=[('pdf', 'PDF'), ('excel', 'Excel'), ('csv', 'CSV')],
                               default='pdf',
                               render_kw={'class': 'form-select'})
    submit = SubmitField("Générer le rapport", render_kw={'class': 'btn btn-primary'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import Employee
        
        # Tous les employés avec option "Tous"
        employees = Employee.query.filter_by(statut='Actif').order_by(Employee.nom).all()
        self.employe_id.choices = [('', 'Tous les employés')] + [(e.id, f"{e.nom} {e.prenom or ''}") for e in employees]
        
        # Départements uniques
        departements = db.session.query(Employee.departement).filter(Employee.departement.isnot(None)).distinct().all()
        self.departement.choices = [('', 'Tous les départements')] + [(d[0], d[0]) for d in departements]
