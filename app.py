import streamlit as st
import pandas as pd
from supabase import create_client
import os
import uuid # Para gerar nomes únicos para as fotos

# --- CONEXÃO ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ROSECON Pro", layout="centered")

# --- CSS PREMIUM (MANTIDO) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 1rem !important; }
    div.stButton > button[key="trigger"] {
        background-color: #1E1E1E !important;
        width: 70px !important; height: 70px !important;
        border-radius: 20px !important; margin: 0 auto 20px auto !important;
        display: flex !important; box-shadow: 0 8px 20px rgba(0,0,0,0.2) !important;
    }
    div.stButton > button[key="trigger"] p { font-size: 35px !important; color: #FFFFFF !important; }
    .nav-card button {
        width: 100% !important; height: 70px !important;
        background-color: #ffffff !important; border-radius: 16px !important;
        font-weight: 600 !important; border: 1px solid #f0f0f0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE ESTADO ---
if 'pagina' not in st.session_state: st.session_state.pagina = 'RESUMO'
if 'menu_aberto' not in st.session_state: st.session_state.menu_aberto = False

# --- BOTÃO MENU HAMBÚRGUER ---
icon = "×" if st.session_state.menu_aberto else "☰"
if st.button(icon, key="trigger"):
    st.session_state.menu_aberto = not st.session_state.menu_aberto
    st.rerun()

# --- MENU OVERLAY ---
if st.session_state.menu_aberto:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊\nRESUMO"): st.session_state.pagina = 'RESUMO'; st.session_state.menu_aberto = False; st.rerun()
        if st.button("💸\nNOVO GASTO"): st.session_state.pagina = 'GASTO'; st.session_state.menu_aberto = False; st.rerun()
    with c2:
        if st.button("🏗️\nOBRAS"): st.session_state.pagina = 'OBRA'; st.session_state.menu_aberto = False; st.rerun()
        if st.button("📋\nLISTA"): st.session_state.pagina = 'LISTA'; st.session_state.menu_aberto = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- PÁGINA DE GASTOS COM CÂMERA ---
elif st.session_state.pagina == 'GASTO':
    st.markdown("### 💸 Registrar Gasto")
    
    # Busca dados necessários
    res_obras = supabase.table("obras").select("id, nome_obra").execute()
    obras = {item['nome_obra']: item['id'] for item in res_obras.data}
    res_cats = supabase.table("categorias_obra").select("id, nome_categoria").execute()
    cats = {item['nome_categoria']: item['id'] for item in res_cats.data}

    with st.container(border=True):
        obra_sel = st.selectbox("Obra", list(obras.keys()))
        cat_sel = st.selectbox("Categoria", list(cats.keys()))
        desc = st.text_input("Descrição (Ex: Cimento)")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        
        st.markdown("---")
        st.markdown("**📸 Comprovante / Recibo**")
        foto = st.camera_input("Tirar foto do recibo", label_visibility="collapsed")
        
        if st.button("FINALIZAR REGISTRO", use_container_width=True, type="primary"):
            if desc and valor > 0:
                url_foto = None
                
                # Se tirou a foto, faz o upload para o Storage
                if foto:
                    file_ext = foto.name.split(".")[-1]
                    file_name = f"{uuid.uuid4()}.{file_ext}"
                    # Upload para o balde 'comprovantes'
                    res_storage = supabase.storage.from_("comprovantes").upload(file_name, foto.getvalue())
                    url_foto = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{file_name}"

                # Salva no banco de dados (adicione a coluna 'url_comprovante' na sua tabela)
                dados_gasto = {
                    "obra_id": obras[obra_sel],
                    "categoria_id": cats[cat_sel],
                    "descricao": desc,
                    "valor": valor,
                    "url_comprovante": url_foto
                }
                supabase.table("lancamentos_obra").insert(dados_gasto).execute()
                
                st.success("Gasto e foto salvos com sucesso!")
                st.session_state.pagina = 'RESUMO'
                st.rerun()
            else:
                st.error("Preencha a descrição e o valor.")

# --- OUTRAS PÁGINAS (RESUMO) ---
elif st.session_state.pagina == 'RESUMO':
    st.info("Dashboard e Resumo aqui...")
    # (Mantenha o código do dashboard anterior aqui)
