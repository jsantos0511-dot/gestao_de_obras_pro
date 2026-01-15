import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import uuid

# --- 1. CONEXÃO ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="ROSECON Pro", layout="centered")

# --- 2. FUNÇÕES CONSOLIDADAS ---
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- 3. CSS DESIGN PREMIUM (BARRINHAS GIGANTES) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 1rem !important; }
    
    div.stButton > button[key="trigger"] {
        background-color: #1E1E1E !important;
        border: none !important;
        width: 75px !important; height: 75px !important;
        border-radius: 22px !important;
        margin: 0 auto 20px auto !important;
        display: flex !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3) !important;
    }
    div.stButton > button[key="trigger"] p { font-size: 38px !important; color: #FFFFFF !important; }

    .nav-card button {
        width: 100% !important; height: 85px !important;
        background-color: #ffffff !important; border: 1px solid #f0f0f0 !important;
        border-radius: 18px !important; font-weight: 700 !important;
        color: #1E1E1E !important; margin-bottom: 12px !important;
    }

    .data-card {
        background: #ffffff; padding: 24px; border-radius: 20px;
        border: 1px solid #f0f0f0; box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        margin-bottom: 20px;
    }
    .label-small { color: #8E8E93; font-size: 11px; font-weight: 700; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

# --- 4. GESTÃO DE NAVEGAÇÃO ---
if 'menu_aberto' not in st.session_state: st.session_state.menu_aberto = False
if 'pagina' not in st.session_state: st.session_state.pagina = 'RESUMO'

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
        obras_dict = listar_obras()
        if obras_dict:
            sel_obra = st.selectbox("Obra", list(obras_dict.keys()), label_visibility="collapsed")
            id_o = obras_dict[sel_obra]
            info = supabase.table("obras").select("*").eq("id", id_o).single().execute().data
            res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_o}).execute()
            
            gasto_total = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
            orcado = float(info['orcamento_previsto'])
            
            st.markdown(f"""
                <div class="data-card">
                    <div class="label-small">Gasto Acumulado</div>
                    <div style="font-size: 34px; font-weight: 800; color: #1c1c1e; margin: 5px 0;">{formatar_real(gasto_total)}</div>
                    <div style="display:flex; justify-content:space-between; margin-top:20px; padding-top:15px; border-top: 1px solid #f5f5f5;">
                        <div><div class="label-small">Orçado</div><b>{formatar_real(orcado)}</b></div>
                        <div style="text-align:right;"><div class="label-small">Saldo</div><b style="color:#34c759;">{formatar_real(orcado - gasto_total)}</b></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if res_s.data:
                st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'GASTO':
        st.markdown("### 💸 Registrar Novo Gasto")
        obras, cats = listar_obras(), listar_categorias()
        with st.container(border=True):
            o_sel = st.selectbox("Obra", list(obras.keys()))
            c_sel = st.selectbox("Categoria", list(cats.keys()))
            desc = st.text_input("Descrição")
            valor = st.number_input("Valor Pago", min_value=0.0, step=0.01)
            foto = st.camera_input("Tirar foto do recibo")
            
            if st.button("CONCLUIR LANÇAMENTO", use_container_width=True, type="primary"):
                url_f = None
                if foto:
                    try:
                        f_name = f"{uuid.uuid4()}.jpg"
                        supabase.storage.from_("comprovantes").upload(f_name, foto.getvalue())
                        url_f = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{f_name}"
                    except Exception as e:
                        st.error(f"Erro ao salvar foto: {e}")

                try:
                    supabase.table("lancamentos_obra").insert({
                        "obra_id": obras[o_sel], "categoria_id": cats[c_sel],
                        "descricao": desc, "valor": valor, "url_comprovante": url_f
                    }).execute()
                    st.success("Lançamento concluído!"); st.session_state.pagina = 'RESUMO'; st.rerun()
                except Exception as e:
                    st.error(f"Erro no banco: {e}")

    elif pag == 'LISTA':
        st.markdown("### 📋 Histórico Detalhado")
        obras = listar_obras()
        if obras:
            o_f = st.selectbox("Obra:", list(obras.keys()))
            dados = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("obra_id", obras[o_f]).order("id", desc=True).execute().data
            for g in dados:
                with st.expander(f"{g['descricao']} | {formatar_real(g['valor'])}"):
                    if g.get('url_comprovante'):
                        st.image(g['url_comprovante'])
                    else:
                        st.caption("Nenhuma foto anexada.")
