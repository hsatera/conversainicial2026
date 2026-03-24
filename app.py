"""
RMFC 2026 — Painel de Diagnóstico de Entrada
=============================================
Lê dados ao vivo do Google Sheets (publicado como CSV) e gera PDFs exportáveis.

Instalação:
    pip install streamlit plotly pandas reportlab gspread requests openpyxl

Execução:
    streamlit run painel_rmfc.py

Configuração do Google Sheets:
    1. Abra a planilha → Arquivo → Compartilhar → Publicar na web
    2. Escolha a aba "Respostas ao formulário 1" e formato CSV
    3. Cole a URL no campo SHEET_CSV_URL abaixo (ou defina a variável de ambiente)

    Alternativamente, use autenticação via Service Account do Google:
    - Crie uma Service Account no Google Cloud Console
    - Compartilhe a planilha com o e-mail da service account
    - Baixe o JSON de credenciais e defina GOOGLE_CREDENTIALS_JSON no ambiente
"""

import os
import io
import sys
import time
import tempfile
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ─── Importa funções de geração de PDF do script principal ────────────────────
# Adiciona o diretório do script ao path para importar gerar_pdfs_rmfc
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from gerar_pdfs_rmfc import (
    build_resident_pdf, build_synthesis_pdf, get, COL_PREFIXES
)

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO — ajuste aqui ou via variáveis de ambiente
# ══════════════════════════════════════════════════════════════════════════════
SHEET_CSV_URL = os.environ.get(
    "RMFC_SHEET_CSV_URL",
    # URL padrão: o spreadsheet público exportado como CSV
    # Troque pelo link "Publicar na web > CSV" da sua planilha
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQR-KEmCfdmmAHhC_Y2GQe1MjDb5y1w6Qbg1GQmHiPCswIIIUctw7erzDH1xFqwLoWCOd5cLu552JNM"
    "/pub?output=csv",
)

# Se preferir usar um arquivo local (fallback)
LOCAL_XLSX_FALLBACK = os.environ.get("RMFC_LOCAL_XLSX", "")

# Cache: quantos segundos antes de buscar novos dados
CACHE_TTL = int(os.environ.get("RMFC_CACHE_TTL", "60"))

# ══════════════════════════════════════════════════════════════════════════════
# CORES
# ══════════════════════════════════════════════════════════════════════════════
AZUL      = "#1B4F72"
AZUL_MED  = "#2E86C1"
VERDE     = "#27AE60"
AMARELO   = "#F39C12"
VERMELHO  = "#E74C3C"
CINZA     = "#717D7E"


# ══════════════════════════════════════════════════════════════════════════════
# CARREGAMENTO DE DADOS
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_data_from_sheet(url: str) -> pd.DataFrame:
    """Baixa a planilha publicada como CSV."""
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    return df


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_data_from_xlsx(path: str) -> pd.DataFrame:
    return pd.read_excel(path)


def load_data() -> pd.DataFrame:
    """Tenta carregar da URL pública; fallback para arquivo local."""
    try:
        with st.spinner("🔄 Atualizando dados do Google Sheets…"):
            df = load_data_from_sheet(SHEET_CSV_URL)
        return df
    except Exception as e:
        if LOCAL_XLSX_FALLBACK and os.path.exists(LOCAL_XLSX_FALLBACK):
            st.warning(f"⚠️ Não foi possível acessar o Google Sheets ({e}). "
                       f"Usando arquivo local: {LOCAL_XLSX_FALLBACK}")
            return load_data_from_xlsx(LOCAL_XLSX_FALLBACK)
        st.error(
            f"❌ Não foi possível carregar os dados.\n\n"
            f"**Erro:** {e}\n\n"
            f"Configure `RMFC_SHEET_CSV_URL` com a URL de exportação CSV da planilha, "
            f"ou `RMFC_LOCAL_XLSX` com o caminho para o arquivo .xlsx."
        )
        st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def clean(val):
    if not isinstance(val, str) and pd.isna(val):
        return None
    v = str(val).strip()
    return v if v and v.lower() != 'nan' else None


def nivel_aps(val):
    if not val:
        return "Não informado"
    v = val.lower()
    if 'nunca' in v:
        return "Nunca"
    if 'profissional de referência' in v and 'não como' not in v:
        return "Profissional de referência"
    return "Parcial / estudante"


