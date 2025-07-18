from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request, jsonify, send_file
from flask_login import login_required, current_user
from app.models import (Conge, Employee, Absence, 
                       TypeConge, SoldeConge, HistoriqueConge, Utilisateur,
                       Presence, ParametrePresence, Pointage, HeuresTravail, NotificationPresence)
from app.forms import (AbsenceForm, CongeForm, ApprovalCongeForm, TypeCongeForm, SoldeCongeForm,
                      ParametrePresenceForm, PointageForm, HeuresTravailForm, RapportPresenceForm)
from app import db
import os
from datetime import datetime, date, timedelta, time
from app.utils.permissions import permission_requise
from werkzeug.utils import secure_filename
from io import BytesIO
import pandas as pd
from weasyprint import HTML
from sqlalchemy import and_, or_, func, extract
from collections import defaultdict
import json
from calendar import monthrange
from app.utils.email_service import email_service

conges_temps_bp = Blueprint('conges_temps', __name__, template_folder='../templates/conges_temps')

def save_conge_file(file, folder):
    """Sauvegarde un fichier de congé et retourne le nom du fichier"""
    if file and file.filename:
        filename = secure_filename(file.filename)
        # Ajouter timestamp pour éviter les conflits
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        # Créer le dossier s'il n'existe pas
        upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'conges', folder)
        os.makedirs(upload_path, exist_ok=True)
        
        # Sauvegarder le fichier
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        return filename
    return None

def log_conge_action(conge_id, action, ancien_statut=None, nouveau_statut=None, commentaire=None):
    """Enregistre une action dans l'historique des congés"""
    try:
        historique = HistoriqueConge(
            conge_id=conge_id,
            action=action,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            commentaire=commentaire,
            utilisateur_id=current_user.id
        )
        db.session.add(historique)
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de l'historique: {e}")

def calculer_jours_ouvrables(date_debut, date_fin):
    """Calcule le nombre de jours ouvrables entre deux dates"""
    if not date_debut or not date_fin:
        return 0
    
    # Simple calcul - à améliorer pour exclure les weekends et jours fériés
    jours = (date_fin - date_debut).days + 1
    return max(0, jours)

def mettre_a_jour_solde(employe_id, annee, jours_pris):
    """Met à jour le solde de congé d'un employé"""
    solde = SoldeConge.query.filter_by(employe_id=employe_id, annee=annee).first()
    if solde:
        solde.jours_pris += jours_pris
        solde.date_maj = datetime.utcnow()
    else:
        # Créer un nouveau solde si nécessaire
        solde = SoldeConge(
            employe_id=employe_id,
            annee=annee,
            jours_alloues=25,  # Valeur par défaut
            jours_pris=jours_pris
        )
        db.session.add(solde)

# ============= ROUTES PRINCIPALES =============

