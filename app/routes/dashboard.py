from flask import Blueprint, render_template, request, jsonify, send_file
from app.models import Employee, Absence, Conge, BulletinPaie, Evaluation, Presence, AvanceSalaire, HeuresTravail
from app import db
from datetime import date, datetime, timedelta
from flask_login import login_required, current_user
from sqlalchemy import func, extract, desc
from collections import defaultdict
import json
import io
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import base64
from app.utils.permissions import permission_requise

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal avec métriques importantes"""
    
    # Métriques de base
    total_employes = Employee.query.filter_by(statut='Actif').count()
    
    today = date.today()
    
    # Absences en cours (absences d'aujourd'hui)
    absences_en_cours = Absence.query.filter_by(date_absence=today).count()
    
    # Congés en cours
    conges_en_cours = Conge.query.filter(
        Conge.date_debut <= today,
        Conge.date_fin >= today,
        Conge.statut == 'Approuvé'
    ).count()
    
    # Jours de congés restants (approximation)
    jours_conges_restants = db.session.query(func.sum(Employee.nombre_enfants * 21)).scalar() or 0
    
    # Dernier recrutement
    dernier_recrutement = Employee.query.order_by(Employee.date_embauche.desc()).first()
    
    # Statistiques mensuelles
    current_month = today.month
    current_year = today.year
    
    # Nouvelles embauches ce mois
    nouvelles_embauches = Employee.query.filter(
        extract('month', Employee.date_embauche) == current_month,
        extract('year', Employee.date_embauche) == current_year
    ).count()
    
    # Congés en attente
    conges_en_attente = Conge.query.filter_by(statut='En attente').count()
    
    # Absences non justifiées
    absences_non_justifiees = Absence.query.filter_by(etat='Non justifiée').count()
    
    # Bulletins de paie à traiter
    bulletins_brouillon = BulletinPaie.query.filter_by(statut='brouillon').count()
    
    # Évaluations en retard
    evaluations_retard = Evaluation.query.filter(
        Evaluation.date_evaluation < today,
        Evaluation.statut.in_(['brouillon', 'en_cours'])
    ).count()
    
    # Graphiques de données
    charts_data = generate_dashboard_charts()
    
    return render_template('dashboard.html', 
                         total_employes=total_employes,
                         absences_en_cours=absences_en_cours,
                         conges_en_cours=conges_en_cours,
                         jours_conges_restants=jours_conges_restants,
                         dernier_recrutement=dernier_recrutement,
                         nouvelles_embauches=nouvelles_embauches,
                         conges_en_attente=conges_en_attente,
                         absences_non_justifiees=absences_non_justifiees,
                         bulletins_brouillon=bulletins_brouillon,
                         evaluations_retard=evaluations_retard,
                         charts_data=charts_data)

@dashboard_bp.route('/api/dashboard/stats')
@login_required
def dashboard_stats_api():
    """API pour les statistiques du dashboard"""
    
    today = date.today()
    
    # Statistiques par département
    stats_departement = db.session.query(
        Employee.departement,
        func.count(Employee.id).label('count')
    ).filter_by(statut='Actif').group_by(Employee.departement).all()
    
    # Évolution des embauches sur les 12 derniers mois
    embauches_mois = []
    for i in range(12):
        month_date = today - timedelta(days=30*i)
        count = Employee.query.filter(
            extract('month', Employee.date_embauche) == month_date.month,
            extract('year', Employee.date_embauche) == month_date.year
        ).count()
        embauches_mois.append({
            'month': month_date.strftime('%B %Y'),
            'count': count
        })
    
    # Statistiques des congés par type
    conges_type = db.session.query(
        Conge.type_conge,
        func.count(Conge.id).label('count')
    ).filter_by(statut='Approuvé').group_by(Conge.type_conge).all()
    
    return jsonify({
        'departements': [{'name': dept[0], 'count': dept[1]} for dept in stats_departement],
        'embauches_mois': embauches_mois,
        'conges_type': [{'type': conge[0], 'count': conge[1]} for conge in conges_type]
    })

@dashboard_bp.route('/dashboard/reports')
@login_required
@permission_requise('rapports')
def reports_dashboard():
    """Dashboard des rapports"""
    
    # Rapports disponibles
    rapports = [
        {
            'id': 'employes',
            'title': 'Rapport Employés',
            'description': 'Liste complète des employés avec leurs informations',
            'icon': 'bi-people',
            'formats': ['PDF', 'Excel', 'CSV']
        },
        {
            'id': 'conges',
            'title': 'Rapport Congés',
            'description': 'Suivi des congés par période et employé',
            'icon': 'bi-calendar-check',
            'formats': ['PDF', 'Excel']
        },
        {
            'id': 'absences',
            'title': 'Rapport Absences',
            'description': 'Analyse des absences et leur impact',
            'icon': 'bi-calendar-x',
            'formats': ['PDF', 'Excel']
        },
        {
            'id': 'paie',
            'title': 'Rapport Paie',
            'description': 'Bulletins de paie et analyses salariales',
            'icon': 'bi-cash',
            'formats': ['PDF', 'Excel']
        },
        {
            'id': 'evaluations',
            'title': 'Rapport Évaluations',
            'description': 'Performances et évaluations des employés',
            'icon': 'bi-graph-up',
            'formats': ['PDF', 'Excel']
        },
        {
            'id': 'presences',
            'title': 'Rapport Présences',
            'description': 'Suivi des présences et pointages',
            'icon': 'bi-clock',
            'formats': ['PDF', 'Excel']
        }
    ]
    
    return render_template('dashboard/reports.html', rapports=rapports)

def generate_dashboard_charts():
    """Génère les données pour les graphiques du dashboard"""
    
    # Répartition par département
    dept_data = db.session.query(
        Employee.departement,
        func.count(Employee.id).label('count')
    ).filter_by(statut='Actif').group_by(Employee.departement).all()
    
    departements = {
        'labels': [dept[0] or 'Non défini' for dept in dept_data],
        'data': [dept[1] for dept in dept_data]
    }
    
    # Évolution des absences sur 6 mois
    today = date.today()
    absences_evolution = []
    
    for i in range(6):
        month_date = today - timedelta(days=30*i)
        count = Absence.query.filter(
            extract('month', Absence.date_absence) == month_date.month,
            extract('year', Absence.date_absence) == month_date.year
        ).count()
        absences_evolution.append({
            'month': month_date.strftime('%B'),
            'count': count
        })
    
    absences_evolution.reverse()
    
    # Congés par statut
    conges_statut = db.session.query(
        Conge.statut,
        func.count(Conge.id).label('count')
    ).group_by(Conge.statut).all()
    
    return {
        'departements': departements,
        'absences_evolution': absences_evolution,
        'conges_statut': [{'statut': c[0], 'count': c[1]} for c in conges_statut]
    }

@dashboard_bp.route('/reports/<report_type>')
@login_required
@permission_requise('rapports')
def generate_report(report_type):
    """Génère un rapport spécifique"""
    
    # Récupérer les paramètres
    format_type = request.args.get('format', 'pdf')
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    departement = request.args.get('departement')
    
    try:
        if report_type == 'employes':
            return generate_employees_report(format_type, date_debut, date_fin, departement)
        elif report_type == 'conges':
            return generate_leaves_report(format_type, date_debut, date_fin, departement)
        elif report_type == 'absences':
            return generate_absences_report(format_type, date_debut, date_fin, departement)
        elif report_type == 'paie':
            return generate_payroll_report(format_type, date_debut, date_fin, departement)
        elif report_type == 'evaluations':
            return generate_evaluations_report(format_type, date_debut, date_fin, departement)
        elif report_type == 'presences':
            return generate_attendance_report(format_type, date_debut, date_fin, departement)
        else:
            return jsonify({'error': 'Type de rapport non supporté'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_employees_report(format_type, date_debut, date_fin, departement):
    """Génère le rapport des employés"""
    
    query = Employee.query.filter_by(statut='Actif')
    
    if departement:
        query = query.filter_by(departement=departement)
    
    if date_debut and date_fin:
        query = query.filter(
            Employee.date_embauche.between(date_debut, date_fin)
        )
    
    employees = query.all()
    
    if format_type == 'excel':
        return generate_excel_report(employees, 'Rapport_Employes')
    elif format_type == 'csv':
        return generate_csv_report(employees, 'Rapport_Employes')
    else:
        return generate_pdf_report(employees, 'Rapport des Employés')

def generate_leaves_report(format_type, date_debut, date_fin, departement):
    """Génère le rapport des congés"""
    
    query = Conge.query.join(Employee)
    
    if departement:
        query = query.filter(Employee.departement == departement)
    
    if date_debut and date_fin:
        query = query.filter(
            Conge.date_debut.between(date_debut, date_fin)
        )
    
    leaves = query.all()
    
    if format_type == 'excel':
        return generate_excel_report(leaves, 'Rapport_Conges', 'conges')
    else:
        return generate_pdf_report(leaves, 'Rapport des Congés', 'conges')

def generate_absences_report(format_type, date_debut, date_fin, departement):
    """Génère le rapport des absences"""
    
    query = Absence.query.join(Employee)
    
    if departement:
        query = query.filter(Employee.departement == departement)
    
    if date_debut and date_fin:
        query = query.filter(
            Absence.date_absence.between(date_debut, date_fin)
        )
    
    absences = query.all()
    
    if format_type == 'excel':
        return generate_excel_report(absences, 'Rapport_Absences', 'absences')
    else:
        return generate_pdf_report(absences, 'Rapport des Absences', 'absences')

def generate_payroll_report(format_type, date_debut, date_fin, departement):
    """Génère le rapport de paie"""
    
    query = BulletinPaie.query.join(Employee)
    
    if departement:
        query = query.filter(Employee.departement == departement)
    
    if date_debut and date_fin:
        query = query.filter(
            BulletinPaie.periode_debut.between(date_debut, date_fin)
        )
    
    bulletins = query.all()
    
    if format_type == 'excel':
        return generate_excel_report(bulletins, 'Rapport_Paie', 'paie')
    else:
        return generate_pdf_report(bulletins, 'Rapport de Paie', 'paie')

def generate_evaluations_report(format_type, date_debut, date_fin, departement):
    """Génère le rapport des évaluations"""
    
    query = Evaluation.query.join(Employee)
    
    if departement:
        query = query.filter(Employee.departement == departement)
    
    if date_debut and date_fin:
        query = query.filter(
            Evaluation.date_evaluation.between(date_debut, date_fin)
        )
    
    evaluations = query.all()
    
    if format_type == 'excel':
        return generate_excel_report(evaluations, 'Rapport_Evaluations', 'evaluations')
    else:
        return generate_pdf_report(evaluations, 'Rapport des Évaluations', 'evaluations')

def generate_attendance_report(format_type, date_debut, date_fin, departement):
    """Génère le rapport des présences"""
    
    query = Presence.query.join(Employee)
    
    if departement:
        query = query.filter(Employee.departement == departement)
    
    if date_debut and date_fin:
        query = query.filter(
            Presence.date.between(date_debut, date_fin)
        )
    
    presences = query.all()
    
    if format_type == 'excel':
        return generate_excel_report(presences, 'Rapport_Presences', 'presences')
    else:
        return generate_pdf_report(presences, 'Rapport des Présences', 'presences')

def generate_excel_report(data, filename, report_type='employees'):
    """Génère un rapport Excel générique"""
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Convertir les données en DataFrame selon le type
        df_data = []
        
        if report_type == 'employees':
            for item in data:
                df_data.append({
                    'Nom': item.nom,
                    'Prénom': item.prenom or '',
                    'Poste': item.poste or '',
                    'Département': item.departement or '',
                    'Email': item.email or '',
                    'Date d\'embauche': item.date_embauche.strftime('%d/%m/%Y') if item.date_embauche else ''
                })
        
        elif report_type == 'conges':
            for item in data:
                df_data.append({
                    'Employé': f"{item.employee.nom} {item.employee.prenom or ''}",
                    'Département': item.employee.departement or '',
                    'Type de congé': item.type_conge,
                    'Date début': item.date_debut.strftime('%d/%m/%Y'),
                    'Date fin': item.date_fin.strftime('%d/%m/%Y'),
                    'Nombre de jours': item.nombre_jours,
                    'Statut': item.statut,
                    'Motif': item.motif or ''
                })
        
        elif report_type == 'absences':
            for item in data:
                df_data.append({
                    'Employé': f"{item.employe.nom} {item.employe.prenom or ''}",
                    'Département': item.employe.departement or '',
                    'Date': item.date_absence.strftime('%d/%m/%Y'),
                    'Motif': item.motif or '',
                    'État': item.etat,
                    'Impact sur paie': 'Oui' if item.impact_paie else 'Non',
                    'Justificatif': item.justificatif or ''
                })
        
        elif report_type == 'paie':
            for item in data:
                df_data.append({
                    'Employé': f"{item.employe.nom} {item.employe.prenom or ''}",
                    'Département': item.employe.departement or '',
                    'Période': f"{item.periode_debut.strftime('%d/%m/%Y')} - {item.periode_fin.strftime('%d/%m/%Y')}",
                    'Salaire brut': item.salaire_brut,
                    'Cotisations salariales': item.total_cotisations_salariales,
                    'Salaire net': item.salaire_net,
                    'Statut': item.statut
                })
        
        elif report_type == 'evaluations':
            for item in data:
                df_data.append({
                    'Employé': f"{item.employe.nom} {item.employe.prenom or ''}",
                    'Département': item.employe.departement or '',
                    'Date évaluation': item.date_evaluation.strftime('%d/%m/%Y'),
                    'Période': f"{item.periode_debut.strftime('%d/%m/%Y')} - {item.periode_fin.strftime('%d/%m/%Y')}" if item.periode_debut and item.periode_fin else str(item.annee),
                    'Note finale': item.note_finale or '',
                    'Statut': item.statut
                })
        
        elif report_type == 'presences':
            for item in data:
                df_data.append({
                    'Employé': f"{item.employe.nom} {item.employe.prenom or ''}",
                    'Département': item.employe.departement or '',
                    'Date': item.date.strftime('%d/%m/%Y'),
                    'Heure arrivée': item.heure_arrivee.strftime('%H:%M') if item.heure_arrivee else '',
                    'Heure départ': item.heure_depart.strftime('%H:%M') if item.heure_depart else '',
                    'Heures travaillées': item.heures_travaillees or 0,
                    'Statut': item.statut or ''
                })
        
        df = pd.DataFrame(df_data)
        df.to_excel(writer, index=False, sheet_name='Rapport')
    
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f'{filename}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def generate_csv_report(data, filename):
    """Génère un rapport CSV"""
    
    output = io.StringIO()
    
    # En-têtes
    output.write('Nom,Prénom,Poste,Département,Email,Date d\'embauche\n')
    
    # Données
    for item in data:
        output.write(f'{item.nom},{item.prenom or ""},{item.poste or ""},{item.departement or ""},{item.email or ""},{item.date_embauche.strftime("%d/%m/%Y") if item.date_embauche else ""}\n')
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        as_attachment=True,
        download_name=f'{filename}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mimetype='text/csv'
    )

def generate_pdf_report(data, title, report_type='employees'):
    """Génère un rapport PDF générique"""
    
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    
    output = io.BytesIO()
    
    # Créer le PDF
    p = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    
    # Titre
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 100, title)
    
    # Date de génération
    p.setFont("Helvetica", 10)
    p.drawString(100, height - 120, f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    
    # Données
    y = height - 160
    p.setFont("Helvetica", 10)
    
    for item in data:
        if y < 100:  # Nouvelle page si nécessaire
            p.showPage()
            y = height - 100
        
        if report_type == 'employees':
            text = f"{item.nom} {item.prenom or ''} - {item.poste or ''} ({item.departement or ''})"
        elif report_type == 'conges':
            text = f"{item.employee.nom} - {item.type_conge} ({item.date_debut.strftime('%d/%m/%Y')} - {item.date_fin.strftime('%d/%m/%Y')})"
        elif report_type == 'absences':
            text = f"{item.employe.nom} - {item.motif} ({item.date_absence.strftime('%d/%m/%Y')})"
        elif report_type == 'paie':
            text = f"{item.employe.nom} - {item.periode_debut.strftime('%m/%Y')} - {item.salaire_net:,.2f} FCFA"
        elif report_type == 'evaluations':
            text = f"{item.employe.nom} - {item.date_evaluation.strftime('%d/%m/%Y')} - Note: {item.note_finale or 'N/A'}"
        elif report_type == 'presences':
            text = f"{item.employe.nom} - {item.date.strftime('%d/%m/%Y')} - {item.heures_travaillees or 0}h"
        else:
            text = str(item)
        
        p.drawString(100, y, text)
        y -= 15
    
    p.save()
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f'{title.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
        mimetype='application/pdf'
    )

@dashboard_bp.route('/api/dashboard/analytics')
@login_required
def analytics_api():
    """API pour les données d'analytics avancées"""
    
    today = date.today()
    
    # Tendances des embauches
    embauches_trend = []
    for i in range(12):
        month_date = today - timedelta(days=30*i)
        count = Employee.query.filter(
            extract('month', Employee.date_embauche) == month_date.month,
            extract('year', Employee.date_embauche) == month_date.year
        ).count()
        embauches_trend.append({
            'month': month_date.strftime('%b %Y'),
            'count': count
        })
    
    # Analyse des absences par département
    absences_dept = db.session.query(
        Employee.departement,
        func.count(Absence.id).label('absences_count')
    ).join(Absence).group_by(Employee.departement).all()
    
    # Taux de présence
    total_employees = Employee.query.filter_by(statut='Actif').count()
    presents_aujourd_hui = total_employees - Absence.query.filter_by(date_absence=today).count()
    taux_presence = (presents_aujourd_hui / total_employees * 100) if total_employees > 0 else 0
    
    # Coût moyen des salaires par département
    salaires_dept = db.session.query(
        Employee.departement,
        func.avg(Employee.salaire_base).label('salaire_moyen')
    ).filter(Employee.salaire_base.isnot(None)).group_by(Employee.departement).all()
    
    return jsonify({
        'embauches_trend': embauches_trend,
        'absences_dept': [{'dept': a[0], 'count': a[1]} for a in absences_dept],
        'taux_presence': round(taux_presence, 2),
        'salaires_dept': [{'dept': s[0], 'salaire_moyen': float(s[1])} for s in salaires_dept]
    })

