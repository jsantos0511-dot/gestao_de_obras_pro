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

# CSS Otimizado
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 0.5rem !important; }
    .header-box { text-align: center; margin-bottom: 5px; }

    /* Menu de 3 Itens - Mais espaço para os dedos */
    div.stButton > button {
        border: none !important;
        background-color: transparent !important;
        color: #444 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        padding: 5px 0px !important;
        width: 100% !important;
        text-transform: uppercase;
    }
    
    .data-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #eee;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-top: 10px;
    }

    /* Botão Voltar Especial */
    .btn-voltar button {
        background-color: #f8f9fa !important;
        border: 1px solid #ddd !important;
        border-radius: 8px !important;
        height: 35px !important;
        margin-bottom: 15px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<div class="header-box">', unsafe_allow_html=True)
if os.path.exists("LOGOMARCA.jpeg"):
    st.image("LOGOMARCA.jpeg", width=150)
else:
    st.markdown("<h4 style='margin:0;'>ROSECON</h4>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- LÓGICA DE NAVEGAÇÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'RESUMO'

# MENU DE 3 ITENS (Obras em primeiro)
m1, m2, m3 = st.columns(3)
with m1:
    if st.button("👷\nOBRAS"): st.session_state.pagina = 'OBRA'; st.rerun()
with m2:
    if st.button("💸\nGASTO"): st.session_state.pagina = 'GASTO'; st.rerun()
with m3:
    if st.button("📋\nLISTA"): st.session_state.pagina = 'LISTA'; st.rerun()

st.markdown("<hr style='margin:5px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

# --- FUNÇÕES ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- RENDERIZAÇÃO ---
pag = st.session_state.pagina

# Botão de Voltar para o Resumo (Aparece em todas menos no próprio resumo)
if pag != 'RESUMO':
    st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
    if st.button("⬅️ VOLTAR PARA RESUMO"):
        st.session_state.pagina = 'RESUMO'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if pag == 'RESUMO':
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
                <small style="color:#888;">GASTO ACUMULADO</small>
                <h2 style="margin:0; color:#e63946;">{formatar_real(gasto)}</h2>
                <div style="display:flex; justify-content:space-between; margin-top:10px; border-top:1px solid #eee; padding-top:8px;">
                    <div><small><b>ORÇADO</b></small><br>{formatar_real(orc)}</div>
                    <div style="text-align:right;"><small><b>SALDO</b></small><br>{formatar_real(orc-gasto)}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if res_s.data:
            st.write("---")
            st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))
    else:
        st.info("Toque em 'OBRAS' para cadastrar seu primeiro projeto.")

elif pag == 'OBRA':
    st.write("### 👷 Gestão de Obras")
    with st.form("nova_obra"):
        n = st.text_input("Nome do Empreendimento")
        v = st.number_input("Orçamento Planejado (R$)", min_value=0.0)
        if st.form_submit_button("CADASTRAR NOVA OBRA"):
            supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
            st.success("Obra salva!")
            st.session_state.pagina = 'RESUMO'
            st.rerun()

elif pag == 'GASTO':
    st.write("### 💸 Lançar Despesa")
    obras, cats = listar_obras(), listar_categorias()
    with st.form("f_gasto"):
        o = st.selectbox("Obra", list(obras.keys()))
        c = st.selectbox("Categoria", list(cats.keys()))
        d = st.text_input("O que foi comprado?")
        v = st.number_input("Valor pago", min_value=0.0)
        if st.form_submit_button("CONFIRMAR LANÇAMENTO"):
            supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v}).execute()
            st.success("Gasto registrado!")
            st.session_state.pagina = 'RESUMO'
            st.rerun()

elif pag == 'LISTA':
    st.write("### 📋 Histórico")
    obras = listar_obras()
    if obras:
        o_sel = st.selectbox("Filtrar por:", list(obras.keys()))
        dados = supabase.table("lancamentos_obra").select("id, descricao, valor").eq("obra_id", obras[o_sel]).execute().data
        for d in dados:
            st.markdown(f"""
                <div style="background:white; padding:12px; border-radius:8px; margin-bottom:8px; border:1px solid #eee; display:flex; justify-content:space-between;">
                    <span style="font-size:13px;">{d['descricao']}</span>
                    <b style="color:#d32f2f;">{formatar_real(d['valor'])}</b>
                </div>
            """, unsafe_allow_html=True)
