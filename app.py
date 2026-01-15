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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ROSECON Pro", layout="centered")

def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# --- CSS REFINADO (DESIGN PREMIUM + FIXES) ---
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
        border-radius: 20px !important;
        margin: 0 auto 25px auto !important;
        display: flex !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2) !important;
    }
    div.stButton > button[key="trigger"] p { font-size: 35px !important; color: #FFFFFF !important; }

    /* CARDS DE NAVEGAÇÃO NO MENU */
    .nav-card button {
        width: 100% !important;
        height: 85px !important;
        background-color: #ffffff !important;
        border: 1px solid #f0f0f0 !important;
        border-radius: 16px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #1E1E1E !important;
        margin-bottom: 10px !important;
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
if 'menu_aberto' not in st.session_state: st.session_state.menu_aberto = False
if 'pagina' not in st.session_state: st.session_state.pagina = 'RESUMO'

# --- HELPERS DE DADOS ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- CABEÇALHO ---
if not st.session_state.menu_aberto:
    st.markdown('<div style="text-align:center; margin-bottom:15px;">', unsafe_allow_html=True)
    if os.path.exists("LOGOMARCA.jpeg"):
        st.image("LOGOMARCA.jpeg", width=110)
    else:
        st.markdown("<h2 style='letter-spacing:-1px; color:#1E1E1E;'>ROSECON</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- BOTÃO HAMBÚRGUER ---
icon_menu = "×" if st.session_state.menu_aberto else "☰"
if st.button(icon_menu, key="trigger"):
    st.session_state.menu_aberto = not st.session_state.menu_aberto
    st.rerun()

# --- MENU OVERLAY ---
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
    # --- CONTEÚDO DAS PÁGINAS ---
    pag = st.session_state.pagina
    
    if pag == 'RESUMO':
        obras = listar_obras()
        if obras:
            o_nome = st.selectbox("Selecione a Obra", list(obras.keys()), label_visibility="collapsed")
            id_o = obras[o_nome]
            
            # Busca Info da Obra e Gastos
            info = supabase.table("obras").select("*").eq("id", id_o).single().execute().data
            res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_o}).execute()
            
            gasto_total = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
            orcamento = float(info['orcamento_previsto'])
            
            st.markdown(f"""
                <div class="data-card">
                    <div class="label-small">Investimento Utilizado</div>
                    <div style="font-size: 34px; font-weight: 800; color: #1c1c1e; margin: 5px 0;">{formatar_real(gasto_total)}</div>
                    <div style="display:flex; justify-content:space-between; margin-top:20px; padding-top:15px; border-top: 1px solid #f5f5f5;">
                        <div>
                            <div class="label-small">Orçado</div>
                            <div style="font-size: 15px; font-weight: 600;">{formatar_real(orcamento)}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="label-small">Disponível</div>
                            <div style="font-size: 15px; font-weight: 600; color: #34c759;">{formatar_real(orcamento - gasto_total)}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if res_s.data:
                df = pd.DataFrame(res_s.data)
                st.bar_chart(df.set_index('nome_categoria'))

    elif pag == 'GASTO':
        st.markdown("### 💸 Lançar Gasto com Foto")
        obras = listar_obras()
        cats = listar_categorias()
        
        with st.container(border=True):
            o_sel = st.selectbox("Obra", list(obras.keys()))
            c_sel = st.selectbox("Categoria", list(cats.keys()))
            desc = st.text_input("Descrição (Ex: Nota Fiscal Material)")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            
            st.markdown("---")
            st.markdown("**📸 Capturar Comprovante**")
            foto = st.camera_input("Tirar foto do recibo", label_visibility="collapsed")
            
            if st.button("SALVAR LANÇAMENTO", use_container_width=True, type="primary"):
                if desc and valor > 0:
                    url_foto = None
                    if foto:
                        file_name = f"{uuid.uuid4()}.jpg"
                        supabase.storage.from_("comprovantes").upload(file_name, foto.getvalue())
                        url_foto = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{file_name}"
                    
                    supabase.table("lancamentos_obra").insert({
                        "obra_id": obras[o_sel],
                        "categoria_id": cats[c_sel],
                        "descricao": desc,
                        "valor": valor,
                        "url_comprovante": url_foto
                    }).execute()
                    
                    st.success("Gasto registrado com sucesso!")
                    st.session_state.pagina = 'RESUMO'; st.rerun()
                else:
                    st.warning("Por favor, preencha descrição e valor.")

    elif pag == 'OBRA':
        st.markdown("### 🏗️ Nova Obra")
        with st.container(border=True):
            n = st.text_input("Nome do Empreendimento")
            v = st.number_input("Orçamento Previsto (R$)", min_value=0.0)
            if st.button("Cadastrar Obra", use_container_width=True):
                supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
                st.success("Obra cadastrada!")
                st.session_state.pagina = 'RESUMO'; st.rerun()

    elif pag == 'LISTA':
        st.markdown("### 📄 Histórico de Gastos")
        obras = listar_obras()
        o_filtro = st.selectbox("Filtrar por Obra", list(obras.keys()))
        
        gastos = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("obra_id", obras[o_filtro]).order("id", desc=True).execute()
        
        for g in gastos.data:
            with st.expander(f"{g['descricao']} - {formatar_real(g['valor'])}"):
                st.write(f"**Categoria:** {g['categorias_obra']['nome_categoria']}")
                if g.get('url_comprovante'):
                    st.image(g['url_comprovante'], caption="Comprovante Original", use_container_width=True)
                else:
                    st.info("Sem foto anexada.")