# ============================================================================
# ADVANCED DASHBOARD ANALYTICS
# ============================================================================

@dashboard_bp.route('/api/dashboard/kpi')
@login_required
def dashboard_kpi():
    """API pour les KPI avancés du dashboard"""
    
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    # Calcul des KPIs
    total_employees = Employee.query.filter_by(statut='Actif').count()
    
    # Taux de rotation (approximation)
    departures_year = Employee.query.filter(
        Employee.statut.in_(['Démissionné', 'Licencié']),
        extract('year', Employee.date_modification) == current_year
    ).count()
    
    turnover_rate = (departures_year / max(total_employees, 1)) * 100
    
    # Coût moyen des salaires
    avg_salary = db.session.query(func.avg(Employee.salaire_base)).scalar() or 0
    
    # Taux d'absentéisme
    total_absences_month = Absence.query.filter(
        extract('month', Absence.date_absence) == current_month,
        extract('year', Absence.date_absence) == current_year
    ).count()
    
    absenteeism_rate = (total_absences_month / max(total_employees, 1)) * 100
    
    # Satisfaction employés (basée sur les évaluations)
    avg_evaluation = db.session.query(func.avg(Evaluation.note_finale)).filter(
        Evaluation.statut == 'terminée'
    ).scalar() or 0
    
    # Productivité (heures travaillées vs heures prévues)
    heures_travaillees_month = db.session.query(func.sum(HeuresTravail.heures_travaillees)).filter(
        extract('month', HeuresTravail.date_travail) == current_month,
        extract('year', HeuresTravail.date_travail) == current_year
    ).scalar() or 0
    
    heures_prevues_month = total_employees * 22 * 8  # 22 jours x 8h approximation
    productivity_rate = (heures_travaillees_month / max(heures_prevues_month, 1)) * 100 if heures_prevues_month > 0 else 0
    
    return jsonify({
        'turnover_rate': round(turnover_rate, 2),
        'avg_salary': round(avg_salary, 2),
        'absenteeism_rate': round(absenteeism_rate, 2),
        'satisfaction_score': round(avg_evaluation, 2),
        'productivity_rate': round(productivity_rate, 2),
        'total_payroll': round(avg_salary * total_employees, 2)
    })

