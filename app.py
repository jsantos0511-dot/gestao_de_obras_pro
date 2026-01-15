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

# --- CSS PARA MENU OVERLAY ---
st.markdown("""
    <style>
    /* Esconde menu lateral e cabeçalho padrão */
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 1rem !important; }
    
    .header-box { text-align: center; margin-bottom: 10px; }
    
    /* Botão que abre o menu */
    div.stButton > button.menu-trigger {
        background-color: #262730 !important;
        color: white !important;
        border-radius: 50px !important;
        width: 100% !important;
        margin-bottom: 20px !important;
    }

    /* Estilo dos botões de opção dentro do "menu" */
    .nav-button button {
        width: 100% !important;
        height: 50px !important;
        border: 1px solid #eee !important;
        background-color: white !important;
        margin-bottom: 10px !important;
        border-radius: 10px !important;
        font-weight: bold !important;
    }
    
    .data-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #eee;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE ESTADO ---
if 'menu_aberto' not in st.session_state:
    st.session_state.menu_aberto = False
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'RESUMO'

# --- CABEÇALHO ---
st.markdown('<div class="header-box">', unsafe_allow_html=True)
if os.path.exists("LOGOMARCA.jpeg"):
    st.image("LOGOMARCA.jpeg", width=160)
else:
    st.subheader("ROSECON ENGENHARIA")
st.markdown('</div>', unsafe_allow_html=True)

# --- BOTÃO DE MENU (ABRE/FECHA) ---
label_menu = "✖️ FECHAR MENU" if st.session_state.menu_aberto else "☰ ABRIR MENU"
if st.button(label_menu, key="trigger"):
    st.session_state.menu_aberto = not st.session_state.menu_aberto
    st.rerun()

# --- INTERFACE DO MENU (Aparece apenas se aberto) ---
if st.session_state.menu_aberto:
    st.markdown('<div class="nav-button">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 RESUMO"):
            st.session_state.pagina = 'RESUMO'
            st.session_state.menu_aberto = False
            st.rerun()
        if st.button("💸 GASTOS"):
            st.session_state.pagina = 'GASTOS'
            st.session_state.menu_aberto = False
            st.rerun()
    with col2:
        if st.button("👷 OBRAS"):
            st.session_state.pagina = 'OBRAS'
            st.session_state.menu_aberto = False
            st.rerun()
        if st.button("📋 LISTA"):
            st.session_state.pagina = 'LISTA'
            st.session_state.menu_aberto = False
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

# --- CONTEÚDO DAS PÁGINAS ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

# Renderiza apenas se o menu estiver fechado (para foco total)
if not st.session_state.menu_aberto:
    pag = st.session_state.pagina
    
    if pag == 'RESUMO':
        obras = listar_obras()
        if obras:
            o_nome = st.selectbox("Obra Ativa", list(obras.keys()))
            id_o = obras[o_nome]
            info = supabase.table("obras").select("*").eq("id", id_o).single().execute().data
            res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_o}).execute()
            gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
            orc = float(info['orcamento_previsto'])
            
            st.markdown(f"""
                <div class="data-card">
                    <small style="color:#888;">GASTO TOTAL</small>
                    <h2 style="margin:0; color:#e63946;">{formatar_real(gasto)}</h2>
                    <div style="display:flex; justify-content:space-between; margin-top:10px; border-top:1px solid #eee; padding-top:8px;">
                        <div><small>ORÇADO</small><br>{formatar_real(orc)}</div>
                        <div style="text-align:right;"><small>SALDO</small><br>{formatar_real(orc-gasto)}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if res_s.data:
                st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'GASTOS':
        st.write("### 💸 Lançar Gasto")
        obras = listar_obras()
        with st.form("fg"):
            o = st.selectbox("Obra", list(obras.keys()))
            d = st.text_input("Descrição")
            v = st.number_input("Valor", min_value=0.0)
            if st.form_submit_button("SALVAR GASTO"):
                # Simulação de insert (ajuste categoria_id conforme seu banco)
                st.success("Gasto registrado com sucesso!")
                st.session_state.pagina = 'RESUMO'
                st.rerun()
                
    elif pag == 'OBRAS':
        st.write("### 👷 Cadastrar Obra")
        with st.form("fo"):
            n = st.text_input("Nome da Obra")
            v = st.number_input("Orçamento", min_value=0.0)
            if st.form_submit_button("CADASTRAR"):
                supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
                st.success("Obra salva!")
                st.session_state.pagina = 'RESUMO'
                st.rerun()

    elif pag == 'LISTA':
        st.write("### 📋 Histórico")
        obras = listar_obras()
        if obras:
            o_sel = st.selectbox("Ver obra:", list(obras.keys()))
            st.info("Lista de gastos aparecerá aqui.")
