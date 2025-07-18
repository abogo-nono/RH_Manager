"""
Module Gestion de la Paie - Routes
Routes pour la gestion complète des bulletins de paie, calculs salariaux, 
cotisations et rapports de paie.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from sqlalchemy import func, desc, asc, extract, and_, or_
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import json
import pandas as pd
from io import BytesIO
import os

from app import db
from app.models import (Employee, BulletinPaie, ElementPaie, ParametresPaie, CotisationSociale,
                       AvanceSalaire, RemboursementAvance, TypeElementPaie, ParametreCalculPaie,
                       HistoriquePaie, HeuresTravail, Absence, Conge, Utilisateur)
from app.forms import (BulletinPaieForm, ElementPaieForm, AvanceSalaireForm, TypeElementPaieForm,
                      ParametreCalculPaieForm, RapportPaieForm, CalculPaieForm,
                      FormParametresPaie, FormAjouterCotisation)
from app.utils.permissions import permission_requise
from app.utils.email_service import email_service

# Blueprint pour les routes de paie
paie_bp = Blueprint('paie', __name__)

# ============= DASHBOARD ET VUES PRINCIPALES =============

@paie_bp.route('/paie')
@login_required
@permission_requise('gestion_paie')
def dashboard():
    """Dashboard principal du module paie"""
    # Période actuelle
    today = date.today()
    mois_actuel = today.month
    annee_actuelle = today.year
    
    # Statistiques globales
    stats = {
        'total_employes': Employee.query.filter_by(statut='Actif').count(),
        'bulletins_mois': BulletinPaie.query.filter_by(mois=mois_actuel, annee=annee_actuelle).count(),
        'bulletins_valides': BulletinPaie.query.filter_by(mois=mois_actuel, annee=annee_actuelle, valide=True).count(),
        'bulletins_payes': BulletinPaie.query.filter_by(mois=mois_actuel, annee=annee_actuelle, statut='payé').count(),
        'masse_salariale_mois': 0.0,
        'total_cotisations': 0.0,
        'avances_en_cours': 0.0
    }
    
    # Calcul de la masse salariale du mois
    bulletins_mois = BulletinPaie.query.filter_by(mois=mois_actuel, annee=annee_actuelle).all()
    stats['masse_salariale_mois'] = sum([b.salaire_brut for b in bulletins_mois])
    stats['total_cotisations'] = sum([b.total_cotisations_salariales + b.total_cotisations_patronales for b in bulletins_mois])
    
    # Avances en cours
    avances_en_cours = AvanceSalaire.query.filter(
        AvanceSalaire.statut.in_(['accorde', 'verse']),
        AvanceSalaire.solde_restant > 0
    ).all()
    stats['avances_en_cours'] = sum([a.solde_restant for a in avances_en_cours])
    
    # Évolution de la masse salariale (6 derniers mois)
    masse_salariale_evolution = []
    for i in range(6):
        date_ref = today - relativedelta(months=i)
        bulletins = BulletinPaie.query.filter_by(mois=date_ref.month, annee=date_ref.year).all()
        masse = sum([b.salaire_brut for b in bulletins])
        masse_salariale_evolution.append({
            'mois': date_ref.strftime('%b %Y'),
            'montant': masse
        })
    
    # Bulletins récents
    bulletins_recents = BulletinPaie.query.join(Employee).order_by(
        BulletinPaie.date_creation.desc()
    ).limit(10).all()
    
    # Avances en attente d'approbation
    avances_attente = AvanceSalaire.query.filter_by(statut='demande').order_by(
        AvanceSalaire.date_demande.desc()
    ).limit(5).all()
    
    return render_template('paie/dashboard.html',
                         stats=stats,
                         masse_salariale_evolution=reversed(masse_salariale_evolution),
                         bulletins_recents=bulletins_recents,
                         avances_attente=avances_attente)

@paie_bp.route('/paie/bulletins')
@login_required
@permission_requise('gestion_paie')
def liste_bulletins():
    """Liste des bulletins de paie avec filtres"""
    # Filtres
    employe_id = request.args.get('employe_id', type=int)
    mois = request.args.get('mois', type=int)
    annee = request.args.get('annee', type=int)
    statut = request.args.get('statut')
    departement = request.args.get('departement')
    
    # Query de base
    query = BulletinPaie.query.join(Employee)
    
    # Appliquer les filtres
    if employe_id:
        query = query.filter(BulletinPaie.employe_id == employe_id)
    if mois:
        query = query.filter(BulletinPaie.mois == mois)
    if annee:
        query = query.filter(BulletinPaie.annee == annee)
    if statut:
        query = query.filter(BulletinPaie.statut == statut)
    if departement:
        query = query.filter(Employee.departement == departement)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    bulletins = query.order_by(BulletinPaie.annee.desc(), BulletinPaie.mois.desc(), Employee.nom).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Données pour les filtres
    employes = Employee.query.filter_by(statut='Actif').order_by(Employee.nom).all()
    departements = db.session.query(Employee.departement.distinct()).filter(
        Employee.departement.isnot(None)
    ).all()
    
    # Statistiques des bulletins filtrés
    stats = {
        'total': query.count(),
        'valides': query.filter(BulletinPaie.valide == True).count(),
        'masse_salariale': query.with_entities(func.sum(BulletinPaie.salaire_brut)).scalar() or 0,
        'total_net': query.with_entities(func.sum(BulletinPaie.salaire_net)).scalar() or 0
    }
    
    return render_template('paie/bulletins/liste.html',
                         bulletins=bulletins,
                         employes=employes,
                         departements=departements,
                         stats=stats,
                         filters={
                             'employe_id': employe_id,
                             'mois': mois,
                             'annee': annee,
                             'statut': statut,
                             'departement': departement
                         })

@paie_bp.route('/paie/bulletins/nouveau', methods=['GET', 'POST'])
@login_required
@permission_requise('gestion_paie')
def nouveau_bulletin():
    """Créer un nouveau bulletin de paie"""
    form = BulletinPaieForm()
    
    # Charger les employés
    employes = Employee.query.filter_by(statut='Actif').order_by(Employee.nom).all()
    form.employe_id.choices = [(0, 'Sélectionner un employé')] + [(e.id, f"{e.nom} {e.prenom or ''}") for e in employes]
    
    if form.validate_on_submit():
        try:
            # Vérifier si un bulletin existe déjà
            bulletin_existant = BulletinPaie.query.filter_by(
                employe_id=form.employe_id.data,
                mois=form.mois.data,
                annee=form.annee.data
            ).first()
            
            if bulletin_existant:
                flash('Un bulletin existe déjà pour cet employé et cette période', 'error')
                return redirect(url_for('paie.nouveau_bulletin'))
            
            # Générer le numéro de bulletin
            numero_bulletin = generer_numero_bulletin(form.employe_id.data, form.mois.data, form.annee.data)
            
            # Récupérer l'employé et ses paramètres
            employe = Employee.query.get(form.employe_id.data)
            parametres_employe = ParametreCalculPaie.query.filter_by(employe_id=employe.id, actif=True).first()
            
            # Créer le bulletin
            bulletin = BulletinPaie(
                employe_id=form.employe_id.data,
                periode_debut=form.periode_debut.data,
                periode_fin=form.periode_fin.data,
                mois=form.mois.data,
                annee=form.annee.data,
                numero_bulletin=numero_bulletin,
                salaire_base=parametres_employe.salaire_base_mensuel if parametres_employe else employe.salaire_base,
                nb_jours_ouvres=form.nb_jours_ouvres.data,
                nb_jours_travailles=form.nb_jours_travailles.data,
                nb_heures_normales=form.nb_heures_normales.data or 0,
                nb_heures_supplementaires=form.nb_heures_supplementaires.data or 0,
                nb_jours_conges=form.nb_jours_conges.data or 0,
                nb_jours_absences=form.nb_jours_absences.data or 0,
                primes_bonus=form.primes_bonus.data or 0,
                indemnites=form.indemnites.data or 0,
                avantages_nature=form.avantages_nature.data or 0,
                retenues_diverses=form.retenues_diverses.data or 0,
                mode_paiement=form.mode_paiement.data,
                reference_paiement=form.reference_paiement.data,
                cree_par=current_user.id,
                salaire_brut=0,  # Sera calculé
                salaire_net=0    # Sera calculé
            )
            
            db.session.add(bulletin)
            db.session.flush()
            
            # Calculer automatiquement le bulletin
            calculer_bulletin_paie(bulletin)
            
            # Enregistrer l'historique
            historique = HistoriquePaie(
                bulletin_id=bulletin.id,
                action='creation',
                nouveau_statut=bulletin.statut,
                commentaire='Création du bulletin de paie',
                utilisateur_id=current_user.id
            )
            db.session.add(historique)
            
            db.session.commit()
            
            # Envoyer notification email si le bulletin est validé
            if bulletin.valide:
                try:
                    email_service.notify_payslip_available(bulletin.id)
                except Exception as e:
                    print(f"Erreur envoi email bulletin: {e}")
            
            flash('Bulletin de paie créé avec succès', 'success')
            return redirect(url_for('paie.detail_bulletin', id=bulletin.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du bulletin: {e}', 'error')
    
    return render_template('paie/bulletins/nouveau.html', form=form)

@paie_bp.route('/paie/bulletins/<int:id>')
@login_required
@permission_requise('gestion_paie')
def detail_bulletin(id):
    """Détail d'un bulletin de paie"""
    bulletin = BulletinPaie.query.get_or_404(id)
    
    # Historique du bulletin
    historique = HistoriquePaie.query.filter_by(bulletin_id=id).order_by(
        HistoriquePaie.date_action.desc()
    ).all()
    
    # Éléments de paie groupés par catégorie
    elements_gains = ElementPaie.query.filter_by(bulletin_id=id, type_element='gain').order_by(
        ElementPaie.ordre_affichage
    ).all()
    elements_retenues = ElementPaie.query.filter_by(bulletin_id=id, type_element='retenue').order_by(
        ElementPaie.ordre_affichage
    ).all()
    
    # Remboursements d'avances pour ce bulletin
    remboursements = RemboursementAvance.query.filter_by(bulletin_id=id).all()
    
    return render_template('paie/bulletins/detail.html',
                         bulletin=bulletin,
                         historique=historique,
                         elements_gains=elements_gains,
                         elements_retenues=elements_retenues,
                         remboursements=remboursements)

