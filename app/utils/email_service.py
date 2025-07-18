"""
Module de gestion des notifications par email
Système d'envoi d'emails automatiques pour les alertes RH
"""

from flask import current_app
from flask_mail import Message
from app import db, mail
from app.models import Employee, Utilisateur, NotificationPresence, Conge, Absence, BulletinPaie
from datetime import datetime, date, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from threading import Thread

logger = logging.getLogger(__name__)

class EmailNotificationService:
    """Service de gestion des notifications par email"""
    
    def __init__(self):
        self.templates = {
            'retard': {
                'subject': 'Alerte Retard - {employee_name}',
                'template': 'retard_notification.html'
            },
            'absence': {
                'subject': 'Alerte Absence - {employee_name}',
                'template': 'absence_notification.html'
            },
            'demande_conge': {
                'subject': 'Nouvelle demande de congé - {employee_name}',
                'template': 'demande_conge_notification.html'
            },
            'conge_approuve': {
                'subject': 'Congé approuvé - {employee_name}',
                'template': 'conge_approuve_notification.html'
            },
            'conge_rejete': {
                'subject': 'Congé rejeté - {employee_name}',
                'template': 'conge_rejete_notification.html'
            },
            'bulletin_paie': {
                'subject': 'Bulletin de paie disponible - {month}/{year}',
                'template': 'bulletin_paie_notification.html'
            }
        }
    
    def send_async_email(self, app, msg):
        """Envoie un email de manière asynchrone"""
        with app.app_context():
            try:
                mail.send(msg)
                logger.info(f"Email envoyé avec succès à {msg.recipients}")
            except Exception as e:
                logger.error(f"Erreur envoi email: {e}")
    
    def send_email(self, subject, recipients, html_body, text_body=None):
        """Envoie un email avec gestion des erreurs"""
        try:
            msg = Message(
                subject=subject,
                recipients=recipients,
                html=html_body,
                body=text_body or html_body
            )
            
            # Envoi asynchrone
            from flask import current_app
            thread = Thread(target=self.send_async_email, args=(current_app._get_current_object(), msg))
            thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur création email: {e}")
            return False
    
    def get_manager_emails(self, employee_id):
        """Récupère les emails des managers d'un employé"""
        employee = Employee.query.get(employee_id)
        if not employee:
            return []
        
        emails = []
        
        # Manager direct
        if employee.manager_id:
            manager = Employee.query.get(employee.manager_id)
            if manager and manager.email:
                emails.append(manager.email)
        
        # Utilisateurs RH
        rh_users = Utilisateur.query.join(Utilisateur.role).filter(
            Utilisateur.role.has(nom='Manager RH')
        ).all()
        
        for user in rh_users:
            if user.email:
                emails.append(user.email)
        
        return list(set(emails))  # Supprimer les doublons
    
    def notify_attendance_issue(self, employee_id, issue_type, details):
        """Notifie les retards et absences"""
        employee = Employee.query.get(employee_id)
        if not employee:
            return False
        
        # Déterminer le template
        template_key = issue_type
        if template_key not in self.templates:
            return False
        
        template_info = self.templates[template_key]
        
        # Préparer les données
        context = {
            'employee': employee,
            'details': details,
            'date': details.get('date', date.today()),
            'company_name': 'RH Manager'
        }
        
        # Générer le contenu HTML
        html_body = self.generate_html_content(template_key, context)
        
        # Destinataires
        recipients = self.get_manager_emails(employee_id)
        
        # Envoyer l'email
        subject = template_info['subject'].format(employee_name=employee.nom)
        return self.send_email(subject, recipients, html_body)
    
    def notify_leave_request(self, demande_conge_id):
        """Notifie une nouvelle demande de congé"""
        demande = Conge.query.get(demande_conge_id)
        if not demande:
            return False
        
        context = {
            'demande': demande,
            'employee': demande.employe,
            'company_name': 'RH Manager'
        }
        
        html_body = self.generate_html_content('demande_conge', context)
        recipients = self.get_manager_emails(demande.employe_id)
        
        subject = f"Nouvelle demande de congé - {demande.employe.nom}"
        return self.send_email(subject, recipients, html_body)
    
    def notify_leave_decision(self, demande_conge_id, decision):
        """Notifie la décision sur une demande de congé"""
        demande = Conge.query.get(demande_conge_id)
        if not demande:
            return False
        
        template_key = 'conge_approuve' if decision == 'Approuvé' else 'conge_rejete'
        
        context = {
            'demande': demande,
            'employee': demande.employe,
            'decision': decision,
            'company_name': 'RH Manager'
        }
        
        html_body = self.generate_html_content(template_key, context)
        recipients = [demande.employe.email] if demande.employe.email else []
        
        subject = f"Congé {decision.lower()} - {demande.employe.nom}"
        return self.send_email(subject, recipients, html_body)
    
    def notify_payslip_available(self, bulletin_paie_id):
        """Notifie qu'un bulletin de paie est disponible"""
        bulletin = BulletinPaie.query.get(bulletin_paie_id)
        if not bulletin:
            return False
        
        context = {
            'bulletin': bulletin,
            'employee': bulletin.employe,
            'company_name': 'RH Manager'
        }
        
        html_body = self.generate_html_content('bulletin_paie', context)
        recipients = [bulletin.employe.email] if bulletin.employe.email else []
        
        subject = f"Bulletin de paie disponible - {bulletin.mois}/{bulletin.annee}"
        return self.send_email(subject, recipients, html_body)
    
    def generate_html_content(self, template_key, context):
        """Génère le contenu HTML pour un template donné"""
        # Templates HTML simples intégrés
        templates = {
            'retard': """
                <html>
                <body style="font-family: Arial, sans-serif; margin: 20px;">
                    <h2 style="color: #dc3545;">Alerte Retard</h2>
                    <p>Bonjour,</p>
                    <p>L'employé <strong>{employee_name}</strong> est arrivé en retard aujourd'hui.</p>
                    <ul>
                        <li>Date: {date}</li>
                        <li>Retard: {retard_minutes} minutes</li>
                        <li>Poste: {poste}</li>
                        <li>Département: {departement}</li>
                    </ul>
                    <p>Merci de prendre les mesures nécessaires.</p>
                    <p>Cordialement,<br>Système RH Manager</p>
                </body>
                </html>
            """,
            'absence': """
                <html>
                <body style="font-family: Arial, sans-serif; margin: 20px;">
                    <h2 style="color: #dc3545;">Alerte Absence</h2>
                    <p>Bonjour,</p>
                    <p>L'employé <strong>{employee_name}</strong> est absent aujourd'hui sans justification.</p>
                    <ul>
                        <li>Date: {date}</li>
                        <li>Poste: {poste}</li>
                        <li>Département: {departement}</li>
                    </ul>
                    <p>Merci de vérifier la situation.</p>
                    <p>Cordialement,<br>Système RH Manager</p>
                </body>
                </html>
            """,
            'demande_conge': """
                <html>
                <body style="font-family: Arial, sans-serif; margin: 20px;">
                    <h2 style="color: #0d6efd;">Nouvelle demande de congé</h2>
                    <p>Bonjour,</p>
                    <p>Une nouvelle demande de congé a été soumise par <strong>{employee_name}</strong>.</p>
                    <ul>
                        <li>Type: {type_conge}</li>
                        <li>Période: du {date_debut} au {date_fin}</li>
                        <li>Durée: {nombre_jours} jours</li>
                        <li>Motif: {motif}</li>
                    </ul>
                    <p>Merci de traiter cette demande dans les plus brefs délais.</p>
                    <p>Cordialement,<br>Système RH Manager</p>
                </body>
                </html>
            """,
            'conge_approuve': """
                <html>
                <body style="font-family: Arial, sans-serif; margin: 20px;">
                    <h2 style="color: #198754;">Congé approuvé</h2>
                    <p>Bonjour {employee_name},</p>
                    <p>Votre demande de congé a été <strong>approuvée</strong>.</p>
                    <ul>
                        <li>Type: {type_conge}</li>
                        <li>Période: du {date_debut} au {date_fin}</li>
                        <li>Durée: {nombre_jours} jours</li>
                    </ul>
                    <p>Bonnes vacances !</p>
                    <p>Cordialement,<br>Service RH</p>
                </body>
                </html>
            """,
            'conge_rejete': """
                <html>
                <body style="font-family: Arial, sans-serif; margin: 20px;">
                    <h2 style="color: #dc3545;">Congé rejeté</h2>
                    <p>Bonjour {employee_name},</p>
                    <p>Votre demande de congé a été <strong>rejetée</strong>.</p>
                    <ul>
                        <li>Type: {type_conge}</li>
                        <li>Période: du {date_debut} au {date_fin}</li>
                        <li>Durée: {nombre_jours} jours</li>
                    </ul>
                    <p>Merci de contacter le service RH pour plus d'informations.</p>
                    <p>Cordialement,<br>Service RH</p>
                </body>
                </html>
            """,
            'bulletin_paie': """
                <html>
                <body style="font-family: Arial, sans-serif; margin: 20px;">
                    <h2 style="color: #0d6efd;">Bulletin de paie disponible</h2>
                    <p>Bonjour {employee_name},</p>
                    <p>Votre bulletin de paie est disponible.</p>
                    <ul>
                        <li>Période: {mois}/{annee}</li>
                        <li>Salaire net: {salaire_net} FCFA</li>
                    </ul>
                    <p>Vous pouvez le consulter et le télécharger depuis votre espace personnel.</p>
                    <p>Cordialement,<br>Service RH</p>
                </body>
                </html>
            """
        }
        
        # Préparer les données pour le template
        template_data = {}
        
        if template_key in ['retard', 'absence']:
            employee = context.get('employee')
            details = context.get('details', {})
            template_data = {
                'employee_name': employee.nom if employee else 'Employé',
                'date': context.get('date', ''),
                'retard_minutes': details.get('retard_minutes', 0),
                'poste': employee.poste if employee else 'N/A',
                'departement': employee.departement if employee else 'N/A'
            }
        
        elif template_key in ['demande_conge', 'conge_approuve', 'conge_rejete']:
            employee = context.get('employee')
            demande = context.get('demande')
            template_data = {
                'employee_name': employee.nom if employee else 'Employé',
                'type_conge': demande.type_conge if demande else 'N/A',
                'date_debut': demande.date_debut if demande else '',
                'date_fin': demande.date_fin if demande else '',
                'nombre_jours': demande.nombre_jours if demande else 0,
                'motif': demande.motif if demande else 'N/A'
            }
        
        elif template_key == 'bulletin_paie':
            employee = context.get('employee')
            bulletin = context.get('bulletin')
            template_data = {
                'employee_name': employee.nom if employee else 'Employé',
                'mois': bulletin.mois if bulletin else '',
                'annee': bulletin.annee if bulletin else '',
                'salaire_net': bulletin.salaire_net if bulletin else 0
            }
        
        template = templates.get(template_key, "")
        return template.format(**template_data)
    
    def send_daily_summary(self):
        """Envoie un résumé quotidien aux managers"""
        today = date.today()
        
        # Récupérer les statistiques du jour
        retards = NotificationPresence.query.filter(
            NotificationPresence.type_notification == 'retard',
            NotificationPresence.date_reference == today
        ).count()
        
        absences = NotificationPresence.query.filter(
            NotificationPresence.type_notification == 'absence',
            NotificationPresence.date_reference == today
        ).count()
        
        demandes_conge = Conge.query.filter(
            Conge.date_demande >= today,
            Conge.statut == 'En attente'
        ).count()
        
        # Générer le résumé
        html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px;">
                <h2 style="color: #0d6efd;">Résumé quotidien RH - {today.strftime('%d/%m/%Y')}</h2>
                <h3>Statistiques du jour</h3>
                <ul>
                    <li>Retards: {retards}</li>
                    <li>Absences: {absences}</li>
                    <li>Demandes de congé en attente: {demandes_conge}</li>
                </ul>
                <p>Merci de traiter les demandes en attente.</p>
                <p>Cordialement,<br>Système RH Manager</p>
            </body>
            </html>
        """
        
        # Envoyer aux managers RH
        rh_users = Utilisateur.query.join(Utilisateur.role).filter(
            Utilisateur.role.has(nom='Manager RH')
        ).all()
        
        recipients = [user.email for user in rh_users if user.email]
        
        if recipients:
            subject = f"Résumé quotidien RH - {today.strftime('%d/%m/%Y')}"
            return self.send_email(subject, recipients, html_body)
        
        return False

# Instance globale du service
email_service = EmailNotificationService()
