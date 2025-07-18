from flask import Blueprint, make_response, render_template, redirect, url_for, flash, send_file, request, current_app
from app import db
import pandas as pd
from io import BytesIO
from weasyprint import HTML
from app.models import Employee, Absence, EmployeeHistory, EmployeeDocument, Utilisateur
from app.forms import EmployeeForm, AbsenceForm, EmployeeDocumentForm, EmployeeSearchForm
from flask_login import login_required, current_user
from app.utils.permissions import permission_requise
from werkzeug.utils import secure_filename
import os
from datetime import datetime

rh_bp = Blueprint('rh', __name__)

def save_employee_file(file, folder):
    """Sauvegarde un fichier d'employé et retourne le nom du fichier"""
    if file and file.filename:
        filename = secure_filename(file.filename)
        # Ajouter timestamp pour éviter les conflits
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        # Créer le dossier s'il n'existe pas
        upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'employees', folder)
        os.makedirs(upload_path, exist_ok=True)
        
        # Sauvegarder le fichier
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        return filename
    return None

def log_employee_change(employee_id, action, champ_modifie=None, ancienne_valeur=None, nouvelle_valeur=None, commentaire=None):
    """Enregistre une modification dans l'historique des employés"""
    try:
        history = EmployeeHistory(
            employee_id=employee_id,
            user_id=current_user.id,
            action=action,
            champ_modifie=champ_modifie,
            ancienne_valeur=str(ancienne_valeur) if ancienne_valeur else None,
            nouvelle_valeur=str(nouvelle_valeur) if nouvelle_valeur else None,
            commentaire=commentaire
        )
        db.session.add(history)
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de l'historique: {e}")

#***************************************************************ADD ON DATA BASE****************************************************************

# ---- Employés ----
@rh_bp.route('/employes')
@login_required
@permission_requise('employes')
def list_employes():
    search_form = EmployeeSearchForm()
    query = Employee.query
    
    # Filtres de recherche
    if request.args.get('nom'):
        nom_recherche = f"%{request.args.get('nom')}%"
        query = query.filter(
            (Employee.nom.ilike(nom_recherche)) | 
            (Employee.prenom.ilike(nom_recherche)) |
            (Employee.nom_complet.ilike(nom_recherche))
        )
    
    if request.args.get('departement'):
        query = query.filter(Employee.departement == request.args.get('departement'))
    
    if request.args.get('poste'):
        poste_recherche = f"%{request.args.get('poste')}%"
        query = query.filter(Employee.poste.ilike(poste_recherche))
    
    if request.args.get('statut'):
        query = query.filter(Employee.statut == request.args.get('statut'))
    
    employes = query.order_by(Employee.nom).all()
    form = EmployeeForm()
    
    return render_template('employes/list.html', employes=employes, form=form, search_form=search_form)

@rh_bp.route('/employes/add', methods=['POST'])
@login_required
@permission_requise('employes')
def add_employe():
    form = EmployeeForm()
    if form.validate_on_submit():
        try:
            # Créer le nom complet
            nom_complet = f"{form.nom.data} {form.prenom.data or ''}".strip()
            
            # Traiter les fichiers uploadés
            photo_filename = None
            cv_filename = None
            contrat_filename = None
            
            if form.photo_profil.data:
                photo_filename = save_employee_file(form.photo_profil.data, 'photos')
            if form.cv_file.data:
                cv_filename = save_employee_file(form.cv_file.data, 'cv')
            if form.contrat_file.data:
                contrat_filename = save_employee_file(form.contrat_file.data, 'contrats')
            
            employe = Employee(
                nom=form.nom.data,
                prenom=form.prenom.data,
                nom_complet=nom_complet,
                date_naissance=form.date_naissance.data,
                lieu_naissance=form.lieu_naissance.data,
                sexe=form.sexe.data,
                nationalite=form.nationalite.data or 'Camerounaise',
                situation_matrimoniale=form.situation_matrimoniale.data,
                nombre_enfants=form.nombre_enfants.data or 0,
                email=form.email.data,
                telephone=form.telephone.data,
                telephone_urgence=form.telephone_urgence.data,
                adresse=form.adresse.data,
                ville=form.ville.data,
                poste=form.poste.data,
                departement=form.departement.data,
                manager_id=form.manager_id.data if form.manager_id.data != 0 else None,
                type_contrat=form.type_contrat.data,
                date_embauche=form.date_embauche.data,
                date_fin_contrat=form.date_fin_contrat.data,
                salaire_base=form.salaire_base.data,
                statut=form.statut.data or 'Actif',
                numero_cni=form.numero_cni.data,
                numero_cnps=form.numero_cnps.data,
                numero_crtv=form.numero_crtv.data,
                numero_compte_bancaire=form.numero_compte_bancaire.data,
                banque=form.banque.data,
                photo_profil=photo_filename,
                cv_file=cv_filename,
                contrat_file=contrat_filename,
                cree_par=current_user.id
            )
            
            db.session.add(employe)
            db.session.flush()  # Pour obtenir l'ID
            
            # Enregistrer dans l'historique
            log_employee_change(employe.id, 'CREATE', 'Création de l\'employé', None, nom_complet)
            
            db.session.commit()
            flash("L'employé a été ajouté avec succès.", "success")
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout : {str(e)}", "danger")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erreur {field}: {error}", "danger")

    return redirect(url_for('rh.list_employes'))

