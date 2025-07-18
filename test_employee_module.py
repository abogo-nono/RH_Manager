#!/usr/bin/env python3
"""
Script de test pour le module Gestion des Employés
"""

import os
import sys
from datetime import datetime, date

# Ajouter le chemin du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Employee, EmployeeHistory, EmployeeDocument, Utilisateur

def test_employee_module():
    """Test complet du module employés"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Test du module Gestion des Employés\n")
        
        # Test 1: Création d'un employé complet
        print("1️⃣ Test de création d'un employé...")
        try:
            # Vérifier qu'il y a au moins un utilisateur pour les tests
            user = Utilisateur.query.first()
            if not user:
                print("❌ Aucun utilisateur trouvé. Créer d'abord un utilisateur.")
                return
            
            # Créer un employé de test
            employe_test = Employee(
                nom="DUPONT",
                prenom="Jean",
                nom_complet="DUPONT Jean",
                date_naissance=date(1985, 5, 15),
                lieu_naissance="Douala",
                sexe="M",
                nationalite="Camerounaise",
                situation_matrimoniale="Marié(e)",
                nombre_enfants=2,
                email="jean.dupont@test.com",
                telephone="+237 690 123 456",
                telephone_urgence="+237 690 654 321",
                adresse="Quartier Bonanjo, Rue de la République",
                ville="Douala",
                poste="Développeur Senior",
                departement="IT",
                type_contrat="CDI",
                date_embauche=date(2020, 1, 15),
                salaire_base=750000,
                statut="Actif",
                numero_cni="123456789",
                numero_cnps="CNP123456",
                numero_crtv="CRT789",
                numero_compte_bancaire="12345678901234567890",
                banque="UBA Cameroun",
                cree_par=user.id,
                date_creation=datetime.now()
            )
            
            db.session.add(employe_test)
            db.session.commit()
            print(f"✅ Employé créé avec ID: {employe_test.id}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création: {e}")
            db.session.rollback()
            return
        
        # Test 2: Test de l'historique
        print("\n2️⃣ Test de l'historique...")
        try:
            # Créer une entrée d'historique
            history_entry = EmployeeHistory(
                employee_id=employe_test.id,
                user_id=user.id,
                action='CREATE',
                champ_modifie='Création employé',
                nouvelle_valeur=employe_test.nom_complet,
                commentaire='Employé créé pour les tests'
            )
            
            db.session.add(history_entry)
            db.session.commit()
            print(f"✅ Entrée d'historique créée avec ID: {history_entry.id}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de l'historique: {e}")
            db.session.rollback()
        
        # Test 3: Test des documents
        print("\n3️⃣ Test des documents...")
        try:
            # Créer un document de test
            document_test = EmployeeDocument(
                employee_id=employe_test.id,
                nom_document="CV Jean DUPONT",
                type_document="CV",
                nom_fichier="cv_jean_dupont.pdf",
                chemin_fichier="test_cv_jean_dupont.pdf",
                taille_fichier=1024000,  # 1 MB
                uploade_par=user.id
            )
            
            db.session.add(document_test)
            db.session.commit()
            print(f"✅ Document créé avec ID: {document_test.id}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création du document: {e}")
            db.session.rollback()
        
        # Test 4: Test des relations
        print("\n4️⃣ Test des relations...")
        try:
            # Vérifier les relations
            employe = Employee.query.get(employe_test.id)
            
            print(f"   - Employé: {employe.nom_complet}")
            print(f"   - Âge: {employe.age} ans")
            print(f"   - Ancienneté: {employe.anciennete_annees} ans")
            print(f"   - Documents: {len(employe.documents)}")
            print(f"   - Historique: {len(employe.historique)}")
            
            if employe.documents:
                doc = employe.documents[0]
                print(f"   - Premier document: {doc.nom_document} ({doc.type_document})")
                print(f"   - Uploadé par: {doc.uploader.nom_complet if doc.uploader else 'Inconnu'}")
            
            if employe.historique:
                hist = employe.historique[0]
                print(f"   - Première entrée historique: {hist.action} - {hist.champ_modifie}")
                print(f"   - Par: {hist.user.nom_complet if hist.user else 'Inconnu'}")
            
            print("✅ Relations vérifiées avec succès")
            
        except Exception as e:
            print(f"❌ Erreur lors de la vérification des relations: {e}")
        
        # Test 5: Test des propriétés calculées
        print("\n5️⃣ Test des propriétés calculées...")
        try:
            employe = Employee.query.get(employe_test.id)
            
            print(f"   - Age: {employe.age} ans")
            print(f"   - Ancienneté: {employe.anciennete_annees} ans") 
            print(f"   - Ancienneté (jours): {employe.anciennete_jours} jours")
            
            # Test avec un manager
            manager = Employee.query.filter(Employee.id != employe.id).first()
            if manager:
                employe.manager_id = manager.id
                db.session.commit()
                print(f"   - Manager assigné: {employe.manager.nom_complet}")
            
            print("✅ Propriétés calculées vérifiées")
            
        except Exception as e:
            print(f"❌ Erreur lors du test des propriétés: {e}")
        
        # Test 6: Test de modification avec historique
        print("\n6️⃣ Test de modification avec historique...")
        try:
            employe = Employee.query.get(employe_test.id)
            
            # Modifier quelques champs
            ancien_poste = employe.poste
            employe.poste = "Lead Developer"
            employe.salaire_base = 850000
            employe.modifie_par = user.id
            employe.date_modification = datetime.now()
            
            # Ajouter l'historique de modification
            hist_modification = EmployeeHistory(
                employee_id=employe.id,
                user_id=user.id,
                action='UPDATE',
                champ_modifie='poste',
                ancienne_valeur=ancien_poste,
                nouvelle_valeur=employe.poste,
                commentaire='Promotion suite à évaluation'
            )
            
            db.session.add(hist_modification)
            db.session.commit()
            
            print(f"✅ Employé modifié: {ancien_poste} → {employe.poste}")
            print(f"✅ Historique de modification enregistré")
            
        except Exception as e:
            print(f"❌ Erreur lors de la modification: {e}")
            db.session.rollback()
        
        # Statistiques finales
        print("\n📊 Statistiques finales:")
        print(f"   - Total employés: {Employee.query.count()}")
        print(f"   - Total documents: {EmployeeDocument.query.count()}")
        print(f"   - Total historique: {EmployeeHistory.query.count()}")
        print(f"   - Employés actifs: {Employee.query.filter_by(statut='Actif').count()}")
        
        # Afficher quelques employés
        print("\n👥 Employés dans la base:")
        employes = Employee.query.limit(5).all()
        for emp in employes:
            print(f"   - {emp.nom_complet} ({emp.poste}) - {emp.statut}")
        
        print("\n✅ Tests du module employés terminés avec succès!")

if __name__ == "__main__":
    test_employee_module()