def nivel_score(val):
    m = {"Não informado": 0, "Nunca": 1, "Parcial / estudante": 2,
         "Profissional de referência": 3}
    return m.get(nivel_aps(val), 0)


def primeiro_nome(nome):
    return (nome or 'R').split()[0]


def pdf_bytes_resident(row) -> bytes:
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        path = f.name
    build_resident_pdf(row, path)
    with open(path, 'rb') as f:
        data = f.read()
    os.unlink(path)
    return data


def pdf_bytes_synthesis(df) -> bytes:
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        path = f.name
    build_synthesis_pdf(df, path)
    with open(path, 'rb') as f:
        data = f.read()
    os.unlink(path)
    return data


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="RMFC 2026 · Painel de Diagnóstico",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado
st.markdown(f"""
<style>
    .main-header {{
        background: linear-gradient(135deg, {AZUL} 0%, {AZUL_MED} 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }}
    .main-header h1 {{ margin: 0; font-size: 1.8rem; }}
    .main-header p  {{ margin: 0.3rem 0 0; opacity: 0.85; font-size: 0.95rem; }}

    .metric-card {{
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,.06);
    }}
    .metric-card .val  {{ font-size: 2rem; font-weight: 700; color: {AZUL}; }}
    .metric-card .lbl  {{ font-size: 0.82rem; color: {CINZA}; margin-top: .2rem; }}

    .section-title {{
        font-size: 1.15rem;
        font-weight: 700;
        color: {AZUL};
        border-left: 4px solid {AZUL_MED};
        padding-left: 0.6rem;
        margin: 1.5rem 0 0.8rem;
    }}

    .resident-badge {{
        display: inline-block;
        background: {AZUL_MED};
        color: white;
        border-radius: 20px;
        padding: 0.2rem 0.7rem;
        font-size: 0.8rem;
        margin: 0.15rem;
    }}
    .tag-green  {{ background: {VERDE}; }}
    .tag-yellow {{ background: {AMARELO}; }}
    .tag-red    {{ background: {VERMELHO}; }}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Unicamp_logo.svg/200px-Unicamp_logo.svg.png",
             width=90)
    st.markdown("## ⚙️ Configurações")

    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("**Fonte dos dados**")
    st.code(SHEET_CSV_URL[:60] + "…", language=None)

    st.markdown("---")
    st.markdown("**Upload de arquivo local**")
    uploaded = st.file_uploader("Carregar .xlsx", type=["xlsx"],
                                help="Substitui temporariamente a fonte online")

    st.markdown("---")
    aba = st.radio("Navegar para", [
        "📊 Visão Geral",
        "🗺️ Mapa de Vivências",
        "📚 Necessidades",
        "👤 Por Residente",
        "📄 Exportar PDFs",
    ])


# ──────────────────────────────────────────────────────────────────────────────
# CARREGA DADOS
# ──────────────────────────────────────────────────────────────────────────────
if uploaded:
    df = pd.read_excel(uploaded)
    st.sidebar.success(f"✅ Arquivo carregado: {len(df)} residentes")
else:
    df = load_data()

n = len(df)

# Cabeçalho principal
st.markdown(f"""
<div class="main-header">
  <h1>🏥 RMFC 2026 · Diagnóstico de Entrada</h1>
  <p>Conversa Inicial · {n} residentes · Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ABA: VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════
if aba == "📊 Visão Geral":
    # Métricas rápidas
    sem_exp = sum(
        1 for _, r in df.iterrows()
        if not get(r, 'exp') or get(r,'exp').lower() in ['nenhuma.','nenhuma','não','nao']
    )
    with_crm = n - sum(1 for _,r in df.iterrows()
                       if 'crm' in str(get(r,'relatos') or '').lower())
    nunca_acolh = sum(1 for _,r in df.iterrows() if 'nunca' in str(get(r,'acolh') or '').lower())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="val">{n}</div>'
                    f'<div class="lbl">Residentes</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="val">{sem_exp}</div>'
                    f'<div class="lbl">Sem exp. prévia</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="val">{nunca_acolh}</div>'
                    f'<div class="lbl">Nunca fizeram acolhimento</div></div>', unsafe_allow_html=True)
    with c4:
        ubs_set = {get(r,'ubs') for _,r in df.iterrows() if get(r,'ubs')}
        st.markdown(f'<div class="metric-card"><div class="val">{len(ubs_set)}</div>'
                    f'<div class="lbl">UBS diferentes</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Distribuição por UBS</div>', unsafe_allow_html=True)
    ubs_counts = df.apply(lambda r: get(r,'ubs') or 'Não informado', axis=1).value_counts()
    fig = px.bar(
        x=ubs_counts.index, y=ubs_counts.values,
        labels={'x':'UBS','y':'Residentes'},
        color=ubs_counts.values, color_continuous_scale='Blues',
        text=ubs_counts.values,
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(showlegend=False, coloraxis_showscale=False,
                      plot_bgcolor='white', margin=dict(t=20,b=20))
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Ano de Graduação</div>', unsafe_allow_html=True)
        anos = df.apply(lambda r: str(get(r,'ano_grad') or 'N/I'), axis=1).value_counts()
        fig2 = px.pie(values=anos.values, names=anos.index,
                      color_discrete_sequence=px.colors.sequential.Blues_r)
        fig2.update_layout(margin=dict(t=20,b=20,l=0,r=0))
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Exp. Profissional Prévia</div>', unsafe_allow_html=True)
        exp_cats = ['Com experiência','Sem experiência']
        exp_vals = [n - sem_exp, sem_exp]
        fig3 = px.pie(values=exp_vals, names=exp_cats,
                      color_discrete_sequence=[AZUL_MED, '#E8F4FD'])
        fig3.update_layout(margin=dict(t=20,b=20,l=0,r=0))
        st.plotly_chart(fig3, use_container_width=True)

    # Tabela resumo
    st.markdown('<div class="section-title">Tabela da Turma</div>', unsafe_allow_html=True)
    tabela = pd.DataFrame([{
        'Nome':     get(r,'nome')    or '-',
        'UBS':      get(r,'ubs')     or '-',
        'Equipe':   get(r,'equipe')  or '-',
        'Graduação':get(r,'grad')    or '-',
        'Ano':      get(r,'ano_grad')or '-',
        'Exp. prévia': get(r,'exp')  or 'Nenhuma',
    } for _,r in df.iterrows()])
    st.dataframe(tabela, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# ABA: MAPA DE VIVÊNCIAS
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "🗺️ Mapa de Vivências":
    st.markdown('<div class="section-title">Nível de Experiência por Atividade na APS</div>',
                unsafe_allow_html=True)

    aps_keys = [
        ('reuniao', 'Reunião de equipe'),
        ('acolh',   'Acolhimento'),
        ('domicil', 'Atenção domiciliar'),
        ('agenda',  'Gestão da agenda'),
        ('nasf',    'NASF / Emulti'),
    ]

    nomes   = [get(r,'nome') or f'R{i}' for i,(_,r) in enumerate(df.iterrows())]
    niveis  = {lbl: [nivel_score(get(r,k)) for _,r in df.iterrows()] for k,lbl in aps_keys}

    heatmap_df = pd.DataFrame(niveis, index=[primeiro_nome(n) for n in nomes])

    fig = go.Figure(go.Heatmap(
        z=heatmap_df.values,
        x=heatmap_df.columns.tolist(),
        y=heatmap_df.index.tolist(),
        colorscale=[
            [0,   '#F5F5F5'],
            [0.33,'#AED6F1'],
            [0.66,'#2E86C1'],
            [1,   '#1B4F72'],
        ],
        zmin=0, zmax=3,
        text=[[
            ['✗','○','◑','●'][v] for v in row
        ] for row in heatmap_df.values],
        texttemplate='%{text}',
        showscale=True,
        colorbar=dict(
            tickvals=[0,1,2,3],
            ticktext=['Não inf.','Nunca','Parcial','Prof. ref.'],
        ),
    ))
    fig.update_layout(height=320, margin=dict(t=20,b=20,l=0,r=0))
    st.plotly_chart(fig, use_container_width=True)

    # Barras de distribuição por atividade
    st.markdown('<div class="section-title">Distribuição por Atividade</div>',
                unsafe_allow_html=True)

    cats   = ['Nunca', 'Parcial / estudante', 'Profissional de referência', 'Não informado']
    colors = [VERMELHO, AMARELO, VERDE, CINZA]

    bar_data = []
    for k, lbl in aps_keys:
        cnt = {c: 0 for c in cats}
        for _, r in df.iterrows():
            cnt[nivel_aps(get(r, k))] += 1
        for c in cats:
            bar_data.append({'Atividade': lbl, 'Nível': c, 'N': cnt[c]})

    bar_df = pd.DataFrame(bar_data)
    fig2 = px.bar(bar_df, x='Atividade', y='N', color='Nível',
                  color_discrete_sequence=colors,
                  barmode='stack', text_auto=True)
    fig2.update_layout(plot_bgcolor='white', margin=dict(t=20,b=20),
                       legend=dict(orientation='h', y=-0.25))
    st.plotly_chart(fig2, use_container_width=True)

    # Atenção à saúde — frequência de itens
    st.markdown('<div class="section-title">Atividades de Atenção à Saúde (frequência)</div>',
                unsafe_allow_html=True)
    from collections import Counter
    itens = Counter()
    for _, r in df.iterrows():
        val = get(r, 'atencao') or ''
        for item in val.split(','):
            item = item.strip()
            if item:
                itens[item] += 1

    if itens:
        top = pd.DataFrame(itens.most_common(12), columns=['Atividade','N'])
        fig3 = px.bar(top, x='N', y='Atividade', orientation='h',
                      color='N', color_continuous_scale='Blues', text='N')
        fig3.update_traces(textposition='outside')
        fig3.update_layout(showlegend=False, coloraxis_showscale=False,
                           plot_bgcolor='white', margin=dict(t=20,b=20,l=0,r=0),
                           height=400, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ABA: NECESSIDADES
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "📚 Necessidades":
    st.markdown('<div class="section-title">Palavras-chave nas Necessidades de Aprendizado</div>',
                unsafe_allow_html=True)

    from collections import Counter
    import re

    STOPWORDS = {
        'de','e','a','o','as','os','que','em','com','para','na','no','se','da',
        'do','um','uma','por','mais','não','gostaria','refere','nada','especificamente',
        'nao','sobre','isso','como','faz','ter','ser','contato','pouco','bastante',
    }

    def tokenize(text):
        return [w.lower() for w in re.findall(r'\b[a-záéíóúãõâêîôûçà]{4,}\b', text or '')
                if w.lower() not in STOPWORDS]

    col1, col2 = st.columns(2)
    for col, key, titulo in [
        (col1, 'nucleo',  '🔬 Núcleo MFC'),
        (col2, 'campo',   '🌍 Saúde Coletiva'),
    ]:
        with col:
            st.markdown(f"**{titulo}**")
            todas = ' '.join(str(get(r, key) or '') for _,r in df.iterrows())
            freq  = Counter(tokenize(todas))
            if freq:
                wdf = pd.DataFrame(freq.most_common(15), columns=['Termo','Freq'])
                fig = px.bar(wdf, x='Freq', y='Termo', orientation='h',
                             color='Freq', color_continuous_scale='Blues', text='Freq')
                fig.update_traces(textposition='outside')
                fig.update_layout(showlegend=False, coloraxis_showscale=False,
                                  plot_bgcolor='white', margin=dict(t=10,b=10,l=0,r=0),
                                  height=380, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-title">Respostas Completas — Núcleo MFC</div>',
                unsafe_allow_html=True)
    for _, row in df.iterrows():
        nome   = get(row,'nome') or 'Residente'
        nucleo = get(row,'nucleo') or '—'
        with st.expander(nome):
            st.write(nucleo)

    st.markdown('<div class="section-title">Respostas Completas — Saúde Coletiva</div>',
                unsafe_allow_html=True)
    for _, row in df.iterrows():
        nome  = get(row,'nome') or 'Residente'
        campo = get(row,'campo') or '—'
        with st.expander(nome):
            st.write(campo)


# ══════════════════════════════════════════════════════════════════════════════
# ABA: POR RESIDENTE
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "👤 Por Residente":
    nomes = [get(r,'nome') or f'Residente {i}' for i,(_,r) in enumerate(df.iterrows())]
    sel   = st.selectbox("Selecione o residente", nomes)
    row   = df.iloc[nomes.index(sel)]

    col1, col2 = st.columns([1,2])
    with col1:
        st.markdown(f"### {sel}")
        st.markdown(f"**UBS:** {get(row,'ubs') or '-'}")
        st.markdown(f"**Equipe:** {get(row,'equipe') or '-'}")
        st.markdown(f"**Graduação:** {get(row,'grad') or '-'} ({get(row,'ano_grad') or '-'})")
        st.markdown(f"**E-mail:** {get(row,'email_res') or '-'}")
        exp = get(row,'exp')
        if exp:
            st.markdown(f"**Exp. prévia:** {exp}")

    with col2:
        # Radar de vivências APS
        aps_keys = [
            ('reuniao','Reunião'),('acolh','Acolhimento'),
            ('domicil','At. domiciliar'),('agenda','Gestão agenda'),
            ('nasf','NASF/Emulti'),
        ]
        vals = [nivel_score(get(row, k)) for k,_ in aps_keys]
        cats = [lbl for _,lbl in aps_keys]
        fig  = go.Figure(go.Scatterpolar(
            r=vals+[vals[0]], theta=cats+[cats[0]],
            fill='toself', fillcolor=f'rgba(46,134,193,0.3)',
            line_color=AZUL_MED, name=sel,
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(range=[0,3], tickvals=[0,1,2,3],
                                ticktext=['✗','○','◑','●']),
            ),
            height=320, margin=dict(t=30,b=10,l=20,r=20),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    motivo = get(row,'motivo')
    if motivo:
        st.markdown(f"**🎯 Por que escolheu MFC?**")
        st.info(motivo)

    for key, label in [
        ('atencao','🏥 Atenção à Saúde'),('rede','🔗 Rede'),
        ('nucleo','📚 Núcleo MFC'),('campo','🌍 Saúde Coletiva'),
        ('relatos','📝 Relatos'),('adicional','ℹ️ Adicionais'),
    ]:
        val = get(row, key)
        if val:
            st.markdown(f"**{label}**")
            st.write(val)


# ══════════════════════════════════════════════════════════════════════════════
# ABA: EXPORTAR PDFs
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "📄 Exportar PDFs":
    st.markdown('<div class="section-title">Exportar PDF de Síntese da Turma</div>',
                unsafe_allow_html=True)

    if st.button("📊 Gerar PDF — Síntese da Turma", use_container_width=True):
        with st.spinner("Gerando PDF…"):
            data = pdf_bytes_synthesis(df)
        st.download_button(
            label="⬇️ Baixar Síntese",
            data=data,
            file_name="RMFC2026_Sintese_Turma.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown('<div class="section-title">Exportar PDF Individual por Residente</div>',
                unsafe_allow_html=True)

    nomes = [get(r,'nome') or f'Residente {i}' for i,(_,r) in enumerate(df.iterrows())]

    for (idx, row), nome in zip(df.iterrows(), nomes):
        col1, col2 = st.columns([3,1])
        col1.markdown(f"**{nome}** — UBS {get(row,'ubs') or '-'}, Equipe {get(row,'equipe') or '-'}")
        if col2.button(f"📄 PDF", key=f"pdf_{idx}"):
            with st.spinner(f"Gerando PDF — {nome}…"):
                data = pdf_bytes_resident(row)
            fname = nome.replace(' ','_').replace('/','_') + '.pdf'
            st.download_button(
                label=f"⬇️ Baixar {nome}",
                data=data,
                file_name=fname,
                mime="application/pdf",
                key=f"dl_{idx}",
                use_container_width=True,
            )

    st.markdown("---")
    st.markdown("**⬇️ Baixar todos de uma vez**")
    if st.button("📦 Gerar ZIP com todos os PDFs", use_container_width=True):
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            with st.spinner("Gerando PDFs…"):
                zf.writestr("RMFC2026_Sintese_Turma.pdf", pdf_bytes_synthesis(df))
                for (idx, row), nome in zip(df.iterrows(), nomes):
                    fname = nome.replace(' ','_').replace('/','_') + '.pdf'
                    zf.writestr(f"residentes/{fname}", pdf_bytes_resident(row))
        buf.seek(0)
        st.download_button(
            label="⬇️ Baixar ZIP completo",
            data=buf.getvalue(),
            file_name="RMFC2026_PDFs.zip",
            mime="application/zip",
            use_container_width=True,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<small style='color:{CINZA}'>RMFC 2026 · Painel de Diagnóstico de Entrada · "
    f"Dados: Google Sheets · Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</small>",
    unsafe_allow_html=True,
)