# ---- Absences ----
@rh_bp.route('/absences')
@login_required
@permission_requise('absences_conges')
def list_absences():
    absences = Absence.query.all()
    form = AbsenceForm()
    return render_template('absences/list.html', absences=absences, form=form)

@rh_bp.route('/absences/add', methods=['POST'])
def add_absence():
    form = AbsenceForm()
    if form.validate_on_submit():
        absence = Absence(
            employee_id=form.employee_id.data,
            type_absence=form.type_absence.data,
            date_debut=form.date_debut.data,
            date_fin=form.date_fin.data,
            motif=form.motif.data,
            justificatif=form.justificatif.data,
            statut=form.statut.data
        )
        db.session.add(absence)
        db.session.commit()
        flash("L'absence a été ajouté avec succès.", "success")
    else:
        flash("Erreur lors de l'ajout de l'absence. Vérifiez le formulaire.", "danger")

    return redirect(url_for('rh.list_absences'))

    
#***************************************************************UPDATE ON DATA BASE***********************************************************

# Modifier un employé
@rh_bp.route('/employes/edit/<int:id>', methods=['POST'])
@login_required
@permission_requise('employes')
def edit_employe(id):
    employe = Employee.query.get_or_404(id)
    form = EmployeeForm()

    if form.validate_on_submit():
        try:
            # Stocker les anciennes valeurs pour l'historique
            changes = []
            
            # Vérifier les changements et enregistrer l'historique
            if employe.nom != form.nom.data:
                changes.append(('nom', employe.nom, form.nom.data))
                employe.nom = form.nom.data
            
            if employe.prenom != form.prenom.data:
                changes.append(('prenom', employe.prenom, form.prenom.data))
                employe.prenom = form.prenom.data
            
            if employe.email != form.email.data:
                changes.append(('email', employe.email, form.email.data))
                employe.email = form.email.data
            
            if employe.telephone != form.telephone.data:
                changes.append(('telephone', employe.telephone, form.telephone.data))
                employe.telephone = form.telephone.data
            
            if employe.telephone_urgence != form.telephone_urgence.data:
                changes.append(('telephone_urgence', employe.telephone_urgence, form.telephone_urgence.data))
                employe.telephone_urgence = form.telephone_urgence.data
            
            if employe.adresse != form.adresse.data:
                changes.append(('adresse', employe.adresse, form.adresse.data))
                employe.adresse = form.adresse.data
            
            if employe.ville != form.ville.data:
                changes.append(('ville', employe.ville, form.ville.data))
                employe.ville = form.ville.data
            
            if employe.poste != form.poste.data:
                changes.append(('poste', employe.poste, form.poste.data))
                employe.poste = form.poste.data
            
            if employe.departement != form.departement.data:
                changes.append(('departement', employe.departement, form.departement.data))
                employe.departement = form.departement.data
            
            if employe.manager_id != (form.manager_id.data if form.manager_id.data != 0 else None):
                old_manager = employe.manager.nom_complet if employe.manager else None
                new_manager = Employee.query.get(form.manager_id.data).nom_complet if form.manager_id.data and form.manager_id.data != 0 else None
                changes.append(('manager', old_manager, new_manager))
                employe.manager_id = form.manager_id.data if form.manager_id.data != 0 else None
            
            if employe.type_contrat != form.type_contrat.data:
                changes.append(('type_contrat', employe.type_contrat, form.type_contrat.data))
                employe.type_contrat = form.type_contrat.data
            
            if employe.date_embauche != form.date_embauche.data:
                changes.append(('date_embauche', employe.date_embauche, form.date_embauche.data))
                employe.date_embauche = form.date_embauche.data
            
            if employe.date_fin_contrat != form.date_fin_contrat.data:
                changes.append(('date_fin_contrat', employe.date_fin_contrat, form.date_fin_contrat.data))
                employe.date_fin_contrat = form.date_fin_contrat.data
            
            if employe.salaire_base != form.salaire_base.data:
                changes.append(('salaire_base', employe.salaire_base, form.salaire_base.data))
                employe.salaire_base = form.salaire_base.data
            
            if employe.statut != form.statut.data:
                changes.append(('statut', employe.statut, form.statut.data))
                employe.statut = form.statut.data
            
            if employe.numero_cni != form.numero_cni.data:
                changes.append(('numero_cni', employe.numero_cni, form.numero_cni.data))
                employe.numero_cni = form.numero_cni.data
            
            if employe.numero_cnps != form.numero_cnps.data:
                changes.append(('numero_cnps', employe.numero_cnps, form.numero_cnps.data))
                employe.numero_cnps = form.numero_cnps.data
            
            if employe.numero_crtv != form.numero_crtv.data:
                changes.append(('numero_crtv', employe.numero_crtv, form.numero_crtv.data))
                employe.numero_crtv = form.numero_crtv.data
            
            if employe.numero_compte_bancaire != form.numero_compte_bancaire.data:
                changes.append(('numero_compte_bancaire', employe.numero_compte_bancaire, form.numero_compte_bancaire.data))
                employe.numero_compte_bancaire = form.numero_compte_bancaire.data
            
            if employe.banque != form.banque.data:
                changes.append(('banque', employe.banque, form.banque.data))
                employe.banque = form.banque.data
            
            if employe.date_naissance != form.date_naissance.data:
                changes.append(('date_naissance', employe.date_naissance, form.date_naissance.data))
                employe.date_naissance = form.date_naissance.data
            
            if employe.lieu_naissance != form.lieu_naissance.data:
                changes.append(('lieu_naissance', employe.lieu_naissance, form.lieu_naissance.data))
                employe.lieu_naissance = form.lieu_naissance.data
            
            if employe.sexe != form.sexe.data:
                changes.append(('sexe', employe.sexe, form.sexe.data))
                employe.sexe = form.sexe.data
            
            if employe.nationalite != form.nationalite.data:
                changes.append(('nationalite', employe.nationalite, form.nationalite.data))
                employe.nationalite = form.nationalite.data
            
            if employe.situation_matrimoniale != form.situation_matrimoniale.data:
                changes.append(('situation_matrimoniale', employe.situation_matrimoniale, form.situation_matrimoniale.data))
                employe.situation_matrimoniale = form.situation_matrimoniale.data
            
            if employe.nombre_enfants != form.nombre_enfants.data:
                changes.append(('nombre_enfants', employe.nombre_enfants, form.nombre_enfants.data))
                employe.nombre_enfants = form.nombre_enfants.data or 0

            # Traiter les nouveaux fichiers uploadés
            if form.photo_profil.data:
                old_photo = employe.photo_profil
                new_photo = save_employee_file(form.photo_profil.data, 'photos')
                if new_photo:
                    employe.photo_profil = new_photo
                    changes.append(('photo_profil', 'Ancienne photo', 'Nouvelle photo'))
                    # Supprimer l'ancienne photo si elle existe
                    if old_photo:
                        old_photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'employees', 'photos', old_photo)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
            
            if form.cv_file.data:
                old_cv = employe.cv_file
                new_cv = save_employee_file(form.cv_file.data, 'cv')
                if new_cv:
                    employe.cv_file = new_cv
                    changes.append(('cv_file', 'Ancien CV', 'Nouveau CV'))
                    # Supprimer l'ancien CV si il existe
                    if old_cv:
                        old_cv_path = os.path.join(current_app.root_path, 'static', 'uploads', 'employees', 'cv', old_cv)
                        if os.path.exists(old_cv_path):
                            os.remove(old_cv_path)
            
            if form.contrat_file.data:
                old_contrat = employe.contrat_file
                new_contrat = save_employee_file(form.contrat_file.data, 'contrats')
                if new_contrat:
                    employe.contrat_file = new_contrat
                    changes.append(('contrat_file', 'Ancien contrat', 'Nouveau contrat'))
                    # Supprimer l'ancien contrat si il existe
                    if old_contrat:
                        old_contrat_path = os.path.join(current_app.root_path, 'static', 'uploads', 'employees', 'contrats', old_contrat)
                        if os.path.exists(old_contrat_path):
                            os.remove(old_contrat_path)

            # Mettre à jour le nom complet
            employe.nom_complet = f"{employe.nom} {employe.prenom or ''}".strip()
            employe.modifie_par = current_user.id
            employe.date_modification = datetime.now()

            # Enregistrer les changements dans l'historique
            for champ, ancienne_valeur, nouvelle_valeur in changes:
                log_employee_change(employe.id, 'UPDATE', champ, ancienne_valeur, nouvelle_valeur)

            if changes:
                log_employee_change(employe.id, 'UPDATE', 'Modification générale', None, f"{len(changes)} champs modifiés")
                db.session.commit()
                flash(f"L'employé {employe.nom_complet} a été modifié avec succès ({len(changes)} modifications).", "success")
            else:
                flash("Aucune modification détectée.", "info")

        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification : {str(e)}", "danger")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erreur {field}: {error}", "danger")
    
    return redirect(url_for('rh.detail_employe', id=id))

