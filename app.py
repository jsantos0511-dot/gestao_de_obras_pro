import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os

# --- CONEXÃO ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ROSECON", layout="centered")

# CSS Avançado para Design de App
st.markdown("""
    <style>
    /* Esconde elementos padrão */
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    
    /* Container da Logo */
    .logo-box { text-align: center; padding: 10px 0; margin-top: -40px; }
    
    /* Menu Estilo Segmentado */
    .stSelectbox label { display: none; } /* Esconde label do seletor se usado */
    
    div.stButton > button {
        border: none;
        background-color: transparent;
        color: #666;
        font-weight: 500;
        border-bottom: 2px solid transparent;
        border-radius: 0px;
        height: 50px;
        transition: 0.3s;
    }
    
    div.stButton > button:hover, div.stButton > button:focus {
        color: #007bff;
        border-bottom: 2px solid #007bff;
        background-color: transparent;
    }

    /* Cards de Informação */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f1f4f9 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin: 10px 0;
        border: 1px solid #e1e4e8;
    }
    </style>
""", unsafe_allow_html=True)

# --- TOPO: LOGO ---
st.markdown('<div class="logo-box">', unsafe_allow_html=True)
if os.path.exists("LOGOMARCA.jpeg"):
    st.image("LOGOMARCA.jpeg", width=180)
else:
    st.title("ROSECON")
st.markdown('</div>', unsafe_allow_html=True)

# --- NAVEGAÇÃO SEGMENTADA ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'RESUMO'

# Barra de navegação horizontal slim
m1, m2, m3, m4 = st.columns(4)
with m1:
    if st.button("📊\nRESUMO"): st.session_state.pagina = 'RESUMO'; st.rerun()
with m2:
    if st.button("💸\nGASTO"): st.session_state.pagina = 'GASTO'; st.rerun()
with m3:
    if st.button("📋\nLISTA"): st.session_state.pagina = 'LISTA'; st.rerun()
with m4:
    if st.button("⚙️\nOBRA"): st.session_state.pagina = 'OBRA'; st.rerun()

st.markdown("---")

# --- LÓGICA DE DADOS ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

# --- PÁGINAS ---
pag = st.session_state.pagina

if pag == 'RESUMO':
    obras = listar_obras()
    if obras:
        o_nome = st.selectbox("Obra", list(obras.keys()))
        id_o = obras[o_nome]
        
        info = supabase.table("obras").select("*").eq("id", id_o).single().execute().data
        res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_o}).execute()
        
        gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
        orc = float(info['orcamento_previsto'])
        
        st.markdown(f"""
            <div class="metric-card">
                <p style="color:#666; font-size:14px; margin:0;">Status Financeiro</p>
                <h3 style="margin:5px 0; color:#1a1a1a;">R$ {gasto:,.2f}</h3>
                <p style="color:#28a745; font-size:12px; margin:0;">Disponível: R$ {(orc-gasto):,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if res_s.data:
            df = pd.DataFrame(res_s.data)
            st.bar_chart(df.set_index('nome_categoria'))

elif pag == 'GASTO':
    st.subheader("Novo Registro")
    obras = listar_obras()
    # Puxa categorias cadastradas
    res_cat = supabase.table("categorias_obra").select("id, nome_categoria").execute()
    cats = {c['nome_categoria']: c['id'] for c in res_cat.data}
    
    with st.form("form_clean", clear_on_submit=True):
        o = st.selectbox("Selecione a Obra", list(obras.keys()))
        c = st.selectbox("Categoria", list(cats.keys()))
        d = st.text_input("Descrição do Material")
        v = st.number_input("Valor Pago", min_value=0.0)
        if st.form_submit_button("CONCLUIR LANÇAMENTO"):
            supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v}).execute()
            st.success("Lançado com sucesso!")

elif pag == 'LISTA':
    st.subheader("Histórico de Gastos")
    obras = listar_obras()
    if obras:
        o_sel = st.selectbox("Filtrar Obra", list(obras.keys()))
        dados = supabase.table("lancamentos_obra").select("id, descricao, valor").eq("obra_id", obras[o_sel]).execute().data
        for d in dados:
            st.markdown(f"""
                <div style="padding:10px; border-bottom:1px solid #eee; display:flex; justify-content:space-between;">
                    <span>{d['descricao']}</span>
                    <b>R$ {d['valor']:,.2f}</b>
                </div>
            """, unsafe_allow_html=True)

elif pag == 'OBRA':
    st.subheader("Nova Obra")
    with st.form("nova"):
        n = st.text_input("Nome do Projeto")
        v = st.number_input("Orçamento Previsto", min_value=0.0)
        if st.form_submit_button("CADASTRAR"):
            supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
            st.rerun()
