from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.forms import FormUtilisateur, AjouterRoleForm, ModifierMonCompteForm, AjouterTypeCongeForm, FormParametresPaie, FormAjouterCotisation, FormParametrePresence
from flask_login import login_required, current_user
from app.models import Utilisateur, Role, Permission, TypeConge, ParametresPaie, CotisationSociale, ParametrePresence
from app.utils.permissions import permission_requise


parametres_bp = Blueprint('parametres', __name__) 

@parametres_bp.route('/parametres', methods=['GET', 'POST'])
@login_required
@permission_requise('parametres')
def utilisateurs():
    form = FormUtilisateur()
    form.role.query = Role.query.all()
    form_role = AjouterRoleForm()
    utilisateurs = Utilisateur.query.all()
    roles = Role.query.all()
    permissions = Permission.query.all()

    if form.validate_on_submit():
        nouvel_utilisateur = Utilisateur(
            nom_utilisateur=form.nom_utilisateur.data,
            nom_complet=form.nom_complet.data,
            email=form.email.data,
            role=form.role.data, 
            actif=form.actif.data
        )
        nouvel_utilisateur.set_password(form.mot_de_passe.data)
        db.session.add(nouvel_utilisateur)
        db.session.commit()
        flash('Nouvel utilisateur ajouté avec succès', 'success')
        return redirect(url_for('parametres.utilisateurs'))

    return render_template('parametres/utilisateurs.html', form=form, form_role=form_role, utilisateurs=utilisateurs, roles=roles, permissions=permissions)

@parametres_bp.route('/parametres/utilisateurs/<int:id>/modifier', methods=['POST'])
@login_required
def modifier_utilisateur(id):
    utilisateur = Utilisateur.query.get_or_404(id)
    utilisateur.nom_utilisateur = request.form['nom_utilisateur']
    utilisateur.nom_complet = request.form['nom_complet']
    utilisateur.email = request.form['email']
    role_id = int(request.form['role'])
    utilisateur.role = Role.query.get(role_id)

    utilisateur.actif = 'actif' in request.form
    db.session.commit()
    flash("Utilisateur modifié avec succès", "success")
    return redirect(url_for('parametres.utilisateurs'))


