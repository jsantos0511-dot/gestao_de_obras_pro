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
st.set_page_config(
    page_title="ROSECON Pro", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Função para formatar moeda
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# --- CSS AVANÇADO ---
st.markdown("""
    <style>
    /* Ajuste de Topo */
    .block-container { padding-top: 1rem !important; }
    .header-box { text-align: center; margin-bottom: 15px; }
    
    /* Estilo dos Botões da Sidebar (Limpos e Sem Seleção) */
    [data-testid="stSidebar"] div.stButton > button {
        width: 100% !important;
        border: none !important;
        background-color: transparent !important;
        color: white !important;
        text-align: left !important;
        font-size: 16px !important;
        padding: 15px 10px !important;
        border-bottom: 1px solid #3d3f4b !important;
        border-radius: 0px !important;
        display: block !important;
    }

    /* Esconde o rádio invisível que usaremos para controlar o estado */
    .st-emotion-cache-1gv3f8u { display: none; }

    .data-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #eee;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE NAVEGAÇÃO ---
# Usamos o session_state para trocar as páginas
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'RESUMO'

# --- CONTEÚDO DA SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏗️ ROSECON MENU")
    
    # Ao clicar em qualquer botão, o Streamlit recarrega a página. 
    # Como a configuração inicial é 'collapsed', ele volta fechado.
    if st.button("📊 RESUMO GERAL"):
        st.session_state.pagina = 'RESUMO'
        st.rerun()
        
    if st.button("👷 GERENCIAR OBRAS"):
        st.session_state.pagina = 'OBRAS'
        st.rerun()
        
    if st.button("💸 LANÇAR GASTO"):
        st.session_state.pagina = 'GASTO'
        st.rerun()
        
    if st.button("📋 HISTÓRICO"):
        st.session_state.pagina = 'LISTA'
        st.rerun()

# --- CABEÇALHO ---
st.markdown('<div class="header-box">', unsafe_allow_html=True)
if os.path.exists("LOGOMARCA.jpeg"):
    st.image("LOGOMARCA.jpeg", width=160)
else:
    st.markdown("<h3 style='margin:0;'>ROSECON ENGENHARIA</h3>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- RENDERIZAÇÃO DAS PÁGINAS ---
pag = st.session_state.pagina

if pag == 'RESUMO':
    obras = listar_obras()
    if obras:
        o_nome = st.selectbox("Escolha a Obra", list(obras.keys()))
        id_o = obras[o_nome]
        info = supabase.table("obras").select("*").eq("id", id_o).single().execute().data
        res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_o}).execute()
        gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
        orc = float(info['orcamento_previsto'])
        
        st.markdown(f"""
            <div class="data-card">
                <small style="color:#888;">GASTO ACUMULADO</small>
                <h2 style="margin:0; color:#e63946;">{formatar_real(gasto)}</h2>
                <div style="display:flex; justify-content:space-between; margin-top:10px; border-top:1px solid #eee; padding-top:8px;">
                    <div><small><b>ORÇADO</b></small><br>{formatar_real(orc)}</div>
                    <div style="text-align:right;"><small><b>SALDO</b></small><br>{formatar_real(orc-gasto)}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if res_s.data:
            st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

elif pag == 'OBRAS':
    st.write("### 🏗️ Gestão de Obras")
    with st.form("n_obra"):
        n = st.text_input("Nome da Obra")
        v = st.number_input("Orçamento Previsto", min_value=0.0)
        if st.form_submit_button("SALVAR"):
            supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
            st.success("Obra cadastrada!")

elif pag == 'GASTO':
    st.write("### 💸 Lançar Despesa")
    obras, cats = listar_obras(), listar_categorias()
    if obras:
        with st.form("f_gasto"):
            o = st.selectbox("Obra", list(obras.keys()))
            c = st.selectbox("Categoria", list(cats.keys()))
            d = st.text_input("O que foi comprado?")
            v = st.number_input("Valor Pago", min_value=0.0)
            if st.form_submit_button("REGISTRAR GASTO"):
                supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v}).execute()
                st.success("Gasto registrado!")

elif pag == 'LISTA':
    st.write("### 📋 Histórico")
    obras = listar_obras()
    if obras:
        o_sel = st.selectbox("Filtrar por Obra:", list(obras.keys()))
        dados = supabase.table("lancamentos_obra").select("id, descricao, valor").eq("obra_id", obras[o_sel]).execute().data
        for d in dados:
            st.markdown(f"""
                <div class="data-card" style="margin-bottom:8px; display:flex; justify-content:space-between;">
                    <span>{d['descricao']}</span>
                    <b style="color:#d32f2f;">{formatar_real(d['valor'])}</b>
                </div>
            """, unsafe_allow_html=True)