# Modifier une absence
@rh_bp.route('/absences/edit/<int:id>', methods=['POST'])
def edit_absence(id):
    absence = Absence.query.get_or_404(id)
    form = AbsenceForm()

    if form.validate_on_submit():
        absence.employee_id = form.employee_id.data
        absence.type_absence = form.type_absence.data
        absence.date_debut = form.date_debut.data
        absence.date_fin = form.date_fin.data
        absence.motif = form.motif.data
        absence.justificatif = form.justificatif.data
        absence.statut = form.statut.data

        db.session.commit()
        flash("L'absence a été modifiée avec succès.", "success")
        return redirect(url_for('rh.list_absences'))

    return redirect(url_for('rh.list_absences'))




#****************************************************************DELETE ON DATA BASE**********************************************************

# Supprimer un employé
@rh_bp.route('/employes/delete/<int:id>', methods=['POST'])
@login_required
@permission_requise('employes')
def delete_employe(id):
    employe = Employee.query.get_or_404(id)
    
    try:
        # Log de la suppression avant de supprimer
        log_employee_change(id, 'DELETE', 'Suppression de l\'employé', employe.nom_complet, None, 'Employé supprimé du système')
        
        # Supprimer les fichiers associés
        if employe.photo_profil:
            photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'employees', 'photos', employe.photo_profil)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        if employe.cv_file:
            cv_path = os.path.join(current_app.root_path, 'static', 'uploads', 'employees', 'cv', employe.cv_file)
            if os.path.exists(cv_path):
                os.remove(cv_path)
        
        if employe.contrat_file:
            contrat_path = os.path.join(current_app.root_path, 'static', 'uploads', 'employees', 'contrats', employe.contrat_file)
            if os.path.exists(contrat_path):
                os.remove(contrat_path)
        
        # Supprimer les documents associés
        for document in employe.documents:
            doc_path = os.path.join(current_app.root_path, 'static', 'uploads', 'employees', 'documents', document.chemin_fichier)
            if os.path.exists(doc_path):
                os.remove(doc_path)
        
        employe_nom = employe.nom_complet
        db.session.delete(employe)
        db.session.commit()
        
        flash(f"L'employé {employe_nom} a été supprimé avec succès.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "danger")
    
    return redirect(url_for('rh.list_employes'))

# Supprimer une absence
@rh_bp.route('/absences/delete/<int:id>', methods=['POST'])
def delete_absence(id):
    absence = Absence.query.get_or_404(id)
    db.session.delete(absence)
    db.session.commit()
    flash("L'absence a été supprimée avec succès.", "success")
    return redirect(url_for('rh.list_absences'))




#*************************************************************************VIEW****************************************************************

# Detail employé
@rh_bp.route("/employes/<int:id>")
@login_required
@permission_requise('employes')
def detail_employe(id):
    employe = Employee.query.get_or_404(id)
    document_form = EmployeeDocumentForm()
    
    # Récupérer l'historique des modifications
    historique = EmployeeHistory.query.filter_by(employee_id=id).order_by(EmployeeHistory.date_modification.desc()).limit(20).all()
    
    # Récupérer la liste des employés pour le champ manager (sauf l'employé actuel)
    employes_managers = Employee.query.filter(Employee.id != id).all()
    
    return render_template("employes/detail.html", employe=employe, document_form=document_form, historique=historique, employes_managers=employes_managers)

#***************************************************************EXPORT***********************************************************************

# Exportation employés Excel et PDF
@rh_bp.route('/employes/export/excel')
def export_employes_excel():
    employes = Employee.query.all()
    data = [{
        "Nom": emp.nom,
        "Poste": emp.poste,
        "Département": emp.departement,
        "Email": emp.email,
        "Téléphone": emp.telephone,
        "Contrat": emp.type_contrat,
        "Date embauche": emp.date_embauche
    } for emp in employes]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Employés')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="employes.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@rh_bp.route('/employes/export/pdf')
def export_employes_pdf():
    employes = Employee.query.all()
    rendered = render_template('employes/employes_pdf.html', employes=employes)
    pdf = HTML(string=rendered).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=employes.pdf'
    return response

# Exportation Absences Excel et PDF 
@rh_bp.route('/absences/export/excel')
def export_absences_excel():
    absences = Absence.query.all()
    data = [{
        #'Employé': absence.employe.nom,
        'Type': absence.type_absence,
        'Période': f"{absence.date_debut.strftime('%d/%m/%Y')} - {absence.date_fin.strftime('%d/%m/%Y')}",
        'Durée': f"{absence.duree} jours",
        'Justificatif': absence.justificatif,
        'Statut': absence.statut
    } for absence in absences]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Absences')

    output.seek(0)
    return send_file(output, download_name="absences.xlsx", as_attachment=True)

@rh_bp.route('/absences/export/pdf')
def export_absences_pdf():
    absences = Absence.query.all()
    rendered = render_template('absences/absences_pdf.html', absences=absences)
    pdf = HTML(string=rendered).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=absences.pdf'
    return response

# Ajouter un document à un employé
@rh_bp.route('/employes/<int:employee_id>/documents/add', methods=['POST'])
@login_required
@permission_requise('employes')
def add_employee_document(employee_id):
    employe = Employee.query.get_or_404(employee_id)
    form = EmployeeDocumentForm()
    
    if form.validate_on_submit():
        try:
            # Sauvegarder le fichier
            filename = save_employee_file(form.fichier.data, 'documents')
            
            if filename:
                # Obtenir la taille du fichier
                file_path = os.path.join(current_app.root_path, 'static', 'uploads', 'employees', 'documents', filename)
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                
                document = EmployeeDocument(
                    employee_id=employee_id,
                    nom_document=form.nom_document.data,
                    type_document=form.type_document.data,
                    nom_fichier=form.fichier.data.filename,
                    chemin_fichier=filename,
                    taille_fichier=file_size,
                    uploade_par=current_user.id
                )
                
                db.session.add(document)
                
                # Log dans l'historique
                log_employee_change(employee_id, 'UPDATE', 'Ajout de document', None, form.nom_document.data)
                
                db.session.commit()
                flash(f"Document '{form.nom_document.data}' ajouté avec succès.", "success")
            else:
                flash("Erreur lors de l'upload du fichier.", "danger")
                
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout du document: {str(e)}", "danger")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erreur {field}: {error}", "danger")
    
    return redirect(url_for('rh.detail_employe', id=employee_id))

