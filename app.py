import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from gerar_pdfs_rmfc import build_resident_pdf, build_synthesis_pdf

# Configurações de Estilo
AZUL_UNICAMP = "#1B4F72"
VERDE_SAUDE = "#27AE60"
LARANJA_ALERTA = "#E67E22"

st.set_page_config(page_title="RMFC 2026 - Diagnóstico por Eixos", layout="wide")

@st.cache_data(ttl=300)
def load_and_clean_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQR-KEmCfdmmAHhC_Y2GQe1MjDb5y1w6Qbg1GQmHiPCswIIIUctw7erzDH1xFqwLoWCOd5cLu552JNM/pub?output=csv"
    df = pd.read_csv(url)
    # Normaliza nomes de colunas removendo quebras de linha e espaços
    df.columns = [col.replace('\n', ' ').strip() for col in df.columns]
    return df

def get_multiselect_counts(df, column_name):
    """Conta ocorrências em colunas de múltipla escolha (separadas por vírgula)"""
    return df[column_name].str.split(',').explode().str.strip().value_counts()

def main():
    df = load_and_clean_data()
    
    st.title("🩺 Painel de Diagnóstico RMFC 2026")
    st.markdown("---")

    # --- EIXO 1: PERFIL DEMOGRÁFICO E ACADÊMICO ---
    st.header("📍 Eixo 1: Identificação e Perfil")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.subheader("Distribuição por UBS")
        fig_ubs = px.bar(df['UBS:'].value_counts(), color_discrete_sequence=[AZUL_UNICAMP])
        st.plotly_chart(fig_ubs, use_container_width=True)
    
    with c2:
        st.subheader("Ano de Graduação")
        fig_ano = px.pie(df, names='Ano de Graduação:', hole=0.4)
        st.plotly_chart(fig_ano, use_container_width=True)
        
    with c3:
        st.subheader("Experiência Prévia")
        # Identifica se há texto além de "Nenhuma" ou "Não"
        exp_check = df['Experiência profissional prévia:'].apply(
            lambda x: "Com Experiência" if len(str(x)) > 10 else "Recém-formado"
        )
        st.plotly_chart(px.pie(names=exp_check.value_counts().index, values=exp_check.value_counts().values), use_container_width=True)

    st.markdown("---")

    # --- EIXO 2: VIVÊNCIAS CLÍNICAS E PROCEDIMENTOS ---
    st.header("💉 Eixo 2: Prática Clínica e Procedimentos")
    
    col_clin1, col_clin2 = st.columns([2, 1])
    
    with col_clin1:
        st.subheader("Competências de Atenção à Saúde (O que já fazem)")
        clinica_counts = get_multiselect_counts(df, 'Atenção à saúde')
        fig_clin = px.bar(clinica_counts, orientation='h', color_discrete_sequence=[VERDE_SAUDE])
        st.plotly_chart(fig_clin, use_container_width=True)
        
    with col_clin2:
        st.subheader("Inserção de Dispositivos (DIU/Implanon)")
        diu = df['Atenção à saúde'].str.contains('Inseriu DIU').sum()
        imp = df['Atenção à saúde'].str.contains('Inseriu Implanon').sum()
        fig_proc = go.Figure(go.Bar(x=['DIU', 'Implanon'], y=[diu, imp], marker_color=LARANJA_ALERTA))
        st.plotly_chart(fig_proc, use_container_width=True)

    st.markdown("---")

    # --- EIXO 3: PROCESSO DE TRABALHO E REDE ---
    st.header("🏢 Eixo 3: Gestão, APS e Rede")
    
    # Mapeamento de níveis de autonomia em processos de APS
    col_proc1, col_proc2, col_proc3 = st.columns(3)
    
    with col_proc1:
        st.subheader("Acolhimento na APS")
        st.plotly_chart(px.funnel(df['Acolhimento'].value_counts()), use_container_width=True)

    with col_proc2:
        st.subheader("Gestão de Agenda")
        st.plotly_chart(px.pie(df, names='Gestão da agenda'), use_container_width=True)

    with col_proc3:
        st.subheader("Conhecimento da Rede")
        rede_counts = get_multiselect_counts(df, 'Rede')
        st.plotly_chart(px.bar(rede_counts, orientation='h'), use_container_width=True)

    st.markdown("---")

    # --- EIXO 4: DEMANDAS DE FORMAÇÃO (QUALITATIVO) ---
    st.header("📚 Eixo 4: Necessidades de Aprendizado")
    
    aba_nucleo, aba_coletiva = st.tabs(["🔬 Núcleo MFC", "🌍 Saúde Coletiva"])
    
    with aba_nucleo:
        for i, row in df.iterrows():
            with st.expander(f"📌 {row['Nome:']} (UBS {row['UBS:']})"):
                st.write(f"**Desejos:** {row['Núcleo MFC']}")
                
    with aba_coletiva:
        for i, row in df.iterrows():
            with st.expander(f"📌 {row['Nome:']} (UBS {row['UBS:']})"):
                st.write(f"**Interesses em Gestão/Epidemio:** {row['Campo Saúde Coletiva (Gestão do Cuidado, Processo de Trabalho, Epidemio, etc.)']}")

    # --- EXPORTAÇÃO ---
    st.sidebar.divider()
    st.sidebar.subheader("Relatórios")
    if st.sidebar.button("📥 Baixar Síntese Geral (PDF)"):
        pdf = build_synthesis_pdf(df)
        st.sidebar.download_button("Download", pdf, "sintese_rmfc_2026.pdf")

if __name__ == "__main__":
    main()
