"""
Commandes CLI pour les tâches automatisées
"""

import click
from flask.cli import with_appcontext
from app.utils.email_service import email_service
from app.models import NotificationPresence, Conge, BulletinPaie, Employee
from app import db
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

@click.command()
@with_appcontext
def send_daily_summary():
    """Envoie le résumé quotidien par email"""
    try:
        result = email_service.send_daily_summary()
        if result:
            click.echo("Résumé quotidien envoyé avec succès")
        else:
            click.echo("Aucun destinataire trouvé ou erreur d'envoi")
    except Exception as e:
        click.echo(f"Erreur lors de l'envoi du résumé: {e}")

@click.command()
@with_appcontext
def send_overdue_reminders():
    """Envoie des rappels pour les demandes en retard"""
    try:
        today = date.today()
        overdue_date = today - timedelta(days=3)
        
        # Demandes de congé en attente depuis plus de 3 jours
        overdue_requests = Conge.query.filter(
            Conge.statut == 'En attente',
            Conge.date_demande < overdue_date
        ).all()
        
        if overdue_requests:
            # Envoyer rappel
            rh_users = Employee.query.filter_by(poste='Manager RH').all()
            emails = [u.email for u in rh_users if u.email]
            
            if emails:
                html_body = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; margin: 20px;">
                        <h2 style="color: #dc3545;">Rappel - Demandes en retard</h2>
                        <p>Bonjour,</p>
                        <p>Il y a {len(overdue_requests)} demandes de congé en attente depuis plus de 3 jours.</p>
                        <p>Merci de traiter ces demandes rapidement.</p>
                        <p>Cordialement,<br>Système RH Manager</p>
                    </body>
                    </html>
                """
                
                email_service.send_email(
                    "Rappel - Demandes de congé en retard",
                    emails,
                    html_body
                )
                
                click.echo(f"Rappel envoyé pour {len(overdue_requests)} demandes en retard")
        else:
            click.echo("Aucune demande en retard")
            
    except Exception as e:
        click.echo(f"Erreur lors de l'envoi des rappels: {e}")

@click.command()
@with_appcontext
def cleanup_old_notifications():
    """Nettoie les anciennes notifications"""
    try:
        cutoff_date = date.today() - timedelta(days=30)
        
        # Supprimer les notifications de plus de 30 jours
        old_notifications = NotificationPresence.query.filter(
            NotificationPresence.date_reference < cutoff_date
        ).all()
        
        count = len(old_notifications)
        for notification in old_notifications:
            db.session.delete(notification)
        
        db.session.commit()
        click.echo(f"Supprimé {count} anciennes notifications")
        
    except Exception as e:
        click.echo(f"Erreur lors du nettoyage: {e}")

def register_commands(app):
    """Enregistre les commandes CLI"""
    app.cli.add_command(send_daily_summary)
    app.cli.add_command(send_overdue_reminders)
    app.cli.add_command(cleanup_old_notifications)
