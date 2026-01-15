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

# --- CSS REFINADO ---
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 1rem !important; }
    
    /* BOTÃO MENU FLUTUANTE */
    div.stButton > button[key="trigger"] {
        background-color: #1E1E1E !important;
        border: none !important;
        width: 70px !important;
        height: 70px !important;
        border-radius: 20px !important; /* Estilo 'Squircle' moderno */
        margin: 0 auto 25px auto !important;
        display: flex !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2) !important;
    }

    div.stButton > button[key="trigger"] p {
        font-size: 35px !important;
        color: #FFFFFF !important;
    }

    /* CARDS DE NAVEGAÇÃO */
    .nav-card button {
        width: 100% !important;
        height: 80px !important;
        background-color: #ffffff !important;
        border: 1px solid #f0f0f0 !important;
        border-radius: 16px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #1E1E1E !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease;
    }
    
    .nav-card button:active {
        background-color: #f0f2f6 !important;
        transform: scale(0.98);
    }

    /* ESTILO DOS CARDS DE DADOS */
    .data-card {
        background: #ffffff;
        padding: 24px;
        border-radius: 20px;
        border: 1px solid #f0f0f0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        margin-bottom: 20px;
    }
    
    .label-small { color: #8E8E93; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE ESTADO ---
if 'menu_aberto' not in st.session_state:
    st.session_state.menu_aberto = False
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'RESUMO'

# --- CABEÇALHO ---
if not st.session_state.menu_aberto:
    st.markdown('<div style="text-align:center; margin-bottom:15px;">', unsafe_allow_html=True)
    if os.path.exists("LOGOMARCA.jpeg"):
        st.image("LOGOMARCA.jpeg", width=120)
    else:
        st.markdown("<h2 style='letter-spacing:-1px;'>ROSECON</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- BOTÃO HAMBÚRGUER ---
icon_menu = "×" if st.session_state.menu_aberto else "☰"
if st.button(icon_menu, key="trigger"):
    st.session_state.menu_aberto = not st.session_state.menu_aberto
    st.rerun()

# --- MENU OVERLAY ESTILIZADO ---
if st.session_state.menu_aberto:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊\nDashboard"):
            st.session_state.pagina = 'RESUMO'; st.session_state.menu_aberto = False; st.rerun()
        if st.button("💸\nNovo Gasto"):
            st.session_state.pagina = 'GASTO'; st.session_state.menu_aberto = False; st.rerun()
    with c2:
        if st.button("🏗️\nMinhas Obras"):
            st.session_state.pagina = 'OBRA'; st.session_state.menu_aberto = False; st.rerun()
        if st.button("📄\nRelatórios"):
            st.session_state.pagina = 'LISTA'; st.session_state.menu_aberto = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    # --- CONTEÚDO ---
    def listar_obras():
        res = supabase.table("obras").select("id, nome_obra").execute()
        return {item['nome_obra']: item['id'] for item in res.data}

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
                    <div class="label-small">Investimento Utilizado</div>
                    <div style="font-size: 34px; font-weight: 800; color: #1c1c1e; margin: 5px 0;">{formatar_real(gasto)}</div>
                    <div style="display:flex; justify-content:space-between; margin-top:20px; padding-top:15px; border-top: 1px solid #f5f5f5;">
                        <div>
                            <div class="label-small">Orçado</div>
                            <div style="font-size: 15px; font-weight: 600;">{formatar_real(orc)}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="label-small">Disponível</div>
                            <div style="font-size: 15px; font-weight: 600; color: #34c759;">{formatar_real(orc-gasto)}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if res_s.data:
                st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'GASTO':
        st.markdown("### 💸 Lançar Gasto")
        obras = listar_obras()
        with st.container(border=True):
            o = st.selectbox("Obra", list(obras.keys()))
            d = st.text_input("Descrição")
            v = st.number_input("Valor (R$)", min_value=0.0)
            if st.button("Confirmar Lançamento", use_container_width=True):
                st.success("Gasto salvo!")
                st.session_state.pagina = 'RESUMO'; st.rerun()

    elif pag == 'OBRA':
        st.markdown("### 🏗️ Gestão de Obras")
        with st.container(border=True):
            n = st.text_input("Nome da Obra")
            v = st.number_input("Orçamento Total", min_value=0.0)
            if st.button("Criar Empreendimento", use_container_width=True):
                supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
                st.session_state.pagina = 'RESUMO'; st.rerun()