# Télécharger un document d'employé
@rh_bp.route('/employes/documents/<int:document_id>/download')
@login_required
@permission_requise('employes')
def download_employee_document(document_id):
    document = EmployeeDocument.query.get_or_404(document_id)
    
    file_path = os.path.join(current_app.root_path, 'static', 'uploads', 'employees', 'documents', document.chemin_fichier)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=document.nom_fichier)
    else:
        flash("Fichier non trouvé.", "danger")
        return redirect(url_for('rh.detail_employe', id=document.employee_id))

# Supprimer un document d'employé
@rh_bp.route('/employes/documents/<int:document_id>/delete', methods=['POST'])
@login_required
@permission_requise('employes')
def delete_employee_document(document_id):
    document = EmployeeDocument.query.get_or_404(document_id)
    employee_id = document.employee_id
    
    try:
        # Supprimer le fichier physique
        file_path = os.path.join(current_app.root_path, 'static', 'uploads', 'employees', 'documents', document.chemin_fichier)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Log dans l'historique
        log_employee_change(employee_id, 'UPDATE', 'Suppression de document', document.nom_document, None)
        
        # Supprimer l'enregistrement de la base de données
        db.session.delete(document)
        db.session.commit()
        
        flash(f"Document '{document.nom_document}' supprimé avec succès.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression du document: {str(e)}", "danger")
    
    return redirect(url_for('rh.detail_employe', id=employee_id))

