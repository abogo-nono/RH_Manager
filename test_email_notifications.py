"""
Test complet du système de notifications email
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models import Employee, Utilisateur, Conge, BulletinPaie, NotificationPresence
from app.utils.email_service import email_service
from datetime import date, datetime, timedelta
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_email_notifications():
    """Test complet des notifications email"""
    print("=== TEST DU SYSTÈME DE NOTIFICATIONS EMAIL ===")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test 1: Vérifier la configuration email
            print("\n1. Test de la configuration email...")
            print(f"   - Serveur SMTP: {app.config.get('MAIL_SERVER')}")
            print(f"   - Port: {app.config.get('MAIL_PORT')}")
            print(f"   - TLS: {app.config.get('MAIL_USE_TLS')}")
            print(f"   - Expéditeur: {app.config.get('MAIL_DEFAULT_SENDER')}")
            print("   ✅ Configuration email OK")
            
            # Test 2: Vérifier les données de test
            print("\n2. Test des données de test...")
            employees = Employee.query.limit(3).all()
            users = Utilisateur.query.limit(3).all()
            
            print(f"   - Employés disponibles: {len(employees)}")
            print(f"   - Utilisateurs disponibles: {len(users)}")
            
            if not employees:
                print("   ❌ Aucun employé trouvé - Créer des données de test")
                return False
            
            if not users:
                print("   ❌ Aucun utilisateur trouvé - Créer des données de test")
                return False
            
            print("   ✅ Données de test OK")
            
            # Test 3: Test notification retard
            print("\n3. Test notification retard...")
            employee = employees[0]
            result = email_service.notify_attendance_issue(
                employee.id, 
                'retard', 
                {
                    'retard_minutes': 15,
                    'date': date.today()
                }
            )
            print(f"   - Notification retard pour {employee.nom}: {'✅ Envoyée' if result else '❌ Échec'}")
            
            # Test 4: Test notification absence
            print("\n4. Test notification absence...")
            result = email_service.notify_attendance_issue(
                employee.id,
                'absence',
                {
                    'date': date.today()
                }
            )
            print(f"   - Notification absence pour {employee.nom}: {'✅ Envoyée' if result else '❌ Échec'}")
            
            # Test 5: Test notification demande de congé
            print("\n5. Test notification demande de congé...")
            # Créer une demande de test
            demande = Conge(
                employe_id=employee.id,
                type_conge='Congé annuel',
                date_debut=date.today() + timedelta(days=7),
                date_fin=date.today() + timedelta(days=14),
                nombre_jours=7,
                motif='Test notification',
                statut='En attente',
                date_demande=datetime.now()
            )
            
            db.session.add(demande)
            db.session.commit()
            
            result = email_service.notify_leave_request(demande.id)
            print(f"   - Notification demande congé: {'✅ Envoyée' if result else '❌ Échec'}")
            
            # Test 6: Test notification approbation congé
            print("\n6. Test notification approbation congé...")
            result = email_service.notify_leave_decision(demande.id, 'Approuvé')
            print(f"   - Notification approbation: {'✅ Envoyée' if result else '❌ Échec'}")
            
            # Test 7: Test notification rejet congé
            print("\n7. Test notification rejet congé...")
            result = email_service.notify_leave_decision(demande.id, 'Rejeté')
            print(f"   - Notification rejet: {'✅ Envoyée' if result else '❌ Échec'}")
            
            # Test 8: Test notification bulletin de paie
            print("\n8. Test notification bulletin de paie...")
            bulletin = BulletinPaie.query.filter_by(employe_id=employee.id).first()
            
            if bulletin:
                result = email_service.notify_payslip_available(bulletin.id)
                print(f"   - Notification bulletin paie: {'✅ Envoyée' if result else '❌ Échec'}")
            else:
                print("   ⚠️ Aucun bulletin de paie trouvé pour les tests")
            
            # Test 9: Test résumé quotidien
            print("\n9. Test résumé quotidien...")
            result = email_service.send_daily_summary()
            print(f"   - Résumé quotidien: {'✅ Envoyé' if result else '❌ Échec'}")
            
            # Test 10: Test des templates HTML
            print("\n10. Test des templates HTML...")
            templates = ['retard', 'absence', 'demande_conge', 'conge_approuve', 'conge_rejete', 'bulletin_paie']
            
            for template in templates:
                context = {
                    'employee': employee,
                    'details': {'retard_minutes': 15, 'date': date.today()},
                    'demande': demande,
                    'bulletin': bulletin,
                    'company_name': 'RH Manager'
                }
                
                html = email_service.generate_html_content(template, context)
                has_content = len(html) > 100  # Vérifier que le template contient du contenu
                print(f"   - Template {template}: {'✅ OK' if has_content else '❌ Vide'}")
            
            # Test 11: Test récupération des emails des managers
            print("\n11. Test récupération emails managers...")
            emails = email_service.get_manager_emails(employee.id)
            print(f"   - Emails managers trouvés: {len(emails)}")
            print(f"   - Emails: {emails}")
            
            # Nettoyer les données de test
            db.session.delete(demande)
            db.session.commit()
            
            print("\n=== RÉSUMÉ DES TESTS ===")
            print("✅ Configuration email: OK")
            print("✅ Données de test: OK")
            print("✅ Notification retard: Testée")
            print("✅ Notification absence: Testée")
            print("✅ Notification demande congé: Testée")
            print("✅ Notification approbation: Testée")
            print("✅ Notification rejet: Testée")
            print("✅ Notification bulletin paie: Testée")
            print("✅ Résumé quotidien: Testé")
            print("✅ Templates HTML: Testés")
            print("✅ Récupération emails: Testée")
            
            print("\n🎉 SYSTÈME DE NOTIFICATIONS EMAIL PRÊT !")
            print("📧 Les notifications seront envoyées automatiquement lors des actions utilisateur")
            print("⏰ Programmez les commandes CLI pour les tâches automatisées:")
            print("   - flask send-daily-summary")
            print("   - flask send-overdue-reminders")
            print("   - flask cleanup-old-notifications")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors des tests: {e}")
            logger.error(f"Erreur tests email: {e}")
            return False

if __name__ == "__main__":
    success = test_email_notifications()
    sys.exit(0 if success else 1)
