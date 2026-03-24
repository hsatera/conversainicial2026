import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def build_resident_pdf(dados):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, spaceAfter=12)
    label_style = ParagraphStyle('Label', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
    text_style = styles['Normal']

    elements = []
    elements.append(Paragraph(f"Diagnóstico Inicial: {dados['Nome:']}", title_style))
    elements.append(Spacer(1, 12))

    # Tabela de Identificação
    info_data = [
        [Paragraph("UBS:", label_style), str(dados.get('UBS:', ''))],
        [Paragraph("Equipe:", label_style), str(dados.get('Equipe:', ''))],
        [Paragraph("Graduação:", label_style), f"{dados.get('Instituição de Ensino em que se graduou:', '')} ({dados.get('Ano de Graduação:', '')})"],
    ]
    t = Table(info_data, colWidths=[100, 350])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 6)]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Seções dissertativas
    secoes = [
        ("Motivação para MFC", 'Por que escolheu MFC?'),
        ("Experiência Profissional Prévia", 'Experiência profissional prévia:'),
        ("Demandas de Aprendizado (Núcleo)", 'Núcleo MFC'),
        ("Saúde Coletiva e Gestão", 'Campo Saúde Coletiva (Gestão do Cuidado, Processo de Trabalho, Epidemio, etc.)'),
        ("Observações do Diagnóstico", 'Se quiser adicionar informações relevantes sobre a conversa e o diagnóstico inicial, para termos em comum, pode utilizar esse espaço')
    ]

    for titulo, campo in secoes:
        if campo in dados and pd.notna(dados[campo]):
            elements.append(Paragraph(titulo, label_style))
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(str(dados[campo]), text_style))
            elements.append(Spacer(1, 12))

    doc.build(elements)
    buffer.seek(0)
    return buffer

def build_synthesis_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = [Paragraph("Relatório Geral de Residentes 2026", getSampleStyleSheet()['Heading1']), Spacer(1, 12)]
    
    data = [["Nome", "UBS", "Equipe", "Graduação"]]
    for _, row in df.iterrows():
        data.append([row['Nome:'], row['UBS:'], row['Equipe:'], row['Instituição de Ensino em que se graduou:']])
    
    t = Table(data, colWidths=[140, 90, 90, 130])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 8)
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer
