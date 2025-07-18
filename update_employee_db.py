#!/usr/bin/env python3
"""
Script pour mettre à jour la base de données avec les nouveaux champs du module employés
"""

import os
import sys
from datetime import datetime

# Ajouter le chemin du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Employee, EmployeeHistory, EmployeeDocument, Utilisateur
from sqlalchemy import text, inspect

def update_database():
    """Met à jour la base de données avec les nouveaux champs"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Mise à jour de la base de données...")
            
            # Créer toutes les tables
            db.create_all()
            print("✅ Tables créées/mises à jour")
            
            # Vérifier les colonnes existantes dans la table Employee
            inspector = inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('employee')]
            print(f"📋 Colonnes existantes dans Employee: {len(existing_columns)}")
            
            # Liste des nouvelles colonnes à ajouter
            new_columns = {
                'nom_complet': 'VARCHAR(200)',
                'date_naissance': 'DATE',
                'lieu_naissance': 'VARCHAR(100)',
                'sexe': 'VARCHAR(1)',
                'nationalite': 'VARCHAR(50)',
                'situation_matrimoniale': 'VARCHAR(20)',
                'nombre_enfants': 'INTEGER DEFAULT 0',
                'telephone_urgence': 'VARCHAR(20)',
                'adresse': 'TEXT',
                'ville': 'VARCHAR(100)',
                'manager_id': 'INTEGER',
                'date_fin_contrat': 'DATE',
                'salaire_base': 'DECIMAL(12,2)',
                'numero_cni': 'VARCHAR(50)',
                'numero_cnps': 'VARCHAR(50)',
                'numero_crtv': 'VARCHAR(50)',
                'numero_compte_bancaire': 'VARCHAR(50)',
                'banque': 'VARCHAR(100)',
                'photo_profil': 'VARCHAR(255)',
                'cv_file': 'VARCHAR(255)',
                'contrat_file': 'VARCHAR(255)',
                'cree_par': 'INTEGER',
                'modifie_par': 'INTEGER',
                'date_creation': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                'date_modification': 'DATETIME'
            }
            
            # Ajouter les colonnes manquantes
            columns_added = 0
            for column_name, column_type in new_columns.items():
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE employee ADD COLUMN {column_name} {column_type}"
                        db.session.execute(text(sql))
                        db.session.commit()
                        print(f"✅ Colonne '{column_name}' ajoutée")
                        columns_added += 1
                    except Exception as e:
                        print(f"⚠️  Erreur lors de l'ajout de la colonne '{column_name}': {e}")
                        db.session.rollback()
            
            if columns_added == 0:
                print("ℹ️  Toutes les colonnes sont déjà présentes")
            
            # Mettre à jour les employés existants avec nom_complet
            existing_employees = Employee.query.filter(Employee.nom_complet.is_(None)).all()
            if existing_employees:
                print(f"🔄 Mise à jour de {len(existing_employees)} employés existants...")
                for emp in existing_employees:
                    if emp.nom:
                        emp.nom_complet = f"{emp.nom} {emp.prenom or ''}".strip()
                        if not emp.date_creation:
                            emp.date_creation = datetime.now()
                
                db.session.commit()
                print("✅ Employés existants mis à jour")
            
            # Vérifier la table EmployeeHistory
            if 'employee_history' not in inspector.get_table_names():
                print("🔄 Création de la table employee_history...")
                EmployeeHistory.__table__.create(db.engine)
                print("✅ Table employee_history créée")
            
            # Vérifier la table EmployeeDocument
            if 'employee_document' not in inspector.get_table_names():
                print("🔄 Création de la table employee_document...")
                EmployeeDocument.__table__.create(db.engine)
                print("✅ Table employee_document créée")
            
            # Créer les dossiers de stockage des fichiers
            upload_dirs = [
                'app/static/uploads/employees/photos',
                'app/static/uploads/employees/cv',
                'app/static/uploads/employees/contrats',
                'app/static/uploads/employees/documents'
            ]
            
            for upload_dir in upload_dirs:
                os.makedirs(upload_dir, exist_ok=True)
                print(f"✅ Dossier '{upload_dir}' créé/vérifié")
            
            print("\n✅ Mise à jour de la base de données terminée avec succès!")
            print("\n📊 Statistiques:")
            print(f"   - Employés: {Employee.query.count()}")
            print(f"   - Documents: {EmployeeDocument.query.count()}")
            print(f"   - Historique: {EmployeeHistory.query.count()}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    update_database()
