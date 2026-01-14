import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURAÇÕES ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- ESTILIZAÇÃO PARA MENU COMPACTO ---
st.set_page_config(page_title="Obras Pro", layout="centered")

st.markdown("""
    <style>
    /* Estilo para os botões de navegação superiores */
    .stButton > button {
        border-radius: 20px;
        height: 2.5em;
        font-weight: bold;
    }
    .metric-card {
        background-color: #161b22;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE NAVEGAÇÃO (Estado da Sessão) ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'Dashboard'

# Criando o menu horizontal com botões
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    if st.button("📊 Resumo"): st.session_state.pagina = 'Dashboard'
with col_m2:
    if st.button("💸 Gasto"): st.session_state.pagina = 'Lançar'
with col_m3:
    if st.button("⚙️ Obra"): st.session_state.pagina = 'Config'

st.divider()

# --- FUNÇÕES ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- RENDERIZAÇÃO DAS TELAS ---

if st.session_state.pagina == 'Dashboard':
    st.subheader("Dashboard Financeiro")
    obras_dict = listar_obras()
    if obras_dict:
        obra_nome = st.selectbox("Selecione a Obra", list(obras_dict.keys()))
        id_obra = obras_dict[obra_nome]
        
        # Dados da Obra
        obra_info = supabase.table("obras").select("*").eq("id", id_obra).single().execute().data
        gastos = supabase.table("lancamentos_obra").select("valor").eq("obra_id", id_obra).execute().data
        
        total_gasto = sum(float(item['valor']) for item in gastos)
        orcamento = float(obra_info['orcamento_previsto'])
        
        # Cards de Resumo
        st.markdown(f"""
            <div class="metric-card">
                <small>Investimento: R$ {orcamento:,.2f}</small><br>
                <span style="font-size: 1.2em;">Gasto: <b style="color:#f85149">R$ {total_gasto:,.2f}</b></span><br>
                <span style="font-size: 0.9em; color:#8b949e;">Saldo: R$ {(orcamento - total_gasto):,.2f}</span>
            </div>
        """, unsafe_allow_html=True)
        
        if total_gasto > 0:
            res_gastos = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_obra}).execute()
            if res_gastos.data:
                df = pd.DataFrame(res_gastos.data)
                st.bar_chart(df.set_index('nome_categoria'))

elif st.session_state.pagina == 'Lançar':
    st.subheader("Novo Lançamento")
    obras_dict = listar_obras()
    cats_dict = listar_categorias()
    
    if obras_dict:
        with st.form("gasto_form", clear_on_submit=True):
            obra = st.selectbox("Obra", list(obras_dict.keys()))
            cat = st.selectbox("Categoria", list(cats_dict.keys()))
            desc = st.text_input("Descrição")
            val = st.number_input("Valor (R$)", min_value=0.0)
            
            if st.form_submit_button("Salvar Registro"):
                if desc and val > 0:
                    payload = {
                        "obra_id": obras_dict[obra],
                        "categoria_id": cats_dict[cat],
                        "descricao": desc,
                        "valor": val
                    }
                    supabase.table("lancamentos_obra").insert(payload).execute()
                    st.success("Salvo!")
                else:
                    st.error("Preencha os campos.")

elif st.session_state.pagina == 'Config':
    st.subheader("Configurações")
    with st.expander("Cadastrar Nova Obra"):
        n_obra = st.text_input("Nome")
        v_obra = st.number_input("Orçamento", min_value=0.0)
        if st.button("Criar"):
            supabase.table("obras").insert({"nome_obra": n_obra, "orcamento_previsto": v_obra}).execute()
            st.rerun()
