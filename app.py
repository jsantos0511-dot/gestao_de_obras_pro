import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import uuid
from datetime import datetime
from fpdf import FPDF

# --- 1. CONEXÃO ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="ROSECON Pro", layout="centered")

# --- 2. GESTÃO DE SESSÃO E LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'user_perfil' not in st.session_state: st.session_state.user_perfil = None

def realizar_login(email, senha):
    res = supabase.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
    if res.data:
        st.session_state.logado = True
        st.session_state.user_perfil = res.data[0]['perfil']
        st.session_state.pagina = 'RESUMO'
        return True
    return False

# --- 3. ESTILO VISUAL ---
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 1rem !important; }
    .data-card { background: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #eee; margin-bottom: 15px; color: #1e1e1e; }
    div.stButton > button[key="trigger"] {
        background-color: #1E1E1E !important; width: 70px !important; height: 70px !important;
        border-radius: 20px !important; margin: 0 auto 15px auto !important; display: flex !important;
    }
    .nav-card button { width: 100% !important; height: 80px !important; border-radius: 15px !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.markdown("<h2 style='text-align:center;'>ROSECON Pro</h2>", unsafe_allow_html=True)
    with st.container(border=True):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA", use_container_width=True, type="primary"):
            if realizar_login(email, senha):
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
    st.stop()

# --- FUNÇÕES DE APOIO (PDF E LISTAS) ---
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- 4. NAVEGAÇÃO E MENU ---
if 'menu_aberto' not in st.session_state: st.session_state.menu_aberto = False

icon = "×" if st.session_state.menu_aberto else "☰"
if st.button(icon, key="trigger"):
    st.session_state.menu_aberto = not st.session_state.menu_aberto
    st.rerun()

if st.session_state.menu_aberto:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        # Acesso comum
        if st.button("📊\nDashboard"): st.session_state.pagina='RESUMO'; st.session_state.menu_aberto=False; st.rerun()
        if st.button("💸\nLançar Gasto"): st.session_state.pagina='GASTO'; st.session_state.menu_aberto=False; st.rerun()
    with c2:
        # Acesso restrito ADMIN
        if st.session_state.user_perfil == 'ADMIN':
            if st.button("🏗️\nMinhas Obras"): st.session_state.pagina='OBRA'; st.session_state.menu_aberto=False; st.rerun()
            if st.button("📋\nRelatórios"): st.session_state.pagina='LISTA'; st.session_state.menu_aberto=False; st.rerun()
        else:
            st.button("🔒\nBloqueado", disabled=True)
            st.button("📋\nHistórico", disabled=True) # Pode-se liberar uma versão simplificada depois
    
    if st.button("Sair / Logout", use_container_width=True):
        st.session_state.logado = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- 5. TELAS ---
    pag = st.session_state.pagina
    perfil = st.session_state.user_perfil

    if pag == 'RESUMO':
        obras = listar_obras()
        if obras:
            sel = st.selectbox("Obra Ativa", list(obras.keys()), label_visibility="collapsed")
            res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': obras[sel]}).execute()
            gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
            
            # Somente ADMIN vê valores financeiros de saldo
            if perfil == 'ADMIN':
                info = supabase.table("obras").select("*").eq("id", obras[sel]).single().execute().data
                st.markdown(f'<div class="data-card"><small>GASTO TOTAL</small><h2>{formatar_real(gasto)}</h2><hr><small>SALDO: {formatar_real(float(info["orcamento_previsto"]) - gasto)}</small></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="data-card"><small>GASTO ACUMULADO</small><h2>{formatar_real(gasto)}</h2></div>', unsafe_allow_html=True)
            
            if res_s.data: st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'GASTO':
        st.markdown("### 💸 Lançar Gasto")
        obras, cats = listar_obras(), listar_categorias()
        with st.container(border=True):
            o = st.selectbox("Obra", list(obras.keys()))
            c = st.selectbox("Categoria", list(cats.keys()))
            d = st.text_input("Descrição")
            v = st.number_input("Valor", min_value=0.0)
            foto = st.camera_input("Foto do Recibo")
            if st.button("SALVAR", use_container_width=True, type="primary"):
                # ... (Lógica de upload mantida igual)
                url = None
                if foto:
                    n_arq = f"{uuid.uuid4()}.jpg"
                    supabase.storage.from_("comprovantes").upload(n_arq, foto.getvalue())
                    url = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{n_arq}"
                supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v, "url_comprovante": url}).execute()
                st.success("Salvo com sucesso!"); st.session_state.pagina = 'RESUMO'; st.rerun()

    elif pag == 'LISTA' and perfil == 'ADMIN':
        # Histórico completo com PDF e Excluir (Só para Admin)
        st.markdown("### 📋 Relatório Mestre")
        # ... (Mantido lógica da Lista anterior com botão excluir e PDF)
        # [Código da LISTA aqui...]
