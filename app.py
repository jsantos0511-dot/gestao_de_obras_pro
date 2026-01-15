import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import uuid

# --- CONEXÃO ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="ROSECON Pro", layout="centered")

# --- FUNÇÕES E ESTILO (MANTIDOS) ---
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 1rem !important; }
    div.stButton > button[key="trigger"] {
        background-color: #1E1E1E !important;
        width: 75px !important; height: 75px !important;
        border-radius: 22px !important; margin: 0 auto 20px auto !important;
        display: flex !important; box-shadow: 0 8px 25px rgba(0,0,0,0.3) !important;
    }
    div.stButton > button[key="trigger"] p { font-size: 38px !important; color: #FFFFFF !important; }
    .nav-card button {
        width: 100% !important; height: 85px !important;
        background-color: #ffffff !important; border: 1px solid #f0f0f0 !important;
        border-radius: 18px !important; font-weight: 700 !important;
    }
    .data-card {
        background: #ffffff; padding: 24px; border-radius: 20px;
        border: 1px solid #f0f0f0; box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

if 'menu_aberto' not in st.session_state: st.session_state.menu_aberto = False
if 'pagina' not in st.session_state: st.session_state.pagina = 'RESUMO'

# Botão Menu
icon = "×" if st.session_state.menu_aberto else "☰"
if st.button(icon, key="trigger"):
    st.session_state.menu_aberto = not st.session_state.menu_aberto
    st.rerun()

if st.session_state.menu_aberto:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊\nDashboard"): st.session_state.pagina='RESUMO'; st.session_state.menu_aberto=False; st.rerun()
        if st.button("💸\nLançar Gasto"): st.session_state.pagina='GASTO'; st.session_state.menu_aberto=False; st.rerun()
    with c2:
        if st.button("🏗️\nMinhas Obras"): st.session_state.pagina='OBRA'; st.session_state.menu_aberto=False; st.rerun()
        if st.button("📋\nRelatórios"): st.session_state.pagina='LISTA'; st.session_state.menu_aberto=False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    pag = st.session_state.pagina
    if pag == 'RESUMO':
        obras = listar_obras()
        if obras:
            sel = st.selectbox("Obra", list(obras.keys()), label_visibility="collapsed")
            info = supabase.table("obras").select("*").eq("id", obras[sel]).single().execute().data
            res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': obras[sel]}).execute()
            gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
            st.markdown(f'<div class="data-card"><small>GASTO</small><h2>{formatar_real(gasto)}</h2><hr><small>SALDO: <b>{formatar_real(float(info["orcamento_previsto"]) - gasto)}</b></small></div>', unsafe_allow_html=True)
            if res_s.data: st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'GASTO':
        st.markdown("### 💸 Novo Gasto")
        obras, cats = listar_obras(), listar_categorias()
        with st.container(border=True):
            o = st.selectbox("Obra", list(obras.keys()))
            c = st.selectbox("Categoria", list(cats.keys()))
            d = st.text_input("Descrição")
            v = st.number_input("Valor", min_value=0.0)
            foto = st.camera_input("Tirar foto do recibo")
            
            if st.button("SALVAR", use_container_width=True, type="primary"):
                url_f = None
                if foto:
                    try:
                        f_name = f"{uuid.uuid4()}.jpg"
                        # Envia o arquivo
                        supabase.storage.from_("comprovantes").upload(f_name, foto.getvalue())
                        url_f = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{f_name}"
                    except Exception as e:
                        st.error(f"Erro ao salvar foto: {e}")
                
                # Salva no banco de dados
                try:
                    supabase.table("lancamentos_obra").insert({
                        "obra_id": obras[o], "categoria_id": cats[c],
                        "descricao": d, "valor": v, "url_comprovante": url_f
                    }).execute()
                    st.success("Lançamento concluído!"); st.session_state.pagina = 'RESUMO'; st.rerun()
                except Exception as e:
                    st.error(f"Erro no banco: {e}")

    elif pag == 'LISTA':
        st.markdown("### 📋 Histórico")
        obras = listar_obras()
        if obras:
            o_f = st.selectbox("Obra:", list(obras.keys()))
            dados = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("obra_id", obras[o_f]).order("id", desc=True).execute().data
            for g in dados:
                with st.expander(f"{g['descricao']} | {formatar_real(g['valor'])}"):
                    if g.get('url_comprovante'): st.image(g['url_comprovante'])
                    else: st.caption("Sem foto anexada.")
