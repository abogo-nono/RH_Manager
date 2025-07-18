from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os, uuid
from app import db, mail
from app.models import OffreEmploi, Candidat, Conge, Employee, Utilisateur, TypeConge
from app.forms import DemandeCongeForm
from flask_login import current_user

public_bp = Blueprint('public', __name__)

# Dossier pour stocker CV + lettres
UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'pdf'}

# Vérifie l'extension (PDF only)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@public_bp.route('/candidature/<int:offre_id>', methods=['GET', 'POST'])
def postuler(offre_id):
    offre = OffreEmploi.query.get_or_404(offre_id)

    if request.method == 'POST':
        nom = request.form['nom']
        email = request.form['email']
        telephone = request.form['telephone']
        cv_file = request.files['cv']
        lettre_file = request.files['lettre']

        # Vérifie les fichiers
        if not (cv_file and allowed_file(cv_file.filename)) or not (lettre_file and allowed_file(lettre_file.filename)):
            flash("Veuillez télécharger des fichiers PDF valides.", "danger")
            return redirect(request.url)

        # Renomme et sauvegarde fichiers
        timestamp = int(datetime.utcnow().timestamp())
        cv_filename = secure_filename(f"{timestamp}_CV_{cv_file.filename}")
        lettre_filename = secure_filename(f"{timestamp}_Lettre_{lettre_file.filename}")

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Crée dossier si pas présent
        cv_file.save(os.path.join(UPLOAD_FOLDER, cv_filename))
        lettre_file.save(os.path.join(UPLOAD_FOLDER, lettre_filename))

        # Crée le candidat en base
        candidat = Candidat(
            nom=nom,
            email=email,
            telephone=telephone,
            cv=cv_filename,
            lettre_motivation=lettre_filename,
            date_soumission=datetime.utcnow().date(),
            statut='en cours d\'examen',
            offre_emploi_id=offre.id
        )
        db.session.add(candidat)
        db.session.commit()

        # Envoie un mail interne sans pièce jointe
#        subject = f"Nouvelle candidature pour {offre.titre}"
#        body = f"""
#        Nouvelle candidature reçue :

#        Nom : {nom}
#        Email : {email}
#        Offre : {offre.titre}
#        """

#        msg = Message(subject, recipients=['mbiadjeutenga@gmail.com']) 
#        msg.body = body
#        mail.send(msg)

        flash("Votre candidature a bien été envoyée ! Merci.", "success")
        return redirect(url_for('public.postuler', offre_id=offre.id))

    return render_template('public/candidature.html', offre=offre)

@public_bp.route('/demandes_conge', methods=['GET', 'POST'])
def demandes_conge():
    form = DemandeCongeForm()
    form.employe_id.choices = [(e.id, e.nom) for e in Employee.query.all()]
    
    if form.validate_on_submit():
        type_conge = form.type.data
        date_debut = form.date_debut.data
        type_obj = TypeConge.query.filter_by(nom=type_conge).first()
        duree = type_obj.duree_max_jours if type_obj else 1
        date_fin = date_debut + timedelta(days=duree - 1)

        demande = Conge(
            reference=f"DCG-{uuid.uuid4().hex[:8]}",
            employe_id=form.employe_id.data,
            type=type_conge,
            date_debut=date_debut,
            date_fin=date_fin,
            duree=duree,
            motif=form.motif.data,
            statut="En attente",
            approbateur_id=current_user.id
        )
        db.session.add(demande)
        db.session.commit()
        flash("Demande de congé soumise avec succès", "success")
        return redirect(url_for('conges_temps.demandes_conge'))

    demandes = Conge.query.order_by(Conge.date_creation.desc()).all()

    type_conges = TypeConge.query.all()
    type_conges_json = {tc.nom: tc.duree_max_jours for tc in type_conges}

    return render_template("conges_temps/demandes_conge.html", form=form, demandes=demandes, type_conges=type_conges,type_conges_json=type_conges_json)
