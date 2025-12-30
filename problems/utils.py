from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from django.conf import settings
import os

def generate_8d_pdf(problem):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#226D68'),
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#18534F'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    # Header
    elements.append(Paragraph(f"Rapport 8D: {problem.title}", title_style))
    elements.append(Paragraph(f"Statut: {problem.get_status_display()}", styles['Normal']))
    elements.append(Paragraph(f"Étape actuelle: {problem.current_step}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # D0: Symptôme
    elements.append(Paragraph("D0 - Symptôme & Préparation", subtitle_style))
    elements.append(Paragraph(f"<b>Description:</b> {problem.description}", styles['Normal']))
    elements.append(Paragraph(f"<b>Créé par:</b> {problem.created_by.username if problem.created_by else 'Inconnu'}", styles['Normal']))
    elements.append(Paragraph(f"<b>Date:</b> {problem.created_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # D1: Équipe
    elements.append(Paragraph("D1 - Équipe", subtitle_style))
    data_d1 = [
        ['Rôle', 'Détail'],
        ['Poste de travail', problem.workstation or '-'],
        ['ID Opérateur', problem.operator_id or '-'],
        ['Méthode détection', problem.detection_method or '-'],
        ['Quantité impactée', str(problem.impacted_quantity) or '-'],
        ['Importance', problem.importance or '-']
    ]
    t_d1 = Table(data_d1, colWidths=[2*inch, 4*inch])
    t_d1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#226D68')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t_d1)
    
    # D2: Description
    elements.append(Paragraph("D2 - Description du Problème (QQOQCCP)", subtitle_style))
    data_d2 = [
        ['Qui', problem.d2_who or '-'],
        ['Quoi', problem.d2_what or '-'],
        ['Où', problem.d2_where or '-'],
        ['Quand', problem.d2_when or '-'],
        ['Comment', problem.d2_how or '-'],
        ['Combien', problem.d2_how_many or '-'],
        ['Pourquoi', problem.d2_why or '-']
    ]
    t_d2 = Table(data_d2, colWidths=[2*inch, 4*inch])
    t_d2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0fcfc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(t_d2)

    # D3: Actions de Containment
    elements.append(Paragraph("D3 - Actions de Containment", subtitle_style))
    if problem.containment_actions:
        elements.append(Paragraph(f"{problem.containment_actions}", styles['Normal']))
    else:
        elements.append(Paragraph("Aucune action de containment spécifiée.", styles['Normal']))
    
    # D4: Causes Racines
    elements.append(Paragraph("D4 - Causes Racines", subtitle_style))
    if problem.root_causes.exists():
        for rc in problem.root_causes.all():
            elements.append(Paragraph(f"• {rc.description} ({rc.category})", styles['Normal']))
            elements.append(Paragraph(f"  Méthode: {rc.analysis_method}", styles['Italic']))
            elements.append(Spacer(1, 6))
    else:
        elements.append(Paragraph("Aucune cause racine identifiée.", styles['Normal']))

    # D5 & D6: Actions Correctives
    elements.append(Paragraph("D5 & D6 - Actions Correctives & Validation", subtitle_style))
    corrective_actions = problem.actions.filter(action_type='CORRECTIVE')
    if corrective_actions.exists():
        actions_data = [['Description', 'Responsable', 'Statut']]
        for action in corrective_actions:
            actions_data.append([
                action.description[:50] + '...' if len(action.description) > 50 else action.description,
                action.assigned_to.username if action.assigned_to else '-',
                action.get_status_display()
            ])
        t_actions = Table(actions_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        t_actions.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#226D68')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        elements.append(t_actions)
    else:
        elements.append(Paragraph("Aucune action corrective.", styles['Normal']))

    # D7: Actions Préventives
    elements.append(Paragraph("D7 - Actions Préventives", subtitle_style))
    preventive_actions = problem.actions.filter(action_type='PREVENTIVE')
    if preventive_actions.exists():
        actions_data = [['Description', 'Responsable', 'Statut']]
        for action in preventive_actions:
            actions_data.append([
                action.description[:50] + '...' if len(action.description) > 50 else action.description,
                action.assigned_to.username if action.assigned_to else '-',
                action.get_status_display()
            ])
        t_actions = Table(actions_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        t_actions.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9c27b0')), # Different color for preventive
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        elements.append(t_actions)
    else:
        elements.append(Paragraph("Aucune action préventive.", styles['Normal']))

    # D8: Clôture
    elements.append(Paragraph("D8 - Clôture", subtitle_style))
    if problem.status == 'CLOSED':
        elements.append(Paragraph("Le problème est officiellement clôturé.", styles['Normal']))
        if problem.final_report_validated_by:
             elements.append(Paragraph(f"Rapport validé par: {problem.final_report_validated_by.username}", styles['Normal']))
    else:
         elements.append(Paragraph("Le problème n'est pas encore clôturé.", styles['Normal']))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer
