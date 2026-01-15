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

# --- CSS PARA MENU HAMBÚRGUER E BOTÕES ---
st.markdown("""
    <style>
    /* Esconde elementos padrão */
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 1rem !important; }
    
    .header-box { text-align: center; margin-bottom: 5px; }
    
    /* Botão Hambúrguer (Trigger) Grande */
    div.stButton > button[key="trigger"] {
        background-color: transparent !important;
        border: 1px solid #eee !important;
        color: #333 !important;
        font-size: 28px !important; /* Ícone Grande */
        width: 60px !important;
        height: 60px !important;
        border-radius: 50% !important;
        margin: 0 auto 15px auto !important;
        display: block !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
    }

    /* Botões de Opção do Menu */
    .nav-button button {
        width: 100% !important;
        height: 55px !important;
        border: 1px solid #f0f0f0 !important;
        background-color: #f8f9fa !important;
        margin-bottom: 12px !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        font-size: 14px !important;
        color: #333 !important;
    }
    
    .data-card {
        background-color: white;
        padding: 18px;
        border-radius: 15px;
        border: 1px solid #eee;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
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
    st.image("LOGOMARCA.jpeg", width=150)
else:
    st.markdown("<h3 style='margin:0;'>ROSECON</h3>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- BOTÃO HAMBÚRGUER (SOMENTE ÍCONE) ---
icon_menu = "✖" if st.session_state.menu_aberto else "☰"
if st.button(icon_menu, key="trigger"):
    st.session_state.menu_aberto = not st.session_state.menu_aberto
    st.rerun()

# --- MENU DE OPÇÕES (EXIBIDO SE ABERTO) ---
if st.session_state.menu_aberto:
    st.markdown('<div class="nav-button">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 RESUMO"):
            st.session_state.pagina = 'RESUMO'
            st.session_state.menu_aberto = False
            st.rerun()
        if st.button("💸 GASTO"):
            st.session_state.pagina = 'GASTO'
            st.session_state.menu_aberto = False
            st.rerun()
    with col2:
        if st.button("👷 OBRAS"):
            st.session_state.pagina = 'OBRA'
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

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

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
                    <small style="color:#888; letter-spacing:1px;">GASTO TOTAL ACUMULADO</small>
                    <h2 style="margin:0; color:#e63946; font-size:28px;">{formatar_real(gasto)}</h2>
                    <div style="display:flex; justify-content:space-between; margin-top:15px; border-top:1px solid #eee; padding-top:10px;">
                        <div><small>ORÇADO</small><br><b>{formatar_real(orc)}</b></div>
                        <div style="text-align:right;"><small>SALDO</small><br><b>{formatar_real(orc-gasto)}</b></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if res_s.data:
                st.write("")
                st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'OBRA':
        st.write("#### 👷 Nova Obra")
        with st.form("n"):
            n = st.text_input("Nome")
            v = st.number_input("Verba", min_value=0.0)
            if st.form_submit_button("SALVAR"):
                supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
                st.session_state.pagina = 'RESUMO'
                st.rerun()

    elif pag == 'GASTO':
        st.write("#### 💸 Registrar Gasto")
        obras, cats = listar_obras(), listar_categorias()
        with st.form("g"):
            o = st.selectbox("Obra", list(obras.keys()))
            c = st.selectbox("Categoria", list(cats.keys()))
            d = st.text_input("Descrição")
            v = st.number_input("Valor", min_value=0.0)
            if st.form_submit_button("CONCLUIR"):
                supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v}).execute()
                st.session_state.pagina = 'RESUMO'
                st.rerun()

    elif pag == 'LISTA':
        st.write("#### 📋 Histórico")
        obras = listar_obras()
        if obras:
            o_sel = st.selectbox("Obra", list(obras.keys()))
            dados = supabase.table("lancamentos_obra").select("id, descricao, valor").eq("obra_id", obras[o_sel]).execute().data
            for d in dados:
                st.markdown(f"<div class='data-card' style='margin-bottom:8px; padding:12px; display:flex; justify-content:space-between;'><span style='font-size:14px;'>{d['descricao']}</span><b>{formatar_real(d['valor'])}</b></div>", unsafe_allow_html=True)