# Modifier un document d'employé
@rh_bp.route('/employes/documents/<int:document_id>/edit', methods=['POST'])
@login_required
@permission_requise('employes')
def edit_employee_document(document_id):
    document = EmployeeDocument.query.get_or_404(document_id)
    employee_id = document.employee_id
    
    try:
        new_name = request.form.get('nom_document')
        new_type = request.form.get('type_document')
        
        if new_name and new_name != document.nom_document:
            log_employee_change(employee_id, 'UPDATE', 'Modification nom document', document.nom_document, new_name)
            document.nom_document = new_name
        
        if new_type and new_type != document.type_document:
            log_employee_change(employee_id, 'UPDATE', 'Modification type document', document.type_document, new_type)
            document.type_document = new_type
        
        db.session.commit()
        flash("Document modifié avec succès.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la modification du document: {str(e)}", "danger")
    
    return redirect(url_for('rh.detail_employe', id=employee_id))

# Route pour obtenir les détails d'un employé en format JSON (pour les modals d'édition)
@rh_bp.route('/employes/<int:id>/json')
@login_required
@permission_requise('employes')
def get_employe_json(id):
    employe = Employee.query.get_or_404(id)
    
    # Obtenir la liste des managers possibles (tous les employés sauf celui-ci)
    managers = Employee.query.filter(Employee.id != id).all()
    
    data = {
        'id': employe.id,
        'nom': employe.nom,
        'prenom': employe.prenom,
        'email': employe.email,
        'telephone': employe.telephone,
        'telephone_urgence': employe.telephone_urgence,
        'adresse': employe.adresse,
        'ville': employe.ville,
        'poste': employe.poste,
        'departement': employe.departement,
        'manager_id': employe.manager_id,
        'type_contrat': employe.type_contrat,
        'date_embauche': employe.date_embauche.strftime('%Y-%m-%d') if employe.date_embauche else '',
        'date_fin_contrat': employe.date_fin_contrat.strftime('%Y-%m-%d') if employe.date_fin_contrat else '',
        'salaire_base': float(employe.salaire_base) if employe.salaire_base else 0,
        'statut': employe.statut,
        'numero_cni': employe.numero_cni,
        'numero_cnps': employe.numero_cnps,
        'numero_crtv': employe.numero_crtv,
        'numero_compte_bancaire': employe.numero_compte_bancaire,
        'banque': employe.banque,
        'date_naissance': employe.date_naissance.strftime('%Y-%m-%d') if employe.date_naissance else '',
        'lieu_naissance': employe.lieu_naissance,
        'sexe': employe.sexe,
        'nationalite': employe.nationalite,
        'situation_matrimoniale': employe.situation_matrimoniale,
        'nombre_enfants': employe.nombre_enfants,
        'managers': [{'id': m.id, 'nom_complet': m.nom_complet} for m in managers]
    }
    
    return data

# Route pour la recherche d'employés (AJAX)
@rh_bp.route('/employes/search')
@login_required
@permission_requise('employes')
def search_employes():
    term = request.args.get('term', '')
    if len(term) < 2:
        return {'employes': []}
    
    employes = Employee.query.filter(
        (Employee.nom.ilike(f'%{term}%')) |
        (Employee.prenom.ilike(f'%{term}%')) |
        (Employee.nom_complet.ilike(f'%{term}%')) |
        (Employee.poste.ilike(f'%{term}%'))
    ).limit(10).all()
    
    results = []
    for emp in employes:
        results.append({
            'id': emp.id,
            'nom_complet': emp.nom_complet,
            'poste': emp.poste,
            'departement': emp.departement,
            'statut': emp.statut
        })
    
    return {'employes': results}

