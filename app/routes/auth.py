from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from app.models import Utilisateur
from app.forms import ResetPasswordRequestForm, ResetPasswordForm, ChangePasswordForm
from app import db, mail
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_name = request.form['nom_utilisateur']
        mot_de_passe = request.form['mot_de_passe']
        user = Utilisateur.query.filter_by(nom_utilisateur=user_name).first()

        # Vérifications de sécurité
        if not user:
            flash("Pseudo ou mot de passe incorrect", "danger")
            return render_template('auth/login.html')
        
        # Vérifier si le compte est verrouillé
        if user.is_account_locked():
            flash("Votre compte est temporairement verrouillé suite à trop de tentatives de connexion. Réessayez plus tard.", "warning")
            return render_template('auth/login.html')
        
        # Vérifier le mot de passe
        if not user.check_password(mot_de_passe):
            user.increment_failed_login()
            db.session.commit()
            flash("Pseudo ou mot de passe incorrect", "danger")
            return render_template('auth/login.html')
            
        if not user.actif:
            flash("Votre compte est inactif. Veuillez contacter l'administrateur.", "warning")
            return render_template('auth/login.html')
        
        # Connexion réussie
        user.reset_failed_login()
        db.session.commit()
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard.dashboard'))
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté avec succès.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """Demande de réinitialisation de mot de passe"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Utilisateur.query.filter_by(email=form.email.data).first()
        if user:
            # Générer le token de réinitialisation
            token = user.generate_reset_token()
            db.session.commit()
            
            # Envoyer l'email
            send_password_reset_email(user, token)
            flash('Un email avec les instructions de réinitialisation vous a été envoyé.', 'info')
        else:
            flash('Cette adresse email n\'est pas enregistrée.', 'warning')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Réinitialisation du mot de passe avec token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    # Trouver l'utilisateur avec ce token
    user = Utilisateur.query.filter_by(reset_token=token).first()
    if not user or not user.verify_reset_token(token):
        flash('Le lien de réinitialisation est invalide ou a expiré.', 'warning')
        return redirect(url_for('auth.reset_password_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        user.reset_failed_login()  # Débloquer le compte si nécessaire
        db.session.commit()
        flash('Votre mot de passe a été réinitialisé avec succès.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Changer son mot de passe (utilisateur connecté)"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Mot de passe actuel incorrect.', 'danger')
            return render_template('auth/change_password.html', form=form)
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Votre mot de passe a été changé avec succès.', 'success')
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('auth/change_password.html', form=form)

def send_password_reset_email(user, token):
    """Envoie l'email de réinitialisation de mot de passe"""
    try:
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        msg = Message(
            subject='[RH Manager] Réinitialisation de votre mot de passe',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        
        msg.body = f"""Bonjour {user.nom_complet or user.nom_utilisateur},

Une demande de réinitialisation de mot de passe a été effectuée pour votre compte RH Manager.

Si vous êtes à l'origine de cette demande, cliquez sur le lien suivant pour réinitialiser votre mot de passe :

{reset_url}

Ce lien est valide pendant 1 heure.

Si vous n'avez pas demandé cette réinitialisation, vous pouvez ignorer cet email.

Cordialement,
L'équipe RH Manager
"""
        
        msg.html = f"""
        <h2>Réinitialisation de mot de passe</h2>
        <p>Bonjour <strong>{user.nom_complet or user.nom_utilisateur}</strong>,</p>
        
        <p>Une demande de réinitialisation de mot de passe a été effectuée pour votre compte RH Manager.</p>
        
        <p>Si vous êtes à l'origine de cette demande, cliquez sur le bouton suivant pour réinitialiser votre mot de passe :</p>
        
        <p style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                Réinitialiser mon mot de passe
            </a>
        </p>
        
        <p><small>Ce lien est valide pendant 1 heure.</small></p>
        
        <p>Si vous n'avez pas demandé cette réinitialisation, vous pouvez ignorer cet email.</p>
        
        <hr>
        <p><small>Cordialement,<br>L'équipe RH Manager</small></p>
        """
        
        mail.send(msg)
        
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")
        # En production, utiliser un système de logging approprié
