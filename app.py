import streamlit as st
import pandas as pd
import plotly.express as px
from gerar_pdfs_rmfc import build_resident_pdf, build_synthesis_pdf

st.set_page_config(page_title="Gestão RMFC 2026", layout="wide", page_icon="🏥")

@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQR-KEmCfdmmAHhC_Y2GQe1MjDb5y1w6Qbg1GQmHiPCswIIIUctw7erzDH1xFqwLoWCOd5cLu552JNM/pub?output=csv"
    df = pd.read_csv(url)
    # Limpeza rigorosa de nomes de colunas
    df.columns = [col.replace('\n', ' ').strip() for col in df.columns]
    return df

def main():
    st.sidebar.title("Navegação")
    df = load_data()

    if df is not None:
        aba = st.sidebar.radio("Escolha a visão:", ["Painel Geral", "Ficha do Residente", "Dados Brutos"])

        if aba == "Painel Geral":
            st.title("📊 Visão Geral da Turma 2026")
            
            # Gráficos de competências
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Experiências em Atenção à Saúde")
                all_skills = df['Atenção à saúde'].str.split(',').explode().str.strip()
                st.plotly_chart(px.bar(all_skills.value_counts(), orientation='h'), use_container_width=True)
            
            with col2:
                st.subheader("Experiência na Rede")
                rede_skills = df['Rede'].str.split(',').explode().str.strip()
                st.plotly_chart(px.bar(rede_skills.value_counts(), orientation='h', color_discrete_sequence=['orange']), use_container_width=True)

            if st.button("📥 Baixar PDF com Lista Geral"):
                st.download_button("Clique para baixar", build_synthesis_pdf(df), "lista_residentes.pdf", "application/pdf")

        elif aba == "Ficha do Residente":
            st.title("👤 Detalhes do Residente")
            nome = st.selectbox("Selecione o nome:", df['Nome:'].unique())
            res = df[df['Nome:'] == nome].iloc[0]

            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn2:
                # Botão PDF
                pdf_res = build_resident_pdf(res)
                st.download_button(f"📥 Exportar PDF de {nome}", pdf_res, f"diagnostico_{nome}.pdf", "application/pdf")

            # Exibição organizada de TODOS os campos
            with st.expander("📌 Identificação e Graduação", expanded=True):
                c1, c2, c3 = st.columns(3)
                c1.write(f"**UBS:** {res['UBS:']}")
                c1.write(f"**Equipe:** {res['Equipe:']}")
                c2.write(f"**Instituição:** {res['Instituição de Ensino em que se graduou:']}")
                c2.write(f"**Ano:** {res['Ano de Graduação:']}")
                c3.write(f"**Telefone:** {res['Telefone:']}")
                c3.write(f"**Email:** {res['Email da residente:']}")

            with st.expander("💡 Motivação e Experiência Prévia", expanded=True):
                st.write(f"**Por que escolheu MFC?**\n{res['Por que escolheu MFC?']}")
                st.divider()
                st.write(f"**Experiência Profissional Prévia:**\n{res['Experiência profissional prévia:']}")

            with st.expander("🛠️ Práticas de APS e Gestão"):
                st.write(f"**Reunião de Equipe:** {res['Reunião de equipe']}")
                st.write(f"**Acolhimento:** {res['Acolhimento']}")
                st.write(f"**Gestão da Agenda:** {res['Gestão da agenda']}")
                st.write(f"**Ações de Planejamento:** {res['Ações de planejamento (marque ações)']}")
                st.write(f"**E-multi/Intersetorial:** {res['NASF-E-multi-Intersetorial']}")

            with st.expander("🩺 Clínica e Rede"):
                st.write(f"**Atenção à Saúde:** {res['Atenção à saúde']}")
                st.write(f"**Rede:** {res['Rede']}")
                st.info(f"**Relatos da Conversa:**\n{res['Relatos/fatos específicos que gostaria de relatar a partir da conversa']}")

            with st.expander("📚 Demandas de Aprendizado"):
                st.write(f"**Núcleo MFC:** {res['Núcleo MFC']}")
                st.write(f"**Saúde Coletiva:** {res['Campo Saúde Coletiva (Gestão do Cuidado, Processo de Trabalho, Epidemio, etc.)']}")
                st.warning(f"**Diagnóstico Inicial / Observações:**\n{res['Se quiser adicionar informações relevantes sobre a conversa e o diagnóstico inicial, para termos em comum, pode utilizar esse espaço']}")

        elif aba == "Dados Brutos":
            st.dataframe(df)

if __name__ == "__main__":
    main()
