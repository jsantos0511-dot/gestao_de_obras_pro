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

# CSS para Menu Inferior e Estilo Clean
st.markdown("""
    <style>
    /* Esconde menus nativos */
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    
    /* Logomarca Pequena */
    .logo-container { text-align: center; margin-bottom: 20px; }
    .logo-img { width: 150px; }

    /* Cards de Resumo */
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #eee;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    
    /* Menu Inferior Fixo */
    .nav-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #ffffff;
        display: flex;
        justify-content: space-around;
        padding: 10px 0;
        border-top: 1px solid #ddd;
        z-index: 999;
    }
    </style>
""", unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = '📊'

# --- TOPO: LOGOMARCA REDUZIDA ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
if os.path.exists("LOGOMARCA.jpeg"):
    st.image("LOGOMARCA.jpeg", width=180) # Tamanho reduzido
else:
    st.subheader("ROSECON")
st.markdown('</div>', unsafe_allow_html=True)

# --- FUNÇÕES ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- CONTEÚDO ---
pag = st.session_state.pagina

if pag == '📊':
    st.write("### Resumo")
    obras = listar_obras()
    if obras:
        o_nome = st.selectbox("Obra", list(obras.keys()), label_visibility="collapsed")
        id_o = obras[o_nome]
        
        info = supabase.table("obras").select("*").eq("id", id_o).single().execute().data
        res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_o}).execute()
        
        gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
        orc = float(info['orcamento_previsto'])
        
        st.markdown(f"""
            <div class="metric-card">
                <p style="margin:0; color:#666;">Gasto Total</p>
                <h2 style="margin:0; color:#d32f2f;">R$ {gasto:,.2f}</h2>
                <p style="margin:0; color:#2e7d32; font-size:14px;">Saldo: R$ {(orc-gasto):,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if res_s.data:
            st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

elif pag == '➕':
    st.write("### Novo Gasto")
    obras, cats = listar_obras(), listar_categorias()
    with st.form("f", clear_on_submit=True):
        o = st.selectbox("Obra", list(obras.keys()))
        c = st.selectbox("Categoria", list(cats.keys()))
        d = st.text_input("Descrição")
        v = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("SALVAR GASTO"):
            supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v}).execute()
            st.success("Salvo!")

elif pag == '📋':
    st.write("### Histórico")
    obras = listar_obras()
    if obras:
        o_sel = st.selectbox("Filtrar Obra", list(obras.keys()))
        dados = supabase.table("lancamentos_obra").select("id, descricao, valor").eq("obra_id", obras[o_sel]).execute().data
        for d in dados:
            with st.expander(f"{d['descricao']} - R$ {d['valor']}"):
                if st.button("Excluir", key=d['id']):
                    supabase.table("lancamentos_obra").delete().eq("id", d['id']).execute()
                    st.rerun()

elif pag == '⚙️':
    st.write("### Configurações")
    n = st.text_input("Nova Obra")
    v = st.number_input("Orçamento", min_value=0.0)
    if st.button("Cadastrar"):
        supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
        st.success("Obra criada!")

# Espaço extra para não cobrir o conteúdo com o menu
st.markdown("<br><br><br>", unsafe_allow_html=True)

# --- MENU INFERIOR FIXO ---
# Usamos colunas para simular os ícones de app
c1, c2, c3, c4 = st.columns(4)
with c1: 
    if st.button("📊"): st.session_state.pagina = '📊'; st.rerun()
with c2: 
    if st.button("➕"): st.session_state.pagina = '➕'; st.rerun()
with c3: 
    if st.button("📋"): st.session_state.pagina = '📋'; st.rerun()
with c4: 
    if st.button("⚙️"): st.session_state.pagina = '⚙️'; st.rerun()
