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

def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# CSS Otimizado para Celulares Estreitos
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    
    /* Remove todo o respiro superior */
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
    .header-box { text-align: center; margin-bottom: 2px; }

    /* Menu Horizontal Ultra Compacto */
    div[data-testid="column"] {
        padding: 0 !important;
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    
    div.stButton > button {
        border: none !important;
        background-color: transparent !important;
        color: #555 !important;
        font-size: 10px !important; /* Fonte reduzida para caber */
        font-weight: 700 !important;
        line-height: 1.1 !important;
        padding: 0px !important;
        width: 100% !important;
        text-transform: uppercase;
    }
    
    /* Ajuste de ícone */
    .icon-text { font-size: 16px; margin-bottom: 2px; display: block; }

    .data-card {
        background-color: white;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #eee;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<div class="header-box">', unsafe_allow_html=True)
if os.path.exists("LOGOMARCA.jpeg"):
    st.image("LOGOMARCA.jpeg", width=140)
else:
    st.markdown("<h4 style='margin:0;'>ROSECON</h4>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- NAVEGAÇÃO HORIZONTAL (FONTES REDUZIDAS) ---
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

st.markdown("<hr style='margin:2px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

# --- FUNÇÕES ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- PÁGINAS ---
pag = st.session_state.pagina

if pag == 'RESUMO':
    obras = listar_obras()
    if obras:
        o_nome = st.selectbox("Obra", list(obras.keys()), label_visibility="collapsed")
        id_o = obras[o_nome]
        info = supabase.table("obras").select("*").eq("id", id_o).single().execute().data
        res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_o}).execute()
        gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
        orc = float(info['orcamento_previsto'])
        
        st.markdown(f"""
            <div class="data-card">
                <small style="color:#888;">GASTO ACUMULADO</small>
                <h2 style="margin:0; color:#e63946; font-size:24px;">{formatar_real(gasto)}</h2>
                <div style="display:flex; justify-content:space-between; margin-top:8px; border-top:1px solid #eee; padding-top:5px;">
                    <small><b>ORÇADO:</b><br>{formatar_real(orc)}</small>
                    <small style="text-align:right;"><b>SALDO:</b><br>{formatar_real(orc-gasto)}</small>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if res_s.data:
            df = pd.DataFrame(res_s.data)
            st.bar_chart(df.set_index('nome_categoria'))

elif pag == 'GASTO':
    st.write("##### 💸 Registrar Gasto")
    obras, cats = listar_obras(), listar_categorias()
    with st.container():
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        with st.form("f_clean", clear_on_submit=True):
            o = st.selectbox("Obra", list(obras.keys()))
            c = st.selectbox("Categoria", list(cats.keys()))
            d = st.text_input("Descrição")
            v = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            if st.form_submit_button("CONCLUIR"):
                supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v}).execute()
                st.success("Salvo!")
        st.markdown('</div>', unsafe_allow_html=True)

elif pag == 'LISTA':
    st.write("##### 📋 Histórico")
    obras = listar_obras()
    if obras:
        o_sel = st.selectbox("Obra", list(obras.keys()))
        dados = supabase.table("lancamentos_obra").select("id, descricao, valor").eq("obra_id", obras[o_sel]).execute().data
        for d in dados:
            st.markdown(f"""
                <div style="background:white; padding:10px; border-radius:8px; margin-bottom:6px; border:1px solid #f0f0f0; display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:12px;">{d['descricao']}</span>
                    <b style="color:#d32f2f; font-size:12px;">{formatar_real(d['valor'])}</b>
                </div>
            """, unsafe_allow_html=True)

elif pag == 'OBRA':
    st.write("##### 👷 Nova Obra")
    with st.container():
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        n = st.text_input("Nome")
        v = st.number_input("Orçamento", min_value=0.0, step=100.0)
        if st.button("SALVAR OBRA"):
            supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
            st.success("Obra cadastrada!")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