@parametres_bp.route('/parametres/utilisateurs/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_utilisateur(id):
    utilisateur = Utilisateur.query.get_or_404(id)
    db.session.delete(utilisateur)
    db.session.commit()
    flash("Utilisateur supprimé avec succès", "success")
    return redirect(url_for('parametres.utilisateurs'))

@parametres_bp.route('/parametres/roles')
@login_required
def roles():
    roles = Role.query.all()
    permissions = Permission.query.all()
    return render_template('parametres/roles.html', roles=roles, permissions=permissions)

@parametres_bp.route('/parametres/ajouter-role', methods=['POST'])
@login_required
def ajouter_role():
    nom = request.form.get('nom')
    if nom:
        nouveau_role = Role(nom=nom)
        db.session.add(nouveau_role)
        db.session.commit()
        flash("Rôle ajouté avec succès.", "success")
    return redirect(url_for('parametres.utilisateurs'))

@parametres_bp.route('/parametres/modifier-permissions/<int:role_id>', methods=['POST'])
@login_required
def modifier_permissions(role_id):
    role = Role.query.get_or_404(role_id)
    selected_permissions_ids = request.form.getlist('permissions')
    selected_permissions = Permission.query.filter(Permission.id.in_(selected_permissions_ids)).all()
    role.permissions = selected_permissions
    db.session.commit()
    flash("Permissions mises à jour.", "success")
    return redirect(url_for('parametres.utilisateurs'))

@parametres_bp.route('/mon-compte', methods=['POST'])
@login_required
def modifier_mon_compte():
    form = ModifierMonCompteForm()
    if form.validate_on_submit():
        utilisateur = Utilisateur.query.get(current_user.id)
        utilisateur.nom_utilisateur = form.nom_utilisateur.data
        utilisateur.nom_complet = form.nom_complet.data
        utilisateur.email = form.email.data

        if form.mot_de_passe.data:
            utilisateur.set_password(form.mot_de_passe.data)

        db.session.commit()
        flash("Informations mises à jour avec succès.", "success")
    else:
        flash("Erreur lors de la modification du compte.", "danger")

    return redirect(request.referrer or url_for('dashboard.accueil'))


@parametres_bp.route('/parametres/conges', methods=['GET', 'POST'])
@login_required
@permission_requise('parametres')
def conges():
    form = AjouterTypeCongeForm()
    types_conge = TypeConge.query.all()
    profil_form = ModifierMonCompteForm(obj=current_user)  
    
    if form.validate_on_submit():
        nouveau_conge = TypeConge(
            nom=form.nom.data,
            duree_max_jours=form.duree_max_jours.data,
            validation_requise=form.validation_requise.data
        )
        db.session.add(nouveau_conge)
        db.session.commit()
        flash('Type de congé ajouté avec succès', 'success')
        return redirect(url_for('parametres.conges'))

    return render_template('parametres/conges.html', form=form, types_conge=types_conge, active_tab='conges')

@parametres_bp.route('/parametres/conges/<int:id>/modifier', methods=['POST'])
@login_required
@permission_requise('parametres')
def modifier_type_conge(id):
    conge = TypeConge.query.get_or_404(id)
    conge.nom = request.form['nom']
    conge.duree_max_jours = request.form['duree_max']
    conge.validation_requise = 'validation_requise' in request.form
    db.session.commit()
    flash('Type de congé modifié avec succès', 'success')
    return redirect(url_for('parametres.conges'))

@parametres_bp.route('/parametres/conges/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_type_conge(id):
    conge = TypeConge.query.get_or_404(id)
    db.session.delete(conge)
    db.session.commit()
    flash('Le congé a été supprimé', 'success')
    return redirect(url_for('parametres.conges'))

@parametres_bp.route('/parametres/paie', methods=['GET', 'POST'])
@login_required
def parametres_paie():
    form = FormParametresPaie()
    form_ajout = FormAjouterCotisation()
    cotisations = CotisationSociale.query.all()

    parametres = ParametresPaie.query.first()
    if not parametres:
        parametres = ParametresPaie(
            smic_horaire=242, plafond_cnps=7500, taux_transport=0,
            auto_calcule=True, jour_paiement=28,
            heures_hebdo=40, hs_25=25, hs_50=50
        )
        db.session.add(parametres)
        db.session.commit()

    if form.validate_on_submit():
        parametres.smic_horaire = form.smic_horaire.data
        parametres.plafond_cnps = form.plafond_cnps.data
        #parametres.taux_transport = form.taux_transport.data
        parametres.auto_calcule = form.auto_calcule.data
        parametres.jour_paiement = form.jour_paiement.data
        parametres.heures_hebdo = form.heures_hebdo.data
        parametres.hs_25 = form.hs_25.data
        parametres.hs_50 = form.hs_50.data
        db.session.commit()
        flash("Paramètres de paie mis à jour", "success")
        return redirect(url_for('parametres.parametres_paie'))
    else:
        # Pré-remplissage du formulaire
        form.smic_horaire.data = parametres.smic_horaire
        form.plafond_cnps.data = parametres.plafond_cnps
        #form.taux_transport.data = parametres.taux_transport
        form.auto_calcule.data = parametres.auto_calcule
        form.jour_paiement.data = parametres.jour_paiement
        form.heures_hebdo.data = parametres.heures_hebdo
        form.hs_25.data = parametres.hs_25
        form.hs_50.data = parametres.hs_50

    return render_template('parametres/paie.html', form=form, cotisations=cotisations, form_ajout=form_ajout)

@parametres_bp.route('/parametres/paie/cotisation/ajouter', methods=['POST'])
@login_required
def ajouter_cotisation():
    form = FormAjouterCotisation()
    if form.validate_on_submit():
        nouvelle_cotisation = CotisationSociale(
            libelle=form.libelle.data,
            taux_salarial=form.taux_salarial.data,
            taux_patronal=form.taux_patronal.data
        )
        db.session.add(nouvelle_cotisation)
        db.session.commit()
        flash("Cotisation ajoutée avec succès", "success")
    else:
        flash("Erreur lors de l'ajout de la cotisation", "danger")
    return redirect(url_for('parametres.parametres_paie'))

@parametres_bp.route('/parametres/paie/<int:id>/modifier', methods=['POST'])
@login_required
def modifier_cotisation(id):
    cotisation = CotisationSociale.query.get_or_404(id)

    try:
        cotisation.taux_salarial = float(request.form['taux_salarial'])
        cotisation.taux_patronal = float(request.form['taux_patronal'])
        db.session.commit()
        flash("Cotisation mise à jour avec succès", "success")
    except Exception as e:
        db.session.rollback()
        flash("Erreur lors de la mise à jour : " + str(e), "danger")

    return redirect(url_for('parametres.parametres_paie'))

@parametres_bp.route('/parametres/presences', methods=['GET', 'POST'])
@login_required
@permission_requise('parametres')
def parametres_presences():
    param = ParametrePresence.query.first()
    form = FormParametrePresence(obj=param)

    if form.validate_on_submit():
        if not param:
            param = ParametrePresence()
            db.session.add(param)

        form.populate_obj(param)
        db.session.commit()
        flash("Paramètres de présence mis à jour", "success")
        return redirect(url_for('parametres.parametres_presences'))

    return render_template('parametres/presences.html', form=form, active_tab='presences')
