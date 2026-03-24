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
    label_style = ParagraphStyle('Label', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, spaceBefore=8)
    text_style = ParagraphStyle('Text', parent=styles['Normal'], fontSize=10, leading=12)

    elements = []
    elements.append(Paragraph(f"Diagnóstico Inicial: {dados['Nome:']}", title_style))
    
    # Tabela de Identificação Rápida
    id_data = [
        [Paragraph("UBS:", label_style), dados.get('UBS:', '')],
        [Paragraph("Equipe:", label_style), dados.get('Equipe:', '')],
        [Paragraph("Telefone:", label_style), str(dados.get('Telefone:', ''))],
        [Paragraph("Email:", label_style), dados.get('Email da residente:', '')],
        [Paragraph("Graduação:", label_style), f"{dados.get('Instituição de Ensino em que se graduou:', '')} ({dados.get('Ano de Graduação:', '')})"]
    ]
    t = Table(id_data, colWidths=[100, 350])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    # Mapeamento de todos os campos do formulário para o PDF
    campos_pdf = [
        ("Motivação para MFC", "Por que escolheu MFC?"),
        ("Experiência Profissional Prévia", "Experiência profissional prévia:"),
        ("Participação em Reunião de Equipe", "Reunião de equipe"),
        ("Experiência com Acolhimento", "Acolhimento"),
        ("Atenção Domiciliar", "Atenção domiciliar"),
        ("Gestão da Agenda", "Gestão da agenda"),
        ("Ações de Planejamento", "Ações de planejamento (marque ações)"),
        ("NASF / E-multi / Intersetorial", "NASF-E-multi-Intersetorial"),
        ("Habilidades de Atenção à Saúde", "Atenção à saúde"),
        ("Experiência na Rede", "Rede"),
        ("Relatos da Conversa", "Relatos/fatos específicos que gostaria de relatar a partir da conversa"),
        ("Demandas de Núcleo MFC", "Núcleo MFC"),
        ("Campo Saúde Coletiva", "Campo Saúde Coletiva (Gestão do Cuidado, Processo de Trabalho, Epidemio, etc.)"),
        ("Informações Adicionais / Diagnóstico", "Se quiser adicionar informações relevantes sobre a conversa e o diagnóstico inicial, para termos em comum, pode utilizar esse espaço")
    ]

    for label, campo in campos_pdf:
        valor = dados.get(campo, "Não informado")
        if pd.notna(valor) and str(valor).strip() != "":
            elements.append(Paragraph(label, label_style))
            elements.append(Paragraph(str(valor), text_style))
            elements.append(Spacer(1, 6))

    doc.build(elements)
    buffer.seek(0)
    return buffer

def build_synthesis_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = [Paragraph("Síntese Geral - Residentes 2026", getSampleStyleSheet()['Heading1']), Spacer(1, 12)]
    
    data = [["Nome", "UBS", "Equipe", "Email"]]
    for _, row in df.iterrows():
        data.append([row['Nome:'], row['UBS:'], row['Equipe:'], row['Email da residente:']])
    
    t = Table(data, colWidths=[140, 100, 100, 150])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('GRID', (0,0), (-1,-1), 0.5, colors.black), ('FONTSIZE', (0,0), (-1,-1), 8)]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer
