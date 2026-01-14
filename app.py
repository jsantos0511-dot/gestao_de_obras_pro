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

# CSS PARA DIMINUIR ESPAÇO ENTRE ITENS
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 0.5rem !important; }
    
    /* REMOVE O ESPAÇAMENTO ENTRE COLUNAS (GAP) */
    [data-testid="stHorizontalBlock"] {
        gap: 0rem !important;
        display: flex !important;
        justify-content: center !important; /* Centraliza o bloco do menu */
    }

    /* AJUSTA A LARGURA DAS COLUNAS PARA FICAREM PRÓXIMAS */
    [data-testid="column"] {
        width: fit-content !important;
        flex: 0 1 auto !important;
        min-width: 80px !important; /* Define uma largura mínima pequena */
        padding: 0px !important;
        margin: 0px -5px !important; /* Margem negativa para aproximar ainda mais */
    }
    
    div.stButton > button {
        border: none !important;
        background-color: transparent !important;
        color: #333 !important;
        font-size: 11px !important;
        font-weight: bold !important;
        padding: 0px !important;
        text-transform: uppercase;
        width: 100%;
    }

    .header-box { text-align: center; margin-bottom: 2px; }
    .data-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #eee;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<div class="header-box">', unsafe_allow_html=True)
if os.path.exists("LOGOMARCA.jpeg"):
    st.image("LOGOMARCA.jpeg", width=130)
else:
    st.markdown("<h4 style='margin:0;'>ROSECON</h4>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- NAVEGAÇÃO (3 ITENS JUNTINHOS) ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'RESUMO'

# Criando colunas e forçando a aproximação
m1, m2, m3 = st.columns(3)
with m1:
    if st.button("👷\nOBRAS"): st.session_state.pagina = 'OBRA'; st.rerun()
with m2:
    if st.button("💸\nGASTO"): st.session_state.pagina = 'GASTO'; st.rerun()
with m3:
    if st.button("📋\nLISTA"): st.session_state.pagina = 'LISTA'; st.rerun()

st.markdown("<hr style='margin:2px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

# --- RESTANTE DAS FUNÇÕES (IGUAL ANTERIOR) ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

pag = st.session_state.pagina

if pag != 'RESUMO':
    if st.button("⬅️ VOLTAR PARA RESUMO"):
        st.session_state.pagina = 'RESUMO'
        st.rerun()

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
                <h2 style="margin:0; color:#e63946;">{formatar_real(gasto)}</h2>
                <div style="display:flex; justify-content:space-between; margin-top:10px; border-top:1px solid #eee; padding-top:8px;">
                    <div><small><b>ORÇADO</b></small><br>{formatar_real(orc)}</div>
                    <div style="text-align:right;"><small><b>SALDO</b></small><br>{formatar_real(orc-gasto)}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if res_s.data:
            st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

elif pag == 'OBRA':
    st.write("##### 👷 Nova Obra")
    with st.form("n"):
        n = st.text_input("Nome")
        v = st.number_input("Verba", min_value=0.0)
        if st.form_submit_button("SALVAR"):
            supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
            st.session_state.pagina = 'RESUMO'
            st.rerun()

elif pag == 'GASTO':
    st.write("##### 💸 Lançar Gasto")
    obras, cats = listar_obras(), listar_categorias()
    with st.form("g"):
        o = st.selectbox("Obra", list(obras.keys()))
        c = st.selectbox("Categoria", list(cats.keys()))
        d = st.text_input("Descrição")
        v = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("LANÇAR"):
            supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v}).execute()
            st.session_state.pagina = 'RESUMO'
            st.rerun()

elif pag == 'LISTA':
    st.write("##### 📋 Histórico")
    obras = listar_obras()
    if obras:
        o_sel = st.selectbox("Filtrar:", list(obras.keys()))
        dados = supabase.table("lancamentos_obra").select("id, descricao, valor").eq("obra_id", obras[o_sel]).execute().data
        for d in dados:
            st.markdown(f"<div class='data-card' style='margin-bottom:5px; padding:10px; display:flex; justify-content:space-between;'><span style='font-size:12px;'>{d['descricao']}</span><b>{formatar_real(d['valor'])}</b></div>", unsafe_allow_html=True)
