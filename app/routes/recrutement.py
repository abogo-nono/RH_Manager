from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from app import db
from app.models import OffreEmploi, Candidat, Entretien
from flask_login import login_required
from app.utils.permissions import permission_requise

recrutement_bp = Blueprint('recrutement', __name__)

@recrutement_bp.route('/recrutement')
@login_required
@permission_requise('recrutement')
def list_offres():
    # Récupère toutes les offres
    offres = OffreEmploi.query.filter(OffreEmploi.statut != 'Supprimée').all()
    liste = []
    for offre in offres:
        nb_candidats = len(offre.candidats)
        nb_entretiens = len(offre.entretiens)
        jours_restants = max(0, (offre.date_cloture - datetime.utcnow().date()).days)
        liste.append({
            'id': offre.id,
            'titre': offre.titre,
            'departement': offre.departement,
            'description': offre.description,
            'statut': offre.statut,
            'nb_candidats': nb_candidats,
            'nb_entretiens': nb_entretiens,
            'jours_restants': jours_restants,
            'date_publication': offre.date_publication,
            'date_cloture': offre.date_cloture,
            'candidats': offre.candidats,
            'entretiens': offre.entretiens
        })
    return render_template('recrutement/list.html', offres=liste)

@recrutement_bp.route('/recrutement/publier/<int:id>')
def publier_offre(id):
    offre = OffreEmploi.query.get_or_404(id)
    if offre.statut == 'Brouillon':
        offre.statut = 'Actif'
        db.session.commit()
        flash('Offre publiée avec succès.', 'success')
    return redirect(url_for('recrutement.list_offres'))

@recrutement_bp.route('/recrutement/creer', methods=['POST'])
def creer_offre():
    titre = request.form.get('titre')
    departement = request.form.get('departement')
    description = request.form.get('description')
    requirements = request.form.get('requirements')
    date_cloture = datetime.strptime(request.form.get('date_cloture'), '%Y-%m-%d')
    statut = request.form.get('statut', 'Brouillon')

    nouvelle_offre = OffreEmploi(
        titre=titre,
        departement=departement,
        description=description,
        requirements=requirements,
        date_publication=datetime.utcnow().date(),
        date_cloture=date_cloture,
        statut=statut
    )
    db.session.add(nouvelle_offre)
    db.session.commit()
    flash('Nouvelle offre créée.', 'success')
    return redirect(url_for('recrutement.list_offres'))

@recrutement_bp.route('/recrutement/<int:offre_id>/planifier_entretien/<int:candidat_id>', methods=['POST'])
def planifier_entretien(offre_id, candidat_id):
    titre = request.form.get('titre')
    datetime_str = request.form.get('datetime')
    duree = int(request.form.get('duree'))
    participants = request.form.get('participants')
    notes = request.form.get('notes')

    entretien = Entretien(
        candidat_id=candidat_id,
        offre_emploi_id=offre_id,
        titre=titre,
        datetime=datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M'),
        duree=duree,
        participants=participants,
        notes=notes
    )
    db.session.add(entretien)

    candidat = Candidat.query.get_or_404(candidat_id)
    candidat.statut = 'entretien planifié'
    db.session.commit()

    flash('Entretien planifié avec succès.', 'success')
    return redirect(url_for('recrutement.list_offres'))

@recrutement_bp.route('/recrutement/<int:offre_id>/candidat/<int:candidat_id>/accepter')
def accepter_candidat(offre_id, candidat_id):
    candidat = Candidat.query.get_or_404(candidat_id)
    candidat.statut = 'accepté'

    # Créer un nouvel employé (modifie selon ton modèle)
    from app.models import Employee
    new_employee = Employee(
        nom=candidat.nom,
        email=candidat.email,
        poste=candidat.offre.titre,
        departement=candidat.offre.departement,
        date_embauche=datetime.utcnow().date(),
        statut='Présent'
    )
    db.session.add(new_employee)
    db.session.commit()

    flash(f'{candidat.nom} a été embauché comme employé.', 'success')
    return redirect(url_for('recrutement.list_offres'))

@recrutement_bp.route('/recrutement/<int:offre_id>/candidat/<int:candidat_id>/refuser', methods=['POST'])
def refuser_candidat(offre_id, candidat_id):
    candidat = Candidat.query.get_or_404(candidat_id)
    candidat.statut = 'refusé'
    db.session.commit()
    flash(f"{candidat.nom} a été refusé.", "info")
    return redirect(url_for('recrutement.list_offres'))

@recrutement_bp.route('/offre/<int:offre_id>/details')
def details_offre(offre_id):
    offre = OffreEmploi.query.get_or_404(offre_id)
    return render_template('recrutement/detail_modal.html', offre=offre)

@recrutement_bp.route('/recrutement/supprimer/<int:id>', methods=['POST'])
def supprimer_offre(id):
    offre = OffreEmploi.query.get_or_404(id)
    offre.statut = 'Supprimée'
    offre.date_suppression = datetime.utcnow().date()
    db.session.commit()
    flash('L\'offre à bien été supprimée.', 'info')
    return redirect(url_for('recrutement.list_offres'))

@recrutement_bp.route('/recrutement/historique')
def historique_offres_supprimees():
    offres_supprimees = OffreEmploi.query.filter_by(statut='Supprimée').all()
    return render_template('recrutement/historique.html', offres=offres_supprimees)

#***************************************** TEST ********************************************************************************

#@recrutement_bp.route('/recrutement/<int:offre_id>/ajouter_candidat_test')
#def ajouter_candidat_test(offre_id):
#    from datetime import datetime
#    from app.models import Candidat

#    candidat = Candidat(
#        nom='Jean Testeur',
#        email='jean.testeur@example.com',
#        cv='cv_test.pdf',  # un fichier factice dans /static/uploads/
#       lettre_motivation='lettre_test.pdf',
#        date_soumission=datetime.utcnow().date(),
#        statut='en cours d\'examen',
#        offre_emploi_id=offre_id
#    )
#    db.session.add(candidat)
#    db.session.commit()
#    return f"Candidat test ajouté à l'offre {offre_id} !"

#@recrutement_bp.route('/recrutement/<int:offre_id>/planifier_entretien_test/<int:candidat_id>')
#def planifier_entretien_test(offre_id, candidat_id):
#    from datetime import datetime, timedelta
#    from app.models import Entretien, Candidat

#    entretien = Entretien(
#        titre='Entretien Test',
#        datetime=datetime.utcnow() + timedelta(days=1),
#        duree=30,
#        participants='HR Manager, Responsable Technique',
#        notes='Premier contact.',
#        candidat_id=candidat_id,
#        offre_emploi_id=offre_id
#    )
#    db.session.add(entretien)

#    candidat = Candidat.query.get_or_404(candidat_id)
#    candidat.statut = 'entretien planifié'

#    db.session.commit()
#    return f"Entretien test planifié pour le candidat {candidat_id} !"



