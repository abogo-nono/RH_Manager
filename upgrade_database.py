#!/usr/bin/env python3
"""
Script pour mettre à jour la base de données avec les nouveaux champs et tables.
"""

from app import create_app, db
from sqlalchemy import text
import os

def upgrade_database():
    app = create_app()
    
    with app.app_context():
        try:
            print("Début de la mise à jour de la base de données...")
            
            # Créer les nouvelles tables
            print("Création des nouvelles tables...")
            
            # Table employee_history
            with db.engine.begin() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS employee_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        action VARCHAR(50) NOT NULL,
                        champ_modifie VARCHAR(100),
                        ancienne_valeur TEXT,
                        nouvelle_valeur TEXT,
                        date_modification DATETIME DEFAULT CURRENT_TIMESTAMP,
                        commentaire TEXT,
                        FOREIGN KEY (employee_id) REFERENCES employee(id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES utilisateur(id)
                    )
                """))
                
                # Table employee_document
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS employee_document (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id INTEGER NOT NULL,
                        nom_document VARCHAR(100) NOT NULL,
                        type_document VARCHAR(50) NOT NULL,
                        nom_fichier VARCHAR(200) NOT NULL,
                        chemin_fichier VARCHAR(200) NOT NULL,
                        taille_fichier INTEGER,
                        date_upload DATETIME DEFAULT CURRENT_TIMESTAMP,
                        uploade_par INTEGER,
                        FOREIGN KEY (employee_id) REFERENCES employee(id) ON DELETE CASCADE,
                        FOREIGN KEY (uploade_par) REFERENCES utilisateur(id)
                    )
                """))
            
            print("Tables créées avec succès.")
            
            # Ajouter les nouvelles colonnes à la table employee
            print("Ajout des nouvelles colonnes à la table employee...")
            
            new_columns = [
                ("prenom", "VARCHAR(100)"),
                ("nom_complet", "VARCHAR(200)"),
                ("date_naissance", "DATE"),
                ("lieu_naissance", "VARCHAR(100)"),
                ("sexe", "VARCHAR(10)"),
                ("nationalite", "VARCHAR(50)"),
                ("situation_matrimoniale", "VARCHAR(50)"),
                ("nombre_enfants", "INTEGER DEFAULT 0"),
                ("telephone_urgence", "VARCHAR(20)"),
                ("adresse", "TEXT"),
                ("ville", "VARCHAR(50)"),
                ("manager_id", "INTEGER"),
                ("date_fin_contrat", "DATE"),
                ("salaire_base", "REAL"),
                ("numero_cni", "VARCHAR(20)"),
                ("numero_cnps", "VARCHAR(20)"),
                ("numero_crtv", "VARCHAR(20)"),
                ("numero_compte_bancaire", "VARCHAR(30)"),
                ("banque", "VARCHAR(50)"),
                ("photo_profil", "VARCHAR(200)"),
                ("cv_file", "VARCHAR(200)"),
                ("contrat_file", "VARCHAR(200)"),
                ("date_creation", "DATETIME"),
                ("date_modification", "DATETIME"),
                ("cree_par", "INTEGER"),
                ("modifie_par", "INTEGER")
            ]
            
            # Vérifier quelles colonnes existent déjà
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('employee')]
            
            with db.engine.begin() as conn:
                for column_name, column_type in new_columns:
                    if column_name not in existing_columns:
                        try:
                            conn.execute(text(f"ALTER TABLE employee ADD COLUMN {column_name} {column_type}"))
                            print(f"  Colonne {column_name} ajoutée.")
                        except Exception as e:
                            print(f"  Erreur lors de l'ajout de {column_name}: {e}")
                    else:
                        print(f"  Colonne {column_name} existe déjà.")
                
                # Mettre à jour le nom_complet pour les employés existants
                print("Mise à jour du nom_complet pour les employés existants...")
                conn.execute(text("""
                    UPDATE employee 
                    SET nom_complet = nom || COALESCE(' ' || prenom, '')
                    WHERE nom_complet IS NULL OR nom_complet = ''
                """))
                
                # Mettre à jour les dates de création pour les employés existants (seulement si la colonne existe)
                try:
                    print("Mise à jour des dates de création pour les employés existants...")
                    conn.execute(text("""
                        UPDATE employee 
                        SET date_creation = CURRENT_TIMESTAMP
                        WHERE date_creation IS NULL
                    """))
                except Exception as e:
                    print(f"  Note: {e} - colonne date_creation non disponible")
            
            print("Base de données mise à jour avec succès!")
            
            # Créer les dossiers nécessaires pour les uploads
            print("Création des dossiers d'upload...")
            upload_dirs = [
                'app/static/uploads/employees/photos',
                'app/static/uploads/employees/cv',
                'app/static/uploads/employees/contrats',
                'app/static/uploads/employees/documents'
            ]
            
            for dir_path in upload_dirs:
                os.makedirs(dir_path, exist_ok=True)
                print(f"  Dossier créé: {dir_path}")
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour: {e}")
            raise

if __name__ == '__main__':
    upgrade_database()