@dashboard_bp.route('/api/dashboard/departement-stats')
@login_required
def department_stats():
    """Statistiques détaillées par département"""
    
    # Statistiques par département
    dept_stats = db.session.query(
        Employee.departement,
        func.count(Employee.id).label('total_employees'),
        func.avg(Employee.salaire_base).label('avg_salary'),
        func.count(Absence.id).label('total_absences')
    ).outerjoin(Absence).filter(
        Employee.statut == 'Actif'
    ).group_by(Employee.departement).all()
    
    result = []
    for dept, total, avg_sal, absences in dept_stats:
        result.append({
            'department': dept or 'Non défini',
            'total_employees': total,
            'avg_salary': round(avg_sal or 0, 2),
            'total_absences': absences or 0,
            'absence_rate': round(((absences or 0) / max(total, 1)) * 100, 2)
        })
    
    return jsonify(result)

@dashboard_bp.route('/api/dashboard/trends')
@login_required
def dashboard_trends():
    """Tendances sur 12 mois"""
    
    today = date.today()
    trends = []
    
    for i in range(12):
        month_date = today - timedelta(days=30*i)
        month_year = f"{month_date.year}-{month_date.month:02d}"
        
        # Embauches
        embauches = Employee.query.filter(
            extract('month', Employee.date_embauche) == month_date.month,
            extract('year', Employee.date_embauche) == month_date.year
        ).count()
        
        # Démissions
        demissions = Employee.query.filter(
            Employee.statut.in_(['Démissionné', 'Licencié']),
            extract('month', Employee.date_modification) == month_date.month,
            extract('year', Employee.date_modification) == month_date.year
        ).count()
        
        # Absences
        absences = Absence.query.filter(
            extract('month', Absence.date_absence) == month_date.month,
            extract('year', Absence.date_absence) == month_date.year
        ).count()
        
        # Bulletins de paie
        bulletins = BulletinPaie.query.filter(
            BulletinPaie.mois == month_date.month,
            BulletinPaie.annee == month_date.year
        ).count()
        
        trends.append({
            'month': month_year,
            'month_name': month_date.strftime('%B %Y'),
            'embauches': embauches,
            'demissions': demissions,
            'absences': absences,
            'bulletins': bulletins
        })
    
    trends.reverse()
    return jsonify(trends)

@dashboard_bp.route('/dashboard/advanced')
@login_required
@permission_requise('rapports')
def advanced_dashboard():
    """Dashboard avancé avec analytics détaillées"""
    
    return render_template('dashboard/advanced.html')
