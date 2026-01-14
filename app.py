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
st.set_page_config(page_title="ROSECON", layout="centered")

# CSS para Menu Superior Slim e Estilo Executivo
st.markdown("""
    <style>
    /* Esconde menus nativos */
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    
    /* Logomarca e Título */
    .header-container { text-align: center; margin-top: -50px; }
    .company-name { font-size: 18px; font-weight: bold; color: #333; margin-top: 5px; }

    /* Estilo dos botões do menu superior */
    div.stButton > button {
        border-radius: 5px;
        height: 45px;
        padding: 0px;
        font-size: 14px;
        background-color: #f8f9fa;
        border: 1px solid #ddd;
    }
    
    /* Destaque para o botão ativo (opcional, simulado por cores) */
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #eee;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO: LOGO + NOME DISCRETO ---
st.markdown('<div class="header-container">', unsafe_allow_html=True)
if os.path.exists("LOGOMARCA.jpeg"):
    st.image("LOGOMARCA.jpeg", width=150)
else:
    st.markdown('<div class="company-name">ROSECON ENGENHARIA</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- MENU SUPERIOR HORIZONTAL ---
# Criando 4 colunas iguais logo abaixo da logo
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'Resumo'

m1, m2, m3, m4 = st.columns(4)
with m1:
    if st.button("📊\nResumo"): st.session_state.pagina = 'Resumo'; st.rerun()
with m2:
    if st.button("💸\nGasto"): st.session_state.pagina = 'Gasto'; st.rerun()
with m3:
    if st.button("📋\nLista"): st.session_state.pagina = 'Lista'; st.rerun()
with m4:
    if st.button("⚙️\nObra"): st.session_state.pagina = 'Obra'; st.rerun()

st.divider()

# --- FUNÇÕES DE BANCO ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- CONTEÚDO DAS PÁGINAS ---
pag = st.session_state.pagina

if pag == 'Resumo':
    obras = listar_obras()
    if obras:
        o_nome = st.selectbox("Selecione a Obra", list(obras.keys()))
        id_o = obras[o_nome]
        
        info = supabase.table("obras").select("*").eq("id", id_o).single().execute().data
        res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_o}).execute()
        
        gasto_total = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
        orcamento = float(info['orcamento_previsto'])
        
        st.markdown(f"""
            <div class="metric-card">
                <small>Investimento Total</small><br>
                <b style="font-size:20px; color:#d32f2f;">Gasto: R$ {gasto_total:,.2f}</b><br>
                <small>Saldo: R$ {(orcamento - gasto_total):,.2f}</small>
            </div>
        """, unsafe_allow_html=True)
        
        if res_s.data:
            df = pd.DataFrame(res_s.data)
            st.bar_chart(df.set_index('nome_categoria'))

elif pag == 'Gasto':
    st.write("### Novo Gasto")
    obras, cats = listar_obras(), listar_categorias()
    if obras:
        with st.form("form_gasto", clear_on_submit=True):
            o = st.selectbox("Obra", list(obras.keys()))
            c = st.selectbox("Categoria", list(cats.keys()))
            d = st.text_input("Descrição")
            v = st.number_input("Valor (R$)", min_value=0.0)
            if st.form_submit_button("REGISTRAR"):
                supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v}).execute()
                st.success("Lançado!")

elif pag == 'Lista':
    st.write("### Histórico")
    obras = listar_obras()
    if obras:
        o_sel = st.selectbox("Obra", list(obras.keys()))
        dados = supabase.table("lancamentos_obra").select("id, descricao, valor").eq("obra_id", obras[o_sel]).execute().data
        for d in dados:
            with st.expander(f"{d['descricao']} - R$ {d['valor']}"):
                if st.button("Remover", key=d['id']):
                    supabase.table("lancamentos_obra").delete().eq("id", d['id']).execute()
                    st.rerun()

elif pag == 'Obra':
    st.write("### Configurar Obra")
    with st.form("nova_obra"):
        n = st.text_input("Nome")
        v = st.number_input("Orçamento", min_value=0.0)
        if st.form_submit_button("CRIAR"):
            supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
            st.success("Obra cadastrada!")