@paie_bp.route('/paie/bulletins/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
@permission_requise('gestion_paie')
def modifier_bulletin(id):
    """Modifier un bulletin de paie"""
    bulletin = BulletinPaie.query.get_or_404(id)
    
    # Vérifier que le bulletin n'est pas payé
    if bulletin.statut == 'payé':
        flash('Impossible de modifier un bulletin déjà payé', 'error')
        return redirect(url_for('paie.detail_bulletin', id=id))
    
    form = BulletinPaieForm(obj=bulletin)
    
    # Charger les employés
    employes = Employee.query.filter_by(statut='Actif').order_by(Employee.nom).all()
    form.employe_id.choices = [(e.id, f"{e.nom} {e.prenom or ''}") for e in employes]
    
    if form.validate_on_submit():
        try:
            # Sauvegarder les anciennes valeurs pour l'historique
            anciennes_valeurs = {
                'nb_jours_travailles': bulletin.nb_jours_travailles,
                'nb_heures_normales': bulletin.nb_heures_normales,
                'nb_heures_supplementaires': bulletin.nb_heures_supplementaires,
                'primes_bonus': bulletin.primes_bonus,
                'indemnites': bulletin.indemnites,
                'avantages_nature': bulletin.avantages_nature,
                'retenues_diverses': bulletin.retenues_diverses
            }
            
            # Mettre à jour les champs
            bulletin.nb_jours_travailles = form.nb_jours_travailles.data
            bulletin.nb_heures_normales = form.nb_heures_normales.data or 0
            bulletin.nb_heures_supplementaires = form.nb_heures_supplementaires.data or 0
            bulletin.nb_jours_conges = form.nb_jours_conges.data or 0
            bulletin.nb_jours_absences = form.nb_jours_absences.data or 0
            bulletin.primes_bonus = form.primes_bonus.data or 0
            bulletin.indemnites = form.indemnites.data or 0
            bulletin.avantages_nature = form.avantages_nature.data or 0
            bulletin.retenues_diverses = form.retenues_diverses.data or 0
            bulletin.mode_paiement = form.mode_paiement.data
            bulletin.reference_paiement = form.reference_paiement.data
            
            # Recalculer le bulletin
            calculer_bulletin_paie(bulletin)
            
            # Enregistrer l'historique
            nouvelles_valeurs = {
                'nb_jours_travailles': bulletin.nb_jours_travailles,
                'nb_heures_normales': bulletin.nb_heures_normales,
                'nb_heures_supplementaires': bulletin.nb_heures_supplementaires,
                'primes_bonus': bulletin.primes_bonus,
                'indemnites': bulletin.indemnites,
                'avantages_nature': bulletin.avantages_nature,
                'retenues_diverses': bulletin.retenues_diverses
            }
            
            historique = HistoriquePaie(
                bulletin_id=bulletin.id,
                action='modification',
                ancien_statut=bulletin.statut,
                nouveau_statut=bulletin.statut,
                anciennes_valeurs=anciennes_valeurs,
                nouvelles_valeurs=nouvelles_valeurs,
                commentaire='Modification du bulletin de paie',
                utilisateur_id=current_user.id
            )
            db.session.add(historique)
            
            db.session.commit()
            
            flash('Bulletin de paie modifié avec succès', 'success')
            return redirect(url_for('paie.detail_bulletin', id=bulletin.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification: {e}', 'error')
    
    return render_template('paie/bulletins/modifier.html', form=form, bulletin=bulletin)

@paie_bp.route('/paie/bulletins/<int:id>/valider', methods=['POST'])
@login_required
@permission_requise('gestion_paie')
def valider_bulletin(id):
    """Valider un bulletin de paie"""
    bulletin = BulletinPaie.query.get_or_404(id)
    
    if bulletin.statut == 'payé':
        flash('Ce bulletin est déjà payé', 'error')
        return redirect(url_for('paie.detail_bulletin', id=id))
    
    try:
        # Valider le bulletin
        bulletin.valide = True
        bulletin.statut = 'validé'
        bulletin.date_validation = datetime.utcnow()
        bulletin.valide_par = current_user.id
        
        # Enregistrer l'historique
        historique = HistoriquePaie(
            bulletin_id=bulletin.id,
            action='validation',
            ancien_statut='brouillon',
            nouveau_statut='validé',
            commentaire='Validation du bulletin de paie',
            utilisateur_id=current_user.id
        )
        db.session.add(historique)
        
        db.session.commit()
        
        flash('Bulletin validé avec succès', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la validation: {e}', 'error')
    
    return redirect(url_for('paie.detail_bulletin', id=id))

@paie_bp.route('/paie/bulletins/<int:id>/marquer-paye', methods=['POST'])
@login_required
@permission_requise('gestion_paie')
def marquer_paye(id):
    """Marquer un bulletin comme payé"""
    bulletin = BulletinPaie.query.get_or_404(id)
    
    if not bulletin.valide:
        flash('Le bulletin doit être validé avant d\'être marqué comme payé', 'error')
        return redirect(url_for('paie.detail_bulletin', id=id))
    
    try:
        # Marquer comme payé
        bulletin.statut = 'payé'
        bulletin.date_paiement = date.today()
        
        # Enregistrer l'historique
        historique = HistoriquePaie(
            bulletin_id=bulletin.id,
            action='paiement',
            ancien_statut='validé',
            nouveau_statut='payé',
            commentaire='Paiement du bulletin de paie',
            utilisateur_id=current_user.id
        )
        db.session.add(historique)
        
        db.session.commit()
        
        flash('Bulletin marqué comme payé', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors du marquage: {e}', 'error')
    
    return redirect(url_for('paie.detail_bulletin', id=id))

# ============= GESTION DES AVANCES =============

@paie_bp.route('/paie/avances')
@login_required
@permission_requise('gestion_paie')
def liste_avances():
    """Liste des avances sur salaire"""
    # Filtres
    employe_id = request.args.get('employe_id', type=int)
    statut = request.args.get('statut')
    
    # Query de base
    query = AvanceSalaire.query.join(Employee)
    
    # Appliquer les filtres
    if employe_id:
        query = query.filter(AvanceSalaire.employe_id == employe_id)
    if statut:
        query = query.filter(AvanceSalaire.statut == statut)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    avances = query.order_by(AvanceSalaire.date_demande.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Données pour les filtres
    employes = Employee.query.filter_by(statut='Actif').order_by(Employee.nom).all()
    
    # Statistiques
    stats = {
        'total_demandes': query.count(),
        'en_attente': query.filter(AvanceSalaire.statut == 'demande').count(),
        'accordees': query.filter(AvanceSalaire.statut.in_(['accorde', 'verse'])).count(),
        'montant_total': query.with_entities(func.sum(AvanceSalaire.montant_accorde)).scalar() or 0,
        'solde_restant': query.with_entities(func.sum(AvanceSalaire.solde_restant)).scalar() or 0
    }
    
    return render_template('paie/avances/liste.html',
                         avances=avances,
                         employes=employes,
                         stats=stats,
                         filters={
                             'employe_id': employe_id,
                             'statut': statut
                         })

@paie_bp.route('/paie/avances/nouvelle', methods=['GET', 'POST'])
@login_required
@permission_requise('gestion_paie')
def nouvelle_avance():
    """Créer une nouvelle avance sur salaire"""
    form = AvanceSalaireForm()
    
    # Charger les employés
    employes = Employee.query.filter_by(statut='Actif').order_by(Employee.nom).all()
    form.employe_id.choices = [(0, 'Sélectionner un employé')] + [(e.id, f"{e.nom} {e.prenom or ''}") for e in employes]
    
    if form.validate_on_submit():
        try:
            # Calculer le montant de mensualité
            montant_mensualite = form.montant_accorde.data / form.nb_mensualites.data if form.montant_accorde.data else 0
            
            # Créer l'avance
            avance = AvanceSalaire(
                employe_id=form.employe_id.data,
                montant_demande=form.montant_demande.data,
                montant_accorde=form.montant_accorde.data or form.montant_demande.data,
                motif=form.motif.data,
                date_demande=form.date_demande.data,
                date_accord=form.date_accord.data,
                date_versement=form.date_versement.data,
                nb_mensualites=form.nb_mensualites.data,
                montant_mensualite=montant_mensualite,
                solde_restant=form.montant_accorde.data or form.montant_demande.data,
                statut=form.statut.data,
                demandeur_id=current_user.id,
                commentaire_approbation=form.commentaire_approbation.data
            )
            
            db.session.add(avance)
            db.session.commit()
            
            flash('Avance sur salaire créée avec succès', 'success')
            return redirect(url_for('paie.liste_avances'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création: {e}', 'error')
    
    return render_template('paie/avances/nouvelle.html', form=form)

# ============= FONCTIONS UTILITAIRES =============

def generer_numero_bulletin(employe_id, mois, annee):
    """Génère un numéro unique pour le bulletin"""
    employe = Employee.query.get(employe_id)
    code_employe = f"{employe.nom[:3].upper()}{employe.id:03d}"
    return f"PAY{annee}{mois:02d}{code_employe}"

def calculer_bulletin_paie(bulletin):
    """Calcule tous les éléments d'un bulletin de paie"""
    try:
        # Récupérer les paramètres globaux
        parametres = ParametresPaie.query.first()
        if not parametres:
            raise Exception("Paramètres de paie non configurés")
        
        # Récupérer les paramètres spécifiques à l'employé
        parametres_employe = ParametreCalculPaie.query.filter_by(
            employe_id=bulletin.employe_id, 
            actif=True
        ).first()
        
        # Calculer le salaire de base au prorata
        salaire_base_prorata = bulletin.salaire_base * (bulletin.nb_jours_travailles / bulletin.nb_jours_ouvres)
        
        # Calculer les heures supplémentaires
        taux_horaire = bulletin.salaire_base / (parametres.heures_hebdo * 52 / 12)
        montant_hs = bulletin.nb_heures_supplementaires * taux_horaire * (1 + parametres.hs_25 / 100)
        
        # Calculer le salaire brut
        bulletin.salaire_brut = (salaire_base_prorata + montant_hs + 
                                bulletin.primes_bonus + bulletin.indemnites + 
                                bulletin.avantages_nature)
        
        # Supprimer les anciens éléments de paie
        ElementPaie.query.filter_by(bulletin_id=bulletin.id).delete()
        
        # Créer les éléments de paie
        # Salaire de base
        element_base = ElementPaie(
            bulletin_id=bulletin.id,
            libelle="Salaire de base",
            code="SAL_BASE",
            categorie="salaire",
            type_element="gain",
            montant=salaire_base_prorata,
            ordre_affichage=1
        )
        db.session.add(element_base)
        
        # Heures supplémentaires
        if montant_hs > 0:
            element_hs = ElementPaie(
                bulletin_id=bulletin.id,
                libelle="Heures supplémentaires",
                code="HEURES_SUP",
                categorie="prime",
                type_element="gain",
                montant=montant_hs,
                ordre_affichage=2
            )
            db.session.add(element_hs)
        
        # Primes et indemnités
        if bulletin.primes_bonus > 0:
            element_prime = ElementPaie(
                bulletin_id=bulletin.id,
                libelle="Primes et bonus",
                code="PRIMES",
                categorie="prime",
                type_element="gain",
                montant=bulletin.primes_bonus,
                ordre_affichage=3
            )
            db.session.add(element_prime)
        
        if bulletin.indemnites > 0:
            element_indemnite = ElementPaie(
                bulletin_id=bulletin.id,
                libelle="Indemnités",
                code="INDEMNITES",
                categorie="indemnite",
                type_element="gain",
                montant=bulletin.indemnites,
                ordre_affichage=4
            )
            db.session.add(element_indemnite)
        
        # Avantages en nature
        if bulletin.avantages_nature > 0:
            element_avantage = ElementPaie(
                bulletin_id=bulletin.id,
                libelle="Avantages en nature",
                code="AVANTAGES",
                categorie="avantage",
                type_element="gain",
                montant=bulletin.avantages_nature,
                ordre_affichage=5
            )
            db.session.add(element_avantage)
        
        # Calculer et créer les cotisations
        total_cotisations_salariales = 0
        total_cotisations_patronales = 0
        
        cotisations = CotisationSociale.query.filter_by(actif=True).order_by(CotisationSociale.ordre_affichage).all()
        ordre_cotisation = 10
        
        for cotisation in cotisations:
            # Calculer la base de cotisation
            base_cotisation = bulletin.salaire_brut
            if cotisation.plafond_application:
                base_cotisation = min(base_cotisation, cotisation.plafond_application)
            
            # Calculer les montants
            montant_salarial = base_cotisation * (cotisation.taux_salarial / 100)
            montant_patronal = base_cotisation * (cotisation.taux_patronal / 100)
            
            # Appliquer les limites
            if cotisation.minimum_cotisation:
                montant_salarial = max(montant_salarial, cotisation.minimum_cotisation)
                montant_patronal = max(montant_patronal, cotisation.minimum_cotisation)
            
            if cotisation.maximum_cotisation:
                montant_salarial = min(montant_salarial, cotisation.maximum_cotisation)
                montant_patronal = min(montant_patronal, cotisation.maximum_cotisation)
            
            # Créer l'élément de cotisation salariale
            if montant_salarial > 0:
                element_cotisation = ElementPaie(
                    bulletin_id=bulletin.id,
                    libelle=f"{cotisation.libelle} (part salariale)",
                    code=f"{cotisation.code}_SAL",
                    categorie="cotisation",
                    type_element="retenue",
                    base_calcul=base_cotisation,
                    taux=cotisation.taux_salarial,
                    montant=montant_salarial,
                    part_salariale=montant_salarial,
                    part_patronale=montant_patronal,
                    ordre_affichage=ordre_cotisation
                )
                db.session.add(element_cotisation)
                total_cotisations_salariales += montant_salarial
                ordre_cotisation += 1
        
        # Retenues diverses
        if bulletin.retenues_diverses > 0:
            element_retenue = ElementPaie(
                bulletin_id=bulletin.id,
                libelle="Retenues diverses",
                code="RETENUES",
                categorie="retenue",
                type_element="retenue",
                montant=bulletin.retenues_diverses,
                ordre_affichage=50
            )
            db.session.add(element_retenue)
        
        # Calculer l'impôt sur le salaire
        salaire_imposable = bulletin.salaire_brut - total_cotisations_salariales
        salaire_imposable_avec_abattement = salaire_imposable * (1 - parametres.abattement_professionnel)
        impot_salaire = salaire_imposable_avec_abattement * (parametres.taux_impot_liberatoire / 100)
        
        # Créer l'élément d'impôt
        if impot_salaire > 0:
            element_impot = ElementPaie(
                bulletin_id=bulletin.id,
                libelle="Impôt sur le salaire",
                code="IMPOT",
                categorie="fiscale",
                type_element="retenue",
                base_calcul=salaire_imposable_avec_abattement,
                taux=parametres.taux_impot_liberatoire,
                montant=impot_salaire,
                ordre_affichage=60
            )
            db.session.add(element_impot)
        
        # Gérer les remboursements d'avances
        total_remboursements = 0
        avances_a_rembourser = AvanceSalaire.query.filter(
            AvanceSalaire.employe_id == bulletin.employe_id,
            AvanceSalaire.statut.in_(['accorde', 'verse']),
            AvanceSalaire.solde_restant > 0
        ).all()
        
        for avance in avances_a_rembourser:
            montant_remboursement = min(avance.montant_mensualite, avance.solde_restant)
            
            # Créer l'élément de remboursement
            element_remboursement = ElementPaie(
                bulletin_id=bulletin.id,
                libelle=f"Remboursement avance {avance.id}",
                code=f"REMBOURS_{avance.id}",
                categorie="remboursement",
                type_element="retenue",
                montant=montant_remboursement,
                ordre_affichage=70
            )
            db.session.add(element_remboursement)
            
            # Créer l'enregistrement de remboursement
            remboursement = RemboursementAvance(
                avance_id=avance.id,
                bulletin_id=bulletin.id,
                montant=montant_remboursement,
                numero_echeance=1,  # À calculer selon l'historique
                date_remboursement=date.today()
            )
            db.session.add(remboursement)
            
            # Mettre à jour le solde de l'avance
            avance.montant_rembourse += montant_remboursement
            avance.solde_restant -= montant_remboursement
            
            if avance.solde_restant <= 0:
                avance.statut = 'rembourse'
            
            total_remboursements += montant_remboursement
        
        # Calculer les totaux finaux
        bulletin.total_cotisations_salariales = total_cotisations_salariales
        bulletin.total_cotisations_patronales = total_cotisations_patronales
        bulletin.salaire_imposable = salaire_imposable
        bulletin.impot_sur_salaire = impot_salaire
        bulletin.salaire_net = (bulletin.salaire_brut - total_cotisations_salariales - 
                               impot_salaire - bulletin.retenues_diverses - total_remboursements)
        
        # Calculer la provision pour congés payés
        bulletin.provision_conges_payes = bulletin.salaire_brut * (parametres.taux_conge_paye / 100)
        
        return True
        
    except Exception as e:
        print(f"Erreur calcul bulletin: {e}")
        return False

# ============= ROUTES API =============

@paie_bp.route('/api/paie/stats')
@login_required
@permission_requise('gestion_paie')
def api_stats_paie():
    """API pour récupérer les statistiques de paie"""
    try:
        periode = request.args.get('periode', 'mois')  # mois, trimestre, annee
        
        if periode == 'mois':
            date_debut = date.today().replace(day=1)
            date_fin = date_debut + relativedelta(months=1) - timedelta(days=1)
        elif periode == 'trimestre':
            today = date.today()
            trimestre = (today.month - 1) // 3 + 1
            date_debut = date(today.year, (trimestre - 1) * 3 + 1, 1)
            date_fin = date_debut + relativedelta(months=3) - timedelta(days=1)
        else:  # annee
            date_debut = date.today().replace(month=1, day=1)
            date_fin = date.today().replace(month=12, day=31)
        
        # Calculer les statistiques
        bulletins = BulletinPaie.query.filter(
            BulletinPaie.periode_debut >= date_debut,
            BulletinPaie.periode_fin <= date_fin
        ).all()
        
        stats = {
            'nombre_bulletins': len(bulletins),
            'masse_salariale': sum([b.salaire_brut for b in bulletins]),
            'salaire_net_total': sum([b.salaire_net for b in bulletins]),
            'cotisations_salariales': sum([b.total_cotisations_salariales for b in bulletins]),
            'cotisations_patronales': sum([b.total_cotisations_patronales for b in bulletins]),
            'impots_total': sum([b.impot_sur_salaire for b in bulletins]),
            'bulletin_valides': len([b for b in bulletins if b.valide]),
            'bulletins_payes': len([b for b in bulletins if b.statut == 'payé'])
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
