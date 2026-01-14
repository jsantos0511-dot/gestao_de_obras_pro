import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURAÇÕES ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- CONFIGURAÇÃO DA PÁGINA (AQUI ESTÁ O SEGREDO) ---
st.set_page_config(
    page_title="Obras Pro", 
    layout="centered", 
    initial_sidebar_state="collapsed" # Força começar fechado (as 3 barrinhas)
)

# CSS para esconder o botão de fechar nativo e ajustar o visual
st.markdown("""
    <style>
    /* Faz o menu lateral se comportar de forma mais agressiva no fechamento */
    [data-testid="sidebar-button"] {
        display: none;
    }
    .metric-card {
        background-color: #161b22;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- MENU LATERAL ---
# No Streamlit, quando você clica em um rádio na sidebar, 
# o app inteiro recarrega. No celular, isso faz o menu fechar.
with st.sidebar:
    st.title("🏗️ Menu")
    pagina = st.radio(
        "Navegação", 
        ["📊 Dashboard", "💸 Novo Gasto", "📋 Histórico", "⚙️ Configurações"],
        key="menu_navegacao"
    )

# --- TELAS ---

if pagina == "📊 Dashboard":
    st.header("Resumo Financeiro")
    obras_dict = listar_obras()
    if obras_dict:
        obra_nome = st.selectbox("Obra", list(obras_dict.keys()))
        id_obra = obras_dict[obra_nome]
        
        obra_info = supabase.table("obras").select("*").eq("id", id_obra).single().execute().data
        res_soma = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_obra}).execute()
        
        total_gasto = sum(float(item['total']) for item in res_soma.data) if res_soma.data else 0
        orcamento = float(obra_info['orcamento_previsto'])
        
        st.markdown(f"""
            <div class="metric-card">
                <small>Orçamento: R$ {orcamento:,.2f}</small><br>
                <b style="font-size:1.3em; color:#f85149">Gasto: R$ {total_gasto:,.2f}</b><br>
                <small style="color:#3fb950">Saldo: R$ {(orcamento - total_gasto):,.2f}</small>
            </div>
        """, unsafe_allow_html=True)

        if res_soma.data:
            df = pd.DataFrame(res_soma.data)
            st.bar_chart(df.set_index('nome_categoria'))

elif pagina == "💸 Novo Gasto":
    st.header("Lançar Despesa")
    obras_dict = listar_obras()
    cats_dict = listar_categorias()
    
    if obras_dict:
        with st.form("form_gasto"):
            obra = st.selectbox("Obra", list(obras_dict.keys()))
            cat = st.selectbox("Categoria", list(cats_dict.keys()))
            desc = st.text_input("Descrição")
            val = st.number_input("Valor (R$)", min_value=0.0)
            
            if st.form_submit_button("Salvar"):
                supabase.table("lancamentos_obra").insert({
                    "obra_id": obras_dict[obra],
                    "categoria_id": cats_dict[cat],
                    "descricao": desc,
                    "valor": val
                }).execute()
                st.success("Lançado!")
                st.rerun() # O rerun força a página a recarregar e o menu a fechar

elif pagina == "📋 Histórico":
    st.header("Histórico")
    obras_dict = listar_obras()
    if obras_dict:
        obra_sel = st.selectbox("Filtrar por:", list(obras_dict.keys()))
        gastos = supabase.table("lancamentos_obra").select("id, data_gasto, descricao, valor").eq("obra_id", obras_dict[obra_sel]).order("data_gasto", desc=True).execute().data
        
        for g in gastos:
            with st.expander(f"{g['descricao']} - R$ {g['valor']}"):
                if st.button("Excluir", key=g['id']):
                    supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute()
                    st.rerun()

elif pagina == "⚙️ Configurações":
    st.header("Configurações")
    with st.expander("➕ Nova Obra"):
        n = st.text_input("Nome")
        v = st.number_input("Verba", min_value=0.0)
        if st.button("Cadastrar"):
            supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
            st.rerun()