@conges_temps_bp.route('/conges-temps')
@login_required
@permission_requise('absences_conges')
def index():
    """Page d'accueil du module congés et temps"""
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get paginated data for the index page
    conges = Conge.query.order_by(Conge.date_demande.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    employes = Employee.query.filter_by(statut='Actif').all()
    types_conges = TypeConge.query.filter_by(actif=True).order_by(TypeConge.ordre_affichage).all()
    
    # Statistiques
    stats = {
        'total': Conge.query.count(),
        'en_attente': Conge.query.filter_by(statut='En attente').count(),
        'approuves': Conge.query.filter_by(statut='Approuvé').count(),
        'rejetes': Conge.query.filter_by(statut='Rejeté').count()
    }
    
    return render_template('conges_temps/index.html', 
                         conges=conges, 
                         employes=employes, 
                         types_conges=types_conges,
                         stats=stats)

# ============= GESTION DES CONGÉS =============

@conges_temps_bp.route('/conges-temps/conges')
@login_required
@permission_requise('absences_conges')
def list_conges():
    """Liste des congés avec filtres"""
    # Filtres depuis les paramètres de requête
    statut = request.args.get('statut')
    employe_id = request.args.get('employe_id')
    type_conge = request.args.get('type_conge')
    
    # Construction de la requête
    query = Conge.query.join(Employee)
    
    if statut:
        query = query.filter(Conge.statut == statut)
    if employe_id:
        query = query.filter(Conge.employe_id == employe_id)
    if type_conge:
        query = query.filter(Conge.type_conge == type_conge)
    
    conges = query.order_by(Conge.date_demande.desc()).all()
    
    # Données pour les filtres
    employes = Employee.query.filter_by(statut='Actif').all()
    types_conges = TypeConge.query.filter_by(actif=True).order_by(TypeConge.ordre_affichage).all()
    
    # Statistiques
    stats = {
        'total': Conge.query.count(),
        'en_attente': Conge.query.filter_by(statut='En attente').count(),
        'approuves': Conge.query.filter_by(statut='Approuvé').count(),
        'rejetes': Conge.query.filter_by(statut='Rejeté').count()
    }
    
    return render_template('conges_temps/conges.html', 
                         conges=conges, 
                         employes=employes, 
                         types_conges=types_conges,
                         stats=stats)

@conges_temps_bp.route('/conges-temps/conges/add', methods=['GET', 'POST'])
@login_required
@permission_requise('absences_conges')
def add_conge():
    """Ajouter une demande de congé"""
    form = CongeForm()
    
    # Charger les choix pour les SelectField
    form.employe_id.choices = [(0, 'Sélectionner un employé')] + [(emp.id, emp.nom_complet) for emp in Employee.query.filter_by(statut='Actif').all()]
    
    # Charger les types de congés ou utiliser des valeurs par défaut
    types_conges = TypeConge.query.filter_by(actif=True).order_by(TypeConge.ordre_affichage).all()
    if types_conges:
        form.type_conge.choices = [(tc.nom, tc.nom) for tc in types_conges]
    else:
        # Types par défaut si aucun n'est configuré
        form.type_conge.choices = [
            ('Congé annuel', 'Congé annuel'),
            ('Maladie', 'Maladie'),
            ('Maternité/Paternité', 'Maternité/Paternité'),
            ('Formation', 'Formation'),
            ('Exceptionnel', 'Exceptionnel')
        ]
    
    form.remplacant_id.choices = [(0, 'Aucun remplaçant')] + [(emp.id, emp.nom_complet) for emp in Employee.query.filter_by(statut='Actif').all()]
    
    if form.validate_on_submit():
        try:
            # Calculer le nombre de jours
            nb_jours = calculer_jours_ouvrables(form.date_debut.data, form.date_fin.data)
            
            # Traiter le fichier justificatif
            justificatif_filename = None
            if form.justificatif.data:
                justificatif_filename = save_conge_file(form.justificatif.data, 'justificatifs')
            
            # Créer le congé
            conge = Conge(
                employe_id=form.employe_id.data,
                type_conge=form.type_conge.data,
                date_debut=form.date_debut.data,
                date_fin=form.date_fin.data,
                nombre_jours=nb_jours,
                motif=form.motif.data,
                remplacant_id=form.remplacant_id.data if form.remplacant_id.data != 0 else None,
                justificatif=justificatif_filename,
                demandeur_id=current_user.id
            )
            
            db.session.add(conge)
            db.session.flush()
            
            # Enregistrer dans l'historique
            log_conge_action(conge.id, 'CREATE', None, 'En attente', 'Demande de congé créée')
            
            db.session.commit()
            
            # Envoyer notification email
            try:
                email_service.notify_leave_request(conge.id)
            except Exception as e:
                print(f"Erreur envoi email: {e}")
            
            flash(f"Demande de congé créée avec succès ({nb_jours} jours)", "success")
            return redirect(url_for('conges_temps.list_conges'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création: {str(e)}", "danger")
    
    return render_template('conges_temps/conge_form.html', form=form, title="Nouvelle demande de congé")

@conges_temps_bp.route('/conges-temps/conges/<int:id>')
@login_required
@permission_requise('absences_conges')
def detail_conge(id):
    """Détail d'un congé"""
    conge = Conge.query.get_or_404(id)
    historique = HistoriqueConge.query.filter_by(conge_id=id).order_by(HistoriqueConge.date_action.desc()).all()
    approval_form = ApprovalCongeForm()
    
    return render_template('conges_temps/conge_detail.html', 
                         conge=conge, 
                         historique=historique,
                         approval_form=approval_form)

@conges_temps_bp.route('/conges-temps/conges/<int:id>/approve', methods=['POST'])
@login_required
@permission_requise('absences_conges')
def approve_conge(id):
    """Approuver ou rejeter un congé"""
    conge = Conge.query.get_or_404(id)
    form = ApprovalCongeForm()
    
    if form.validate_on_submit():
        try:
            ancien_statut = conge.statut
            nouveau_statut = form.statut.data
            
            conge.statut = nouveau_statut
            conge.approbateur_id = current_user.id
            conge.date_approbation = datetime.utcnow()
            conge.commentaire_approbateur = form.commentaire.data
            
            # Si approuvé, déduire du solde de congé
            if nouveau_statut == 'Approuvé':
                mettre_a_jour_solde(conge.employe_id, conge.date_debut.year, conge.nombre_jours)
            
            # Enregistrer dans l'historique
            action = 'APPROVE' if nouveau_statut == 'Approuvé' else 'REJECT'
            log_conge_action(conge.id, action, ancien_statut, nouveau_statut, form.commentaire.data)
            
            db.session.commit()
            flash(f"Congé {nouveau_statut.lower()} avec succès", "success")
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'approbation: {str(e)}", "danger")
    
    return redirect(url_for('conges_temps.detail_conge', id=id))

# ============= APPROBATION DES CONGÉS =============

@conges_temps_bp.route('/conges-temps/conges/<int:id>/approuver', methods=['POST'])
@login_required
@permission_requise('absences_conges')
def approuver_conge(id):
    """Approuver une demande de congé"""
    conge = Conge.query.get_or_404(id)
    
    try:
        ancien_statut = conge.statut
        conge.statut = 'Approuvé'
        conge.approbateur_id = current_user.id
        conge.date_approbation = datetime.utcnow()
        
        # Enregistrer dans l'historique
        log_conge_action(conge.id, 'APPROVE', ancien_statut, 'Approuvé', 'Demande approuvée')
        
        db.session.commit()
        
        # Envoyer notification email
        try:
            email_service.notify_leave_decision(conge.id, 'Approuvé')
        except Exception as e:
            print(f"Erreur envoi email: {e}")
        
        flash("Demande de congé approuvée avec succès", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'approbation: {str(e)}", "danger")
    
    return redirect(url_for('conges_temps.list_conges'))

@conges_temps_bp.route('/conges-temps/conges/<int:id>/rejeter', methods=['POST'])
@login_required
@permission_requise('absences_conges')
def rejeter_conge(id):
    """Rejeter une demande de congé"""
    conge = Conge.query.get_or_404(id)
    
    try:
        ancien_statut = conge.statut
        conge.statut = 'Rejeté'
        conge.approbateur_id = current_user.id
        conge.date_approbation = datetime.utcnow()
        
        # Récupérer le motif de rejet
        motif_rejet = request.form.get('motif_rejet', '')
        conge.commentaire_approbateur = motif_rejet
        
        # Enregistrer dans l'historique
        log_conge_action(conge.id, 'REJECT', ancien_statut, 'Rejeté', motif_rejet)
        
        db.session.commit()
        
        # Envoyer notification email
        try:
            email_service.notify_leave_decision(conge.id, 'Rejeté')
        except Exception as e:
            print(f"Erreur envoi email: {e}")
        
        flash("Demande de congé rejetée", "warning")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors du rejet: {str(e)}", "danger")
    
    return redirect(url_for('conges_temps.list_conges'))

@conges_temps_bp.route('/conges-temps/demandes/<int:id>/valider', methods=['POST'])
@login_required
@permission_requise('absences_conges')
def valider_demande_conge(id):
    """Valider une demande de congé (alias pour approuver)"""
    return approuver_conge(id)

@conges_temps_bp.route('/conges-temps/demandes/<int:id>/rejeter', methods=['POST'])
@login_required
@permission_requise('absences_conges')
def rejeter_demande_conge(id):
    """Rejeter une demande de congé (alias pour rejeter)"""
    return rejeter_conge(id)

# ============= GESTION DES ABSENCES =============

@conges_temps_bp.route('/conges-temps/absences')
@login_required
@permission_requise('absences_conges')
def list_absences():
    """Liste des absences"""
    form = AbsenceForm()
    form.employe_id.choices = [(0, 'Sélectionner un employé')] + [(emp.id, emp.nom_complet) for emp in Employee.query.filter_by(statut='Actif').all()]
    
    # Filtres
    employe_id = request.args.get('employe_id')
    statut = request.args.get('statut')
    
    query = Absence.query.join(Employee)
    
    if employe_id:
        query = query.filter(Absence.employe_id == employe_id)
    if statut:
        query = query.filter(Absence.statut == statut)
    
    absences = query.order_by(Absence.date_absence.desc()).all()
    employes = Employee.query.filter_by(statut='Actif').all()
    
    return render_template('conges_temps/absences.html', 
                         form=form, 
                         absences=absences,
                         employes=employes)

@conges_temps_bp.route('/conges-temps/absences/add', methods=['POST'])
@login_required
@permission_requise('absences_conges')
def add_absence():
    """Ajouter une absence"""
    form = AbsenceForm()
    form.employe_id.choices = [(emp.id, emp.nom_complet) for emp in Employee.query.filter_by(statut='Actif').all()]
    
    if form.validate_on_submit():
        try:
            # Traiter le fichier justificatif
            justificatif_filename = None
            if form.justificatif.data:
                justificatif_filename = save_conge_file(form.justificatif.data, 'absences')
            
            absence = Absence(
                employe_id=form.employe_id.data,
                date_absence=form.date_absence.data,
                motif=form.motif.data,
                justificatif=justificatif_filename,
                statut="En attente"
            )
            
            db.session.add(absence)
            db.session.commit()
            flash("Absence enregistrée avec succès", "success")
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'enregistrement: {str(e)}", "danger")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erreur {field}: {error}", "danger")
    
    return redirect(url_for('conges_temps.list_absences'))

@conges_temps_bp.route('/absences/<int:id>/valider', methods=['POST'])
@login_required
def valider_absence(id):
    absence = Absence.query.get_or_404(id)
    absence.statut = "Justifiée"
    db.session.commit()
    flash("Absence justifiée", "success")
    return redirect(url_for('conges_temps.list_absences'))

@conges_temps_bp.route('/absences/<int:id>/refuser', methods=['POST'])
@login_required
def refuser_absence(id):
    absence = Absence.query.get_or_404(id)
    absence.statut = "Non justifiée"
    db.session.commit()
    flash("Absence refusée", "danger")
    return redirect(url_for('conges_temps.list_absences'))

# ============= GESTION DES SOLDES =============

@conges_temps_bp.route('/conges-temps/soldes')
@login_required
@permission_requise('absences_conges')
def list_soldes():
    """Gestion des soldes de congés"""
    annee_courante = date.today().year
    annee = request.args.get('annee', annee_courante, type=int)
    
    # Récupérer tous les employés actifs avec leurs soldes
    employes = Employee.query.filter_by(statut='Actif').all()
    soldes_data = []
    
    for employe in employes:
        solde = SoldeConge.query.filter_by(employe_id=employe.id, annee=annee).first()
        if not solde:
            # Créer un solde par défaut
            solde = SoldeConge(
                employe_id=employe.id,
                annee=annee,
                jours_alloues=25  # Valeur par défaut
            )
            db.session.add(solde)
        
        soldes_data.append({
            'employe': employe,
            'solde': solde
        })
    
    db.session.commit()
    
    form = SoldeCongeForm()
    form.employe_id.choices = [(emp.id, emp.nom_complet) for emp in employes]
    
    return render_template('conges_temps/soldes.html', 
                         soldes_data=soldes_data, 
                         annee=annee,
                         form=form)

# ============= EXPORT ET RAPPORTS =============

@conges_temps_bp.route('/conges-temps/export/conges/excel')
@login_required
@permission_requise('absences_conges')
def export_conges_excel():
    """Export des congés en Excel"""
    conges = Conge.query.join(Employee).all()
    
    data = []
    for conge in conges:
        data.append({
            'Employé': conge.employe.nom_complet,
            'Type': conge.type_conge,
            'Date début': conge.date_debut.strftime('%d/%m/%Y'),
            'Date fin': conge.date_fin.strftime('%d/%m/%Y'),
            'Nb jours': conge.nombre_jours,
            'Statut': conge.statut,
            'Demandé le': conge.date_demande.strftime('%d/%m/%Y'),
            'Motif': conge.motif or ''
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Congés')
        
        # Formatage
        workbook = writer.book
        worksheet = writer.sheets['Congés']
        
        # Format pour les en-têtes
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Appliquer le format aux en-têtes
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    
    output.seek(0)
    return send_file(output, 
                     as_attachment=True, 
                     download_name=f"conges_{datetime.now().strftime('%Y%m%d')}.xlsx",
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ============= API ENDPOINTS =============

@conges_temps_bp.route('/api/solde/<int:employe_id>/<int:annee>')
@login_required
def api_get_solde(employe_id, annee):
    """API pour récupérer le solde d'un employé"""
    solde = SoldeConge.query.filter_by(employe_id=employe_id, annee=annee).first()
    
    if not solde:
        return jsonify({
            'jours_disponibles': 0,
            'jours_alloues': 0,
            'jours_pris': 0,
            'jours_reports': 0
        })
    
    return jsonify({
        'jours_disponibles': solde.jours_disponibles,
        'jours_alloues': solde.jours_alloues,
        'jours_pris': solde.jours_pris,
        'jours_reports': solde.jours_reports
    })

@conges_temps_bp.route('/api/conges/calendrier')
@login_required
def api_conges_calendrier():
    """API pour le calendrier des congés"""
    conges = Conge.query.filter_by(statut='Approuvé').all()
    
    events = []
    for conge in conges:
        events.append({
            'title': f"{conge.employe.nom_complet} - {conge.type_conge}",
            'start': conge.date_debut.isoformat(),
            'end': conge.date_fin.isoformat(),
            'color': '#28a745' if conge.est_en_cours else '#007bff'
        })
    
    return jsonify(events)

# ============= MODULE PRESENCES AVANCE =============

# ============= FONCTIONS UTILITAIRES PRESENCES =============

def calculer_heures_travaillees(heure_arrivee, heure_depart, duree_pause_minutes=60):
    """Calcule les heures travaillées en tenant compte de la pause"""
    if not heure_arrivee or not heure_depart:
        return 0.0
    
    # Convertir en datetime pour calcul
    today = date.today()
    dt_arrivee = datetime.combine(today, heure_arrivee)
    dt_depart = datetime.combine(today, heure_depart)
    
    # Si départ le lendemain
    if dt_depart < dt_arrivee:
        dt_depart = dt_depart + timedelta(days=1)
    
    # Calculer la durée totale
    duree_totale = (dt_depart - dt_arrivee).total_seconds() / 3600
    
    # Soustraire la pause
    duree_pause_heures = duree_pause_minutes / 60
    heures_travaillees = max(0, duree_totale - duree_pause_heures)
    
    return round(heures_travaillees, 2)

def calculer_retard(heure_arrivee, heure_standard, tolerance_minutes=15):
    """Calcule le retard en minutes"""
    if not heure_arrivee or not heure_standard:
        return 0
    
    today = date.today()
    dt_arrivee = datetime.combine(today, heure_arrivee)
    dt_standard = datetime.combine(today, heure_standard)
    
    # Ajouter la tolérance
    dt_standard_avec_tolerance = dt_standard + timedelta(minutes=tolerance_minutes)
    
    if dt_arrivee > dt_standard_avec_tolerance:
        retard_minutes = (dt_arrivee - dt_standard).total_seconds() / 60
        return int(retard_minutes)
    
    return 0

def generer_notifications_presence(employe_id, date_reference, type_notif, donnees):
    """Génère des notifications automatiques de présence"""
    try:
        employe = Employee.query.get(employe_id)
        if not employe:
            return
        
        # Définir les messages selon le type
        messages = {
            'retard': {
                'titre': f'Retard détecté - {employe.nom}',
                'message': f'{employe.nom} est arrivé en retard de {donnees.get("retard_minutes", 0)} minutes le {date_reference.strftime("%d/%m/%Y")}.',
                'priorite': 'normale'
            },
            'absence': {
                'titre': f'Absence détectée - {employe.nom}',
                'message': f'{employe.nom} est absent le {date_reference.strftime("%d/%m/%Y")} sans justification.',
                'priorite': 'haute'
            },
            'depart_anticipe': {
                'titre': f'Départ anticipé - {employe.nom}',
                'message': f'{employe.nom} est parti {donnees.get("depart_anticipe_minutes", 0)} minutes plus tôt le {date_reference.strftime("%d/%m/%Y")}.',
                'priorite': 'normale'
            },
            'heures_sup': {
                'titre': f'Heures supplémentaires - {employe.nom}',
                'message': f'{employe.nom} a effectué {donnees.get("heures_sup", 0)} heures supplémentaires le {date_reference.strftime("%d/%m/%Y")}.',
                'priorite': 'normale'
            }
        }
        
        if type_notif not in messages:
            return
        
        info = messages[type_notif]
        
        notification = NotificationPresence(
            employe_id=employe_id,
            type_notification=type_notif,
            titre=info['titre'],
            message=info['message'],
            priorite=info['priorite'],
            date_reference=date_reference,
            donnees_reference=donnees
        )
        
        db.session.add(notification)
        
    except Exception as e:
        print(f"Erreur génération notification: {e}")

def mettre_a_jour_heures_travail(employe_id, date_travail):
    """Met à jour automatiquement les heures de travail d'un employé pour une date"""
    try:
        # Récupérer les paramètres
        params = ParametrePresence.query.first()
        if not params:
            return
        
        # Récupérer les pointages de la journée
        pointages = Pointage.query.filter(
            Pointage.employe_id == employe_id,
            Pointage.date_pointage == date_travail,
            Pointage.valide == True
        ).order_by(Pointage.heure_pointage).all()
        
        if not pointages:
            return
        
        # Trouver la première entrée et la dernière sortie
        entrees = [p for p in pointages if p.type_pointage == 'entree']
        sorties = [p for p in pointages if p.type_pointage == 'sortie']
        
        if not entrees or not sorties:
            return
        
        heure_arrivee = entrees[0].heure_pointage
        heure_depart = sorties[-1].heure_pointage
        
        # Calculer les pauses
        pauses_debut = [p for p in pointages if p.type_pointage == 'pause_debut']
        pauses_fin = [p for p in pointages if p.type_pointage == 'pause_fin']
        
        duree_pause_minutes = 0
        for i, pause_debut in enumerate(pauses_debut):
            if i < len(pauses_fin):
                pause_fin = pauses_fin[i]
                today = date.today()
                dt_debut = datetime.combine(today, pause_debut.heure_pointage)
                dt_fin = datetime.combine(today, pause_fin.heure_pointage)
                duree_pause_minutes += (dt_fin - dt_debut).total_seconds() / 60
        
        # Si pas de pause explicite, utiliser la pause standard
        if duree_pause_minutes == 0:
            duree_pause_minutes = params.duree_pause_minutes
        
        # Calculer les heures travaillées
        heures_travaillees = calculer_heures_travaillees(heure_arrivee, heure_depart, duree_pause_minutes)
        
        # Calculer le retard
        retard_minutes = calculer_retard(heure_arrivee, params.heure_arrivee_standard, params.tolerance_retard_minutes)
        
        # Calculer les heures supplémentaires
        heures_normales = min(heures_travaillees, params.seuil_hs_quotidien)
        heures_supplementaires = max(0, heures_travaillees - params.seuil_hs_quotidien)
        
        # Déterminer le statut
        statut = 'present'
        if retard_minutes > 0:
            statut = 'retard'
        if heures_travaillees < params.heures_minimum_journee:
            statut = 'absent'
        
        # Créer ou mettre à jour l'enregistrement
        heures_travail = HeuresTravail.query.filter_by(
            employe_id=employe_id,
            date_travail=date_travail
        ).first()
        
        if not heures_travail:
            heures_travail = HeuresTravail(
                employe_id=employe_id,
                date_travail=date_travail
            )
            db.session.add(heures_travail)
        
        # Mettre à jour les données
        heures_travail.heure_arrivee = heure_arrivee
        heures_travail.heure_depart = heure_depart
        heures_travail.duree_pause_minutes = int(duree_pause_minutes)
        heures_travail.heures_travaillees = heures_travaillees
        heures_travail.heures_normales = heures_normales
        heures_travail.heures_supplementaires = heures_supplementaires
        heures_travail.retard_minutes = retard_minutes
        heures_travail.statut = statut
        heures_travail.calcule_automatiquement = True
        
        # Générer notifications si nécessaire
        if params.notifier_retard and retard_minutes > 0:
            generer_notifications_presence(employe_id, date_travail, 'retard', {'retard_minutes': retard_minutes})
            # Envoyer notification email
            try:
                email_service.notify_attendance_issue(employe_id, 'retard', {'retard_minutes': retard_minutes, 'date': date_travail})
            except Exception as e:
                print(f"Erreur envoi email retard: {e}")
        
        if params.notifier_absence and statut == 'absent':
            generer_notifications_presence(employe_id, date_travail, 'absence', {})
            # Envoyer notification email
            try:
                email_service.notify_attendance_issue(employe_id, 'absence', {'date': date_travail})
            except Exception as e:
                print(f"Erreur envoi email absence: {e}")
        
        if params.notifier_heures_supplementaires and heures_supplementaires > 0:
            generer_notifications_presence(employe_id, date_travail, 'heures_sup', {'heures_sup': heures_supplementaires})
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur mise à jour heures travail: {e}")

# ============= ROUTES PRINCIPALES PRESENCES =============

@conges_temps_bp.route('/conges-temps/presences')
@login_required
@permission_requise('presences')
def presences_dashboard():
    """Dashboard principal du module présences"""
    today = date.today()
    
    # Statistiques du jour
    stats_jour = {
        'presents': HeuresTravail.query.filter(
            HeuresTravail.date_travail == today,
            HeuresTravail.statut.in_(['present', 'retard'])
        ).count(),
        'absents': HeuresTravail.query.filter(
            HeuresTravail.date_travail == today,
            HeuresTravail.statut == 'absent'
        ).count(),
        'retards': HeuresTravail.query.filter(
            HeuresTravail.date_travail == today,
            HeuresTravail.statut == 'retard'
        ).count(),
        'total_employes': Employee.query.filter_by(statut='Actif').count()
    }
    
    # Présences récentes
    presences_recentes = HeuresTravail.query.join(Employee).filter(
        HeuresTravail.date_travail >= today - timedelta(days=7)
    ).order_by(HeuresTravail.date_travail.desc()).limit(20).all()
    
    # Notifications non lues
    notifications = NotificationPresence.query.filter(
        NotificationPresence.statut == 'nouvelle',
        NotificationPresence.date_reference >= today - timedelta(days=7)
    ).order_by(NotificationPresence.date_creation.desc()).limit(10).all()
    
    return render_template('conges_temps/presences/dashboard.html',
                         stats_jour=stats_jour,
                         presences_recentes=presences_recentes,
                         notifications=notifications,
                         active_tab='presences')

@conges_temps_bp.route('/conges-temps/presences/pointage', methods=['GET', 'POST'])
@login_required
@permission_requise('presences')
def pointage():
    """Interface de pointage"""
    form = PointageForm()
    form.employe_id.choices = [(0, 'Sélectionner un employé')] + [
        (emp.id, f"{emp.nom} {emp.prenom}") for emp in Employee.query.filter_by(statut='Actif').all()
    ]
    
    if form.validate_on_submit():
        try:
            # Créer le pointage
            pointage = Pointage(
                employe_id=form.employe_id.data,
                date_pointage=form.date_pointage.data,
                heure_pointage=form.heure_pointage.data,
                type_pointage=form.type_pointage.data,
                methode='manuel',
                latitude=form.latitude.data,
                longitude=form.longitude.data,
                adresse=form.adresse.data,
                commentaire=form.commentaire.data,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:200]
            )
            
            db.session.add(pointage)
            db.session.commit()
            
            # Mettre à jour les heures de travail si c'est une sortie
            if form.type_pointage.data == 'sortie':
                mettre_a_jour_heures_travail(form.employe_id.data, form.date_pointage.data)
            
            flash('Pointage enregistré avec succès', 'success')
            return redirect(url_for('conges_temps.pointage'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'enregistrement: {e}', 'error')
    
    # Pointages récents
    pointages_recents = Pointage.query.join(Employee).filter(
        Pointage.date_pointage >= date.today() - timedelta(days=7)
    ).order_by(Pointage.timestamp_creation.desc()).limit(20).all()
    
    return render_template('conges_temps/presences/pointage.html',
                         form=form,
                         pointages_recents=pointages_recents)

@conges_temps_bp.route('/conges-temps/presences/heures')
@login_required
@permission_requise('presences')
def gestion_heures():
    """Gestion des heures de travail"""
    # Filtres
    employe_id = request.args.get('employe_id', type=int)
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    statut = request.args.get('statut')
    
    # Query de base
    query = HeuresTravail.query.join(Employee)
    
    # Appliquer les filtres
    if employe_id:
        query = query.filter(HeuresTravail.employe_id == employe_id)
    
    if date_debut:
        query = query.filter(HeuresTravail.date_travail >= datetime.strptime(date_debut, '%Y-%m-%d').date())
    
    if date_fin:
        query = query.filter(HeuresTravail.date_travail <= datetime.strptime(date_fin, '%Y-%m-%d').date())
    
    if statut:
        query = query.filter(HeuresTravail.statut == statut)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    heures_travail = query.order_by(HeuresTravail.date_travail.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Données pour les filtres
    employes = Employee.query.filter_by(statut='Actif').all()
    
    # Statistiques
    stats = {
        'total_heures': query.with_entities(func.sum(HeuresTravail.heures_travaillees)).scalar() or 0,
        'total_heures_sup': query.with_entities(func.sum(HeuresTravail.heures_supplementaires)).scalar() or 0,
        'moyenne_retard': query.with_entities(func.avg(HeuresTravail.retard_minutes)).scalar() or 0,
        'taux_presence': query.filter(HeuresTravail.statut.in_(['present', 'retard'])).count() / max(query.count(), 1) * 100
    }
    
    return render_template('conges_temps/presences/heures.html',
                         heures_travail=heures_travail,
                         employes=employes,
                         stats=stats,
                         filters={
                             'employe_id': employe_id,
                             'date_debut': date_debut,
                             'date_fin': date_fin,
                             'statut': statut
                         })

@conges_temps_bp.route('/conges-temps/presences/heures/modifier/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_requise('presences')
def modifier_heures(id):
    """Modifier les heures de travail d'un employé"""
    heures_travail = HeuresTravail.query.get_or_404(id)
    form = HeuresTravailForm(obj=heures_travail)
    
    form.employe_id.choices = [(emp.id, f"{emp.nom} {emp.prenom}") for emp in Employee.query.filter_by(statut='Actif').all()]
    form.employe_id.data = heures_travail.employe_id
    
    if form.validate_on_submit():
        try:
            # Mettre à jour les données
            heures_travail.heure_arrivee = form.heure_arrivee.data
            heures_travail.heure_depart = form.heure_depart.data
            heures_travail.duree_pause_minutes = form.duree_pause_minutes.data
            heures_travail.statut = form.statut.data
            heures_travail.commentaire_validation = form.commentaire_validation.data
            heures_travail.valide_par = current_user.id
            heures_travail.date_validation = datetime.utcnow()
            heures_travail.calcule_automatiquement = False
            
            # Recalculer les heures si nécessaire
            if form.heure_arrivee.data and form.heure_depart.data:
                heures_travail.heures_travaillees = calculer_heures_travaillees(
                    form.heure_arrivee.data, 
                    form.heure_depart.data, 
                    form.duree_pause_minutes.data or 60
                )
                
                # Recalculer le retard
                params = ParametrePresence.query.first()
                if params:
                    heures_travail.retard_minutes = calculer_retard(
                        form.heure_arrivee.data,
                        params.heure_arrivee_standard,
                        params.tolerance_retard_minutes
                    )
            
            # Si saisie directe des heures
            if form.heures_travaillees.data is not None:
                heures_travail.heures_travaillees = form.heures_travaillees.data
            
            if form.heures_supplementaires.data is not None:
                heures_travail.heures_supplementaires = form.heures_supplementaires.data
            
            db.session.commit()
            flash('Heures de travail mises à jour avec succès', 'success')
            return redirect(url_for('conges_temps.gestion_heures'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour: {e}', 'error')
    
    return render_template('conges_temps/presences/modifier_heures.html',
                         form=form,
                         heures_travail=heures_travail)

# ============= ROUTES API PRESENCES =============

@conges_temps_bp.route('/api/presences/pointage-rapide', methods=['POST'])
@login_required
@permission_requise('presences')
def api_pointage_rapide():
    """API pour pointage rapide (QR code, badge, etc.)"""
    try:
        data = request.get_json()
        employe_id = data.get('employe_id')
        type_pointage = data.get('type_pointage', 'entree')
        methode = data.get('methode', 'qr_code')
        
        if not employe_id:
            return jsonify({'error': 'ID employé manquant'}), 400
        
        # Vérifier que l'employé existe
        employe = Employee.query.get(employe_id)
        if not employe:
            return jsonify({'error': 'Employé non trouvé'}), 404
        
        # Créer le pointage
        pointage = Pointage(
            employe_id=employe_id,
            date_pointage=date.today(),
            heure_pointage=datetime.now().time(),
            type_pointage=type_pointage,
            methode=methode,
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:200]
        )
        
        db.session.add(pointage)
        db.session.commit()
        
        # Mettre à jour les heures si c'est une sortie
        if type_pointage == 'sortie':
            mettre_a_jour_heures_travail(employe_id, date.today())
        
        return jsonify({
            'success': True,
            'message': f'Pointage {type_pointage} enregistré pour {employe.nom}',
            'pointage_id': pointage.id,
            'heure': pointage.heure_pointage.strftime('%H:%M')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@conges_temps_bp.route('/api/presences/statistiques')
@login_required
@permission_requise('presences')
def api_stats_presences():
    """API pour récupérer les statistiques de présence"""
    try:
        periode = request.args.get('periode', 'semaine')  # jour, semaine, mois
        employe_id = request.args.get('employe_id', type=int)
        
        # Statistiques globales
        stats = {
            'total_employes': Employee.query.filter_by(statut='Actif').count(),
            'total_present': HeuresTravail.query.filter(HeuresTravail.statut.in_(['present', 'retard'])).count(),
            'total_absent': HeuresTravail.query.filter(HeuresTravail.statut == 'absent').count(),
            'taux_presence': 0,
            'moyenne_retard': 0,
            'total_heures_travaillees': 0,
            'total_heures_supplementaires': 0
        }
        
        if stats['total_present'] > 0:
            stats['taux_presence'] = (stats['total_present'] / stats['total_employes']) * 100
            
            # Moyenne de retard
            stats['moyenne_retard'] = HeuresTravail.query.filter(HeuresTravail.statut == 'retard').with_entities(func.avg(HeuresTravail.retard_minutes)).scalar() or 0
            
            # Total des heures travaillées et supplémentaires
            stats['total_heures_travaillees'] = HeuresTravail.query.with_entities(func.sum(HeuresTravail.heures_travaillees)).scalar() or 0
            stats['total_heures_supplementaires'] = HeuresTravail.query.with_entities(func.sum(HeuresTravail.heures_supplementaires)).scalar() or 0
        
        # Statistiques par période
        if periode == 'jour':
            date_debut = datetime.combine(date.today(), time.min)
            date_fin = datetime.combine(date.today(), time.max)
        elif periode == 'semaine':
            date_debut = datetime.combine(date.today() - timedelta(days=date.today().weekday()), time.min)
            date_fin = datetime.combine(date.today() + timedelta(days=6 - date.today().weekday()), time.max)
        else:  # mois
            date_debut = datetime.combine(date.today().replace(day=1), time.min)
            next_month = date.today().replace(day=1) + timedelta(days=31)
            date_fin = datetime.combine(next_month.replace(day=1) - timedelta(days=1), time.max)
        
        stats_periode = HeuresTravail.query.filter(
            HeuresTravail.date_travail >= date_debut,
            HeuresTravail.date_travail <= date_fin
        ).with_entities(
            func.count(HeuresTravail.id),
            func.sum(HeuresTravail.heures_travaillees),
            func.sum(HeuresTravail.heures_supplementaires),
            func.avg(HeuresTravail.retard_minutes)
        ).first()
        
        if stats_periode:
            stats['total_jours_ouvres'] = stats_periode[0]
            stats['total_heures_travaillees_periode'] = stats_periode[1] or 0
            stats['total_heures_supplementaires_periode'] = stats_periode[2] or 0
            stats['moyenne_retard_periode'] = stats_periode[3] or 0
        
        # Filtrer par employé si demandé
        if employe_id:
            stats['employe'] = Employee.query.get(employe_id)
            
            # Statistiques spécifiques à l'employé
            stats_employe = HeuresTravail.query.filter_by(employe_id=employe_id).with_entities(
                func.count(HeuresTravail.id),
                func.sum(HeuresTravail.heures_travaillees),
                func.sum(HeuresTravail.heures_supplementaires),
                func.avg(HeuresTravail.retard_minutes)
            ).first()
            
            if stats_employe:
                stats['total_jours_ouvres_employe'] = stats_employe[0]
                stats['total_heures_travaillees_employe'] = stats_employe[1] or 0
                stats['total_heures_supplementaires_employe'] = stats_employe[2] or 0
                stats['moyenne_retard_employe'] = stats_employe[3] or 0
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============= ROUTES RAPPORTS PRESENCES =============

@conges_temps_bp.route('/conges-temps/presences/rapports', methods=['GET', 'POST'])
@login_required
@permission_requise('presences')
def rapports_presences():
    """Génération de rapports de présence"""
    form = RapportPresenceForm()
    
    # Charger les choix
    form.employes.choices = [(emp.id, f"{emp.nom} {emp.prenom}") for emp in Employee.query.filter_by(statut='Actif').all()]
    form.departements.choices = [(dept, dept) for dept in db.session.query(Employee.departement).distinct() if dept[0]]
    
    if form.validate_on_submit():
        try:
            # Générer le rapport selon le type demandé
            return generer_rapport_presence(form)
            
        except Exception as e:
            flash(f'Erreur lors de la génération du rapport: {e}', 'error')
    
    return render_template('conges_temps/presences/rapports.html', form=form)

def generer_rapport_presence(form):
    """Génère un rapport de présence selon les paramètres"""
    date_debut = form.date_debut.data
    date_fin = form.date_fin.data
    type_rapport = form.type_rapport.data
    format_export = form.format_export.data
    
    # Query de base
    query = HeuresTravail.query.join(Employee).filter(
        HeuresTravail.date_travail >= date_debut,
        HeuresTravail.date_travail <= date_fin
    )
    
    # Appliquer les filtres
    if form.employes.data:
        query = query.filter(HeuresTravail.employe_id.in_(form.employes.data))
    
    if form.statuts.data:
        query = query.filter(HeuresTravail.statut.in_(form.statuts.data))
    
    heures_travail = query.order_by(HeuresTravail.date_travail.desc(), Employee.nom).all()
    
    if format_export == 'excel':
        return exporter_presences_excel(heures_travail, type_rapport, date_debut, date_fin)
    elif format_export == 'pdf':
        return exporter_presences_pdf(heures_travail, type_rapport, date_debut, date_fin)
    else:  # CSV
        return exporter_presences_csv(heures_travail, type_rapport, date_debut, date_fin)

def exporter_presences_excel(heures_travail, type_rapport, date_debut, date_fin):
    """Export Excel des données de présence"""
    output = BytesIO()
    
    data = []
    for h in heures_travail:
        data.append({
            'Employé': f"{h.employe.nom} {h.employe.prenom}",
            'Date': h.date_travail.strftime('%d/%m/%Y'),
            'Arrivée': h.heure_arrivee.strftime('%H:%M') if h.heure_arrivee else '-',
            'Départ': h.heure_depart.strftime('%H:%M') if h.heure_depart else '-',
            'Heures travaillées': h.heures_travaillees or 0,
            'Heures supplémentaires': h.heures_supplementaires or 0,
            'Retard (min)': h.retard_minutes or 0,
            'Statut': h.statut
        })
    
    df = pd.DataFrame(data)
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    
    filename = f'rapport_presences_{date_debut.strftime("%Y%m%d")}_{date_fin.strftime("%Y%m%d")}.xlsx'
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def exporter_presences_csv(heures_travail, type_rapport, date_debut, date_fin):
    """Export CSV des données de présence"""
    output = BytesIO()
    
    data = []
    for h in heures_travail:
        data.append({
            'Employé': f"{h.employe.nom} {h.employe.prenom}",
            'Date': h.date_travail.strftime('%d/%m/%Y'),
            'Arrivée': h.heure_arrivee.strftime('%H:%M') if h.heure_arrivee else '',
            'Départ': h.heure_depart.strftime('%H:%M') if h.heure_depart else '',
            'Heures travaillées': h.heures_travaillees or 0,
            'Heures supplémentaires': h.heures_supplementaires or 0,
            'Retard (min)': h.retard_minutes or 0,
            'Statut': h.statut
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    filename = f'presences_{date_debut.strftime("%Y%m%d")}_{date_fin.strftime("%Y%m%d")}.csv'
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )

def exporter_presences_pdf(heures_travail, type_rapport, date_debut, date_fin):
    """Export PDF des données de présence"""
    template_name = 'conges_temps/presences/rapport_pdf.html'
    
    # Calculer les statistiques globales
    stats = {
        'periode': f"Du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}",
        'total_heures': sum([h.heures_travaillees or 0 for h in heures_travail]),
        'total_heures_sup': sum([h.heures_supplementaires or 0 for h in heures_travail]),
        'total_retards': len([h for h in heures_travail if h.retard_minutes > 0]),
        'total_absences': len([h for h in heures_travail if h.statut == 'absent'])
    }
    
    html_content = render_template(template_name, 
                                  heures_travail=heures_travail,
                                  stats=stats,
                                  date_generation=datetime.now())
    
    # Générer le PDF
    pdf_file = HTML(string=html_content).write_pdf()
    
    filename = f'rapport_presences_{date_debut.strftime("%Y%m%d")}.pdf'
    
    return send_file(
        BytesIO(pdf_file),
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )