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

# --- CSS PARA FORÇAR TAMANHO DO ÍCONE ---
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 1rem !important; }
    
    /* BOTÃO HAMBÚRGUER GIGANTE */
    div.stButton > button[key="trigger"] {
        background-color: #f8f9fa !important;
        border: 2px solid #333 !important;
        width: 80px !important;  /* Aumentei a largura */
        height: 80px !important; /* Aumentei a altura */
        border-radius: 50% !important;
        margin: 0 auto 20px auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15) !important;
        transition: 0.3s;
    }

    /* FORÇANDO O TAMANHO DO TEXTO/ÍCONE DENTRO DO BOTÃO */
    div.stButton > button[key="trigger"] p {
        font-size: 40px !important; /* AQUI O ÍCONE FICA GIGANTE */
        font-weight: bold !important;
        line-height: 1 !important;
    }
    
    div.stButton > button[key="trigger"]:active {
        transform: scale(0.9); /* Efeito de clique */
    }

    /* Botões de Opção do Menu */
    .nav-button button {
        width: 100% !important;
        height: 60px !important;
        background-color: #ffffff !important;
        border: 1px solid #ddd !important;
        border-radius: 12px !important;
        font-size: 16px !important;
        font-weight: bold !important;
        margin-bottom: 10px !important;
    }

    .data-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #eee;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE ESTADO ---
if 'menu_aberto' not in st.session_state:
    st.session_state.menu_aberto = False
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'RESUMO'

# --- CABEÇALHO ---
if not st.session_state.menu_aberto:
    st.markdown('<div style="text-align:center; margin-bottom:10px;">', unsafe_allow_html=True)
    if os.path.exists("LOGOMARCA.jpeg"):
        st.image("LOGOMARCA.jpeg", width=140)
    else:
        st.markdown("<h3>ROSECON</h3>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- BOTÃO HAMBÚRGUER (SÓ O ÍCONE GIGANTE) ---
icon_menu = "×" if st.session_state.menu_aberto else "☰"
if st.button(icon_menu, key="trigger"):
    st.session_state.menu_aberto = not st.session_state.menu_aberto
    st.rerun()

# --- MENU DE OPÇÕES ---
if st.session_state.menu_aberto:
    st.markdown('<div class="nav-button">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊 RESUMO"):
            st.session_state.pagina = 'RESUMO'; st.session_state.menu_aberto = False; st.rerun()
        if st.button("💸 GASTO"):
            st.session_state.pagina = 'GASTO'; st.session_state.menu_aberto = False; st.rerun()
    with c2:
        if st.button("👷 OBRAS"):
            st.session_state.pagina = 'OBRA'; st.session_state.menu_aberto = False; st.rerun()
        if st.button("📋 LISTA"):
            st.session_state.pagina = 'LISTA'; st.session_state.menu_aberto = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

# --- CONTEÚDO DAS PÁGINAS ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

if not st.session_state.menu_aberto:
    pag = st.session_state.pagina
    
    if pag == 'RESUMO':
        obras = listar_obras()
        if obras:
            o_nome = st.selectbox("Obra Ativa", list(obras.keys()), label_visibility="collapsed")
            id_o = obras[o_nome]
            info = supabase.table("obras").select("*").eq("id", id_o).single().execute().data
            res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_o}).execute()
            gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
            orc = float(info['orcamento_previsto'])
            
            st.markdown(f"""
                <div class="data-card">
                    <small style="color:#888;">GASTO ACUMULADO</small>
                    <h2 style="margin:0; color:#e63946; font-size:32px;">{formatar_real(gasto)}</h2>
                    <div style="display:flex; justify-content:space-between; margin-top:15px; border-top:1px solid #eee; padding-top:10px;">
                        <div><small>ORÇADO</small><br><b>{formatar_real(orc)}</b></div>
                        <div style="text-align:right;"><small>SALDO</small><br><b>{formatar_real(orc-gasto)}</b></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    elif pag == 'OBRA':
        st.write("#### 👷 Nova Obra")
        with st.form("n"):
            n = st.text_input("Nome")
            v = st.number_input("Verba", min_value=0.0)
            if st.form_submit_button("SALVAR"):
                supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
                st.session_state.pagina = 'RESUMO'; st.rerun()

    elif pag == 'GASTO':
        st.write("#### 💸 Registrar Gasto")
        obras = listar_obras()
        with st.form("g"):
            o = st.selectbox("Obra", list(obras.keys()))
            d = st.text_input("Descrição")
            v = st.number_input("Valor", min_value=0.0)
            if st.form_submit_button("CONCLUIR"):
                st.success("Lançado!"); st.session_state.pagina = 'RESUMO'; st.rerun()
