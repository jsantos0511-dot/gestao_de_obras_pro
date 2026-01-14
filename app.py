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

# CSS PARA MENU MANUAL (HORIZONTAL TOTAL)
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 0.5rem !important; }
    
    /* Container do Menu Manual */
    .nav-container {
        display: flex;
        justify-content: center;
        gap: 20px; /* AJUSTE AQUI O ESPAÇO ENTRE OS ITENS */
        margin-bottom: 15px;
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
    }

    /* Estilo dos botões invisíveis do Streamlit para sobrepor o menu */
    div.stButton > button {
        background-color: transparent !important;
        border: none !important;
        color: #333 !important;
        font-size: 11px !important;
        font-weight: bold !important;
        text-transform: uppercase;
        padding: 0 !important;
        width: 80px !important; /* Largura fixa para cada item */
        height: 50px !important;
    }
    
    .header-box { text-align: center; margin-bottom: 5px; }
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

# --- NAVEGAÇÃO MANUAL (3 ITENS LADO A LADO) ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'RESUMO'

# Criamos uma linha horizontal real usando colunas com largura mínima
c1, c2, c3 = st.columns([1,1,1])

with c1:
    if st.button("👷\nOBRAS", use_container_width=True): 
        st.session_state.pagina = 'OBRA'
        st.rerun()
with c2:
    if st.button("💸\nGASTO", use_container_width=True): 
        st.session_state.pagina = 'GASTO'
        st.rerun()
with c3:
    if st.button("📋\nLISTA", use_container_width=True): 
        st.session_state.pagina = 'LISTA'
        st.rerun()

# --- TELAS ---
pag = st.session_state.pagina

# Botão Voltar (Apenas nas páginas internas)
if pag != 'RESUMO':
    st.markdown("---")
    if st.button("⬅️ VOLTAR PARA RESUMO"):
        st.session_state.pagina = 'RESUMO'
        st.rerun()

# --- CONTEÚDO ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

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
