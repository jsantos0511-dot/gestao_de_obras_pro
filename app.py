import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os

# --- CONFIGURAÇÕES DO BANCO ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ROSECON Engenharia", layout="centered")

# CSS para botões grandes e esconder menus nativos
st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stHeader"] {display: none;}
    .stButton>button {
        width: 100%;
        height: 80px;
        font-size: 20px;
        font-weight: bold;
        border-radius: 15px;
        margin-bottom: 10px;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #007bff;
        color: #333;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOGOMARCA (Com verificação de erro) ---
if os.path.exists("LOGOMARCA.jpeg"):
    st.image("LOGOMARCA.jpeg", use_container_width=True)
else:
    st.title("ROSECON ENGENHARIA")

# --- LÓGICA DE NAVEGAÇÃO ---
if 'tela' not in st.session_state:
    st.session_state.tela = 'home'

def mudar_tela(nome):
    st.session_state.tela = nome
    st.rerun()

# --- FUNÇÕES DE DADOS ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- RENDERIZAÇÃO ---

# Botão Voltar (aparece em todas as telas exceto na home)
if st.session_state.tela != 'home':
    if st.button("⬅️ VOLTAR AO MENU"):
        mudar_tela('home')

# 🏠 TELA PRINCIPAL
if st.session_state.tela == 'home':
    st.write("### Painel de Gestão")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 RESUMO"): mudar_tela('dash')
        if st.button("📋 LISTAR"): mudar_tela('hist')
    with col2:
        if st.button("💸 GASTO"): mudar_tela('gasto')
        if st.button("⚙️ OBRAS"): mudar_tela('config')

# 📊 DASHBOARD
elif st.session_state.tela == 'dash':
    st.subheader("Resumo Financeiro")
    obras = listar_obras()
    if obras:
        nome_obra = st.selectbox("Selecione a Obra", list(obras.keys()))
        id_obra = obras[nome_obra]
        
        # Totais
        obra_info = supabase.table("obras").select("*").eq("id", id_obra).single().execute().data
        res_soma = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_obra}).execute()
        
        total_gasto = sum(float(item['total']) for item in res_soma.data) if res_soma.data else 0
        orcamento = float(obra_info['orcamento_previsto'])
        
        st.markdown(f"""
            <div class="metric-card">
                <small>Orçamento: R$ {orcamento:,.2f}</small><br>
                <b style="font-size:1.5em; color:red">Gasto: R$ {total_gasto:,.2f}</b><br>
                <small style="color:green">Saldo: R$ {(orcamento - total_gasto):,.2f}</small>
            </div>
        """, unsafe_allow_html=True)
        
        if res_soma.data:
            df = pd.DataFrame(res_soma.data)
            st.bar_chart(df.set_index('nome_categoria'))

# 💸 LANÇAR GASTO
elif st.session_state.tela == 'gasto':
    st.subheader("Novo Lançamento")
    obras = listar_obras()
    cats = listar_categorias()
    if obras:
        with st.form("f_gasto"):
            o = st.selectbox("Obra", list(obras.keys()))
            c = st.selectbox("Categoria", list(cats.keys()))
            d = st.text_input("Descrição")
            v = st.number_input("Valor (R$)", min_value=0.0)
            if st.form_submit_button("SALVAR"):
                supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v}).execute()
                st.success("Registrado!")
                mudar_tela('home')

# 📋 HISTÓRICO
elif st.session_state.tela == 'hist':
    st.subheader("Histórico Detalhado")
    obras = listar_obras()
    if obras:
        o_sel = st.selectbox("Obra", list(obras.keys()))
        gastos = supabase.table("lancamentos_obra").select("id, data_gasto, descricao, valor").eq("obra_id", obras[o_sel]).order("data_gasto", desc=True).execute().data
        for g in gastos:
            with st.expander(f"{g['data_gasto']} - {g['descricao']}"):
                st.write(f"Valor: R$ {g['valor']}")
                if st.button("Excluir", key=g['id']):
                    supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute()
                    st.rerun()

# ⚙️ CONFIGURAÇÕES
elif st.session_state.tela == 'config':
    st.subheader("Gerenciar Obras")
    with st.form("f_obra"):
        n = st.text_input("Nome da Obra")
        v = st.number_input("Orçamento Previsto", min_value=0.0)
        if st.form_submit_button("CADASTRAR OBRA"):
            supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
            st.success("Obra cadastrada!")
