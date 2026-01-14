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
st.set_page_config(page_title="ROSECON Pro", layout="centered")

# CSS para replicar o estilo da imagem (Menu em blocos, Cards Modernos)
st.markdown("""
    <style>
    /* Esconde elementos nativos */
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    
    /* Fundo e Container */
    .main { background-color: #f4f7f9; }
    
    /* Estilo dos Botões do Menu (Blocos Escuros) */
    div.stButton > button {
        background-color: #262730;
        color: white;
        border-radius: 10px;
        height: 60px;
        font-weight: bold;
        border: none;
        margin-bottom: 5px;
        transition: 0.3s;
    }
    
    div.stButton > button:hover {
        background-color: #40414f;
        border: 1px solid #007bff;
    }

    /* Título Rosecon */
    .company-header {
        font-family: 'Arial Black', sans-serif;
        font-size: 24px;
        color: #1a1a1a;
        text-align: center;
        margin-top: -40px;
        margin-bottom: 20px;
    }

    /* Cards de Histórico e Dashboard */
    .data-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 1px solid #eef2f6;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
if os.path.exists("LOGOMARCA.jpeg"):
    st.image("LOGOMARCA.jpeg", width=220)
else:
    st.markdown('<div class="company-header">ROSECON</div>', unsafe_allow_html=True)

# --- NAVEGAÇÃO (Seguindo a imagem: RESUMO, GASTO, LISTA, OBRA) ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'RESUMO'

m1, m2, m3, m4 = st.columns(4)
with m1:
    if st.button("📊\nRESUMO"): st.session_state.pagina = 'RESUMO'; st.rerun()
with m2:
    if st.button("💸\nGASTO"): st.session_state.pagina = 'GASTO'; st.rerun()
with m3:
    if st.button("📋\nLISTA"): st.session_state.pagina = 'LISTA'; st.rerun()
with m4:
    if st.button("👷\nOBRA"): st.session_state.pagina = 'OBRA'; st.rerun()

st.markdown("---")

# --- FUNÇÕES ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

# --- PÁGINAS ---
pag = st.session_state.pagina

if pag == 'RESUMO':
    st.markdown("### 📈 Dashboard Financeiro")
    obras = listar_obras()
    if obras:
        o_nome = st.selectbox("Selecione a Obra", list(obras.keys()))
        id_o = obras[o_nome]
        
        info = supabase.table("obras").select("*").eq("id", id_o).single().execute().data
        res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_o}).execute()
        
        gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
        orc = float(info['orcamento_previsto'])
        
        st.markdown(f"""
            <div class="data-card">
                <p style="color:#888; margin:0;">Investimento Total: R$ {orc:,.2f}</p>
                <h2 style="color:#d32f2f; margin:5px 0;">Gasto: R$ {gasto:,.2f}</h2>
                <p style="color:#2e7d32; font-weight:bold;">Saldo: R$ {(orc-gasto):,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if res_s.data:
            df = pd.DataFrame(res_s.data)
            st.bar_chart(df.set_index('nome_categoria'))

elif pag == 'GASTO':
    st.markdown("### 💸 Registrar Novo Gasto")
    obras = listar_obras()
    res_cat = supabase.table("categorias_obra").select("id, nome_categoria").execute()
    cats = {c['nome_categoria']: c['id'] for c in res_cat.data}
    
    with st.container():
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        with st.form("form_obra", clear_on_submit=True):
            o = st.selectbox("Obra", list(obras.keys()))
            c = st.selectbox("Categoria", list(cats.keys()))
            d = st.text_input("Descrição (Ex: Cimento CP-II)")
            v = st.number_input("Valor do Lançamento", min_value=0.0)
            if st.form_submit_button("CADASTRAR GASTO"):
                supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v}).execute()
                st.success("Lançado!")
        st.markdown('</div>', unsafe_allow_html=True)

elif pag == 'LISTA':
    st.markdown("### 📋 Histórico de Gastos")
    obras = listar_obras()
    if obras:
        o_sel = st.selectbox("Filtrar por Obra", list(obras.keys()))
        dados = supabase.table("lancamentos_obra").select("id, descricao, valor, data_gasto").eq("obra_id", obras[o_sel]).order("data_gasto", desc=True).execute().data
        for d in dados:
            st.markdown(f"""
                <div style="background:white; padding:15px; border-radius:10px; margin-bottom:10px; border:1px solid #eee; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <small style="color:#999;">{d['data_gasto']}</small><br>
                        <b>{d['descricao']}</b>
                    </div>
                    <b style="color:#d32f2f;">R$ {d['valor']:,.2f}</b>
                </div>
            """, unsafe_allow_html=True)

elif pag == 'OBRA':
    st.markdown("### 👷 Configurar Nova Obra")
    with st.container():
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        n = st.text_input("Nome do Empreendimento")
        v = st.number_input("Orçamento Planejado", min_value=0.0)
        if st.button("SALVAR OBRA"):
            supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
