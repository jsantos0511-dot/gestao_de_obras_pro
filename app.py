import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURAÇÕES ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ROSECON Engenharia", layout="centered")

# CSS Personalizado para Botões Estilo App e Esconder Menu Nativo
st.markdown("""
    <style>
    /* Esconde o menu lateral nativo e o cabeçalho padrão */
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stHeader"] {display: none;}
    
    .main-button {
        background-color: #f0f2f6;
        border: 2px solid #000;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin-bottom: 10px;
        cursor: pointer;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #ddd;
        color: #000;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE NAVEGAÇÃO ---
if 'tela' not in st.session_state:
    st.session_state.tela = 'home'

def mudar_tela(nome_tela):
    st.session_state.tela = nome_tela

# --- CABEÇALHO COM LOGO ---
st.image("LOGOMARCA.jpeg", use_container_width=True)
st.divider()

# --- INTERFACE DE NAVEGAÇÃO (BOTÕES) ---
if st.session_state.tela != 'home':
    if st.button("⬅️ Voltar ao Menu Principal"):
        mudar_tela('home')
        st.rerun()

# --- FUNÇÕES DE BANCO ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

# --- RENDERIZAÇÃO DAS TELAS ---

if st.session_state.tela == 'home':
    st.subheader("O que deseja fazer hoje?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 RESUMO\nFINANCEIRO"): mudar_tela('dash')
    with col2:
        if st.button("💸 LANÇAR\nNOVO GASTO"): mudar_tela('gasto')
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("📋 VER\nHISTÓRICO"): mudar_tela('hist')
    with col4:
        if st.button("⚙️ CONFIG.\nOBRAS"): mudar_tela('config')

elif st.session_state.tela == 'dash':
    st.header("📊 Resumo Financeiro")
    obras_dict = listar_obras()
    if obras_dict:
        obra_nome = st.selectbox("Selecione a Obra", list(obras_dict.keys()))
        # ... (Restante da lógica do Dashboard que já fizemos)
        st.info("Aqui aparecerá o gráfico de gastos da ROSECON.")

elif st.session_state.tela == 'gasto':
    st.header("💸 Novo Lançamento")
    obras_dict = listar_obras()
    if obras_dict:
        with st.form("gasto_form"):
            st.selectbox("Obra", list(obras_dict.keys()))
            st.text_input("Descrição do Material")
            st.number_input("Valor (R$)")
            if st.form_submit_button("REGISTRAR"):
                st.success("Salvo com sucesso!")

elif st.session_state.tela == 'hist':
    st.header("📋 Histórico de Obras")
    st.write("Lista de gastos detalhados aqui.")

elif st.session_state.tela == 'config':
    st.header("⚙️ Configurações de Obra")
    with st.expander("Cadastrar Nova Obra"):
        st.text_input("Nome da Obra")
        st.button("Salvar")
