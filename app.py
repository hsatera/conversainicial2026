import streamlit as st
import pandas as pd
import plotly.express as px
from gerar_pdfs_rmfc import build_resident_pdf, build_synthesis_pdf

# Configurações iniciais
st.set_page_config(page_title="Painel RMFC UNICAMP 2026", layout="wide", page_icon="🩺")

# Função para carregar dados do Google Sheets
@st.cache_data(ttl=600) # Atualiza a cada 10 minutos
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQR-KEmCfdmmAHhC_Y2GQe1MjDb5y1w6Qbg1GQmHiPCswIIIUctw7erzDH1xFqwLoWCOd5cLu552JNM/pub?output=csv"
    df = pd.read_csv(url)
    # Limpa nomes de colunas (remove quebras de linha e espaços extras)
    df.columns = [col.replace('\n', ' ').strip() for col in df.columns]
    return df

def main():
    st.sidebar.title("Menu de Navegação")
    df = load_data()

    if df is not None:
        menu = st.sidebar.radio("Ir para:", ["Dashboard Geral", "Perfil Individual", "Tabela de Dados"])

        if menu == "Dashboard Geral":
            st.title("📊 Painel Geral de Residentes - 2026")
            
            # Métricas
            m1, m2, m3 = st.columns(3)
            m1.metric("Total de Residentes", len(df))
            m2.metric("UBSs Diferentes", df['UBS:'].nunique())
            m3.metric("Equipes Atendidas", df['Equipe:'].nunique())

            st.divider()
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Distribuição por UBS")
                fig_ubs = px.pie(df, names='UBS:', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_ubs, use_container_width=True)
            
            with c2:
                st.subheader("Top Experiências Prévias")
                # Analisa a coluna de Atenção à Saúde (múltipla escolha separada por vírgula)
                if 'Atenção à saúde' in df.columns:
                    skills = df['Atenção à saúde'].str.split(',').explode().str.strip()
                    fig_skills = px.bar(skills.value_counts().head(8), orientation='h', color_discrete_sequence=['#4c78a8'])
                    st.plotly_chart(fig_skills, use_container_width=True)

            if st.button("📥 Exportar PDF com Lista Geral"):
                pdf_geral = build_synthesis_pdf(df)
                st.download_button("Clique aqui para baixar", pdf_geral, "relatorio_geral_2026.pdf", "application/pdf")

        elif menu == "Perfil Individual":
            st.title("👤 Diagnóstico por Residente")
            residente_nome = st.selectbox("Selecione o(a) Residente:", df['Nome:'].unique())
            
            row = df[df['Nome:'] == residente_nome].iloc[0]

            col_inf1, col_inf2 = st.columns([1, 2])
            with col_inf1:
                st.success(f"**UBS:** {row['UBS:']}\n\n**Equipe:** {row['Equipe:']}")
                st.write(f"**Formação:** {row['Instituição de Ensino em que se graduou:']} ({row['Ano de Graduação:']})")
                
                # Botão de exportação PDF
                pdf_res = build_resident_pdf(row)
                st.download_button(f"📥 Exportar PDF de {residente_nome}", pdf_res, f"perfil_{residente_nome}.pdf", "application/pdf")

            with col_inf2:
                st.subheader("Relatos e Motivações")
                st.markdown(f"**Por que escolheu MFC?**\n{row['Por que escolheu MFC?']}")
                st.divider()
                st.markdown(f"**Núcleo MFC (Demandas):**\n{row.get('Núcleo MFC', 'Não informado')}")

        elif menu == "Tabela de Dados":
            st.title("📑 Visualização dos Dados Brutos")
            st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()
