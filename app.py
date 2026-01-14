import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURAÇÕES ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- CONFIGURAÇÃO DA PÁGINA ---
# 'initial_sidebar_state="collapsed"' faz o menu começar recolhido (as 3 barrinhas)
st.set_page_config(
    page_title="Obras Pro", 
    layout="centered", 
    initial_sidebar_state="collapsed" 
)

# Estilização para deixar os cards bonitos no mobile
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #0e1117;
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

# --- MENU LATERAL (HAMBÚRGUER) ---
with st.sidebar:
    st.title("🏗️ Menu")
    pagina = st.radio("Navegar para:", ["📊 Dashboard", "💸 Lançar Gasto", "⚙️ Configurações"])
    st.divider()
    st.caption("Versão 1.0 - Gestão de Obras")

# --- FUNÇÕES ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- LÓGICA DAS TELAS ---

if pagina == "📊 Dashboard":
    st.header("Resumo da Obra")
    obras_dict = listar_obras()
    if obras_dict:
        obra_nome = st.selectbox("Escolha a Obra", list(obras_dict.keys()))
        id_obra = obras_dict[obra_nome]
        
        # Dados Financeiros
        obra_info = supabase.table("obras").select("*").eq("id", id_obra).single().execute().data
        gastos = supabase.table("lancamentos_obra").select("valor").eq("obra_id", id_obra).execute().data
        
        total_gasto = sum(float(item['valor']) for item in gastos)
        orcamento = float(obra_info['orcamento_previsto'])
        
        st.markdown(f"""
            <div class="metric-card">
                <small>Orçamento: R$ {orcamento:,.2f}</small><br>
                <b style="font-size:1.3em;">Gasto: R$ {total_gasto:,.2f}</b><br>
                <small style="color:#3fb950">Disponível: R$ {(orcamento - total_gasto):,.2f}</small>
            </div>
        """, unsafe_allow_html=True)

        if total_gasto > 0:
            res_gastos = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_obra}).execute()
            if res_gastos.data:
                st.write("### Gastos por Categoria")
                df = pd.DataFrame(res_gastos.data)
                st.bar_chart(df.set_index('nome_categoria'))
    else:
        st.info("Abra o menu lateral (3 barrinhas) e cadastre uma obra em 'Configurações'.")

elif pagina == "💸 Lançar Gasto":
    st.header("Novo Gasto")
    obras_dict = listar_obras()
    cats_dict = listar_categorias()
    
    if obras_dict:
        with st.form("form_gasto"):
            obra = st.selectbox("Obra", list(obras_dict.keys()))
            cat = st.selectbox("Categoria", list(cats_dict.keys()))
            desc = st.text_input("Descrição do Gasto")
            val = st.number_input("Valor (R$)", min_value=0.0)
            
            if st.form_submit_button("Salvar no Banco"):
                if desc and val > 0:
                    payload = {
                        "obra_id": obras_dict[obra],
                        "categoria_id": cats_dict[cat],
                        "descricao": desc,
                        "valor": val
                    }
                    supabase.table("lancamentos_obra").insert(payload).execute()
                    st.success("Lançamento realizado com sucesso!")
                else:
                    st.warning("Preencha todos os campos corretamente.")
    else:
        st.error("Nenhuma obra cadastrada.")

elif pagina == "⚙️ Configurações":
    st.header("Configurações")
    with st.expander("➕ Adicionar Nova Obra"):
        n = st.text_input("Nome da Obra")
        v = st.number_input("Orçamento Total", min_value=0.0)
        if st.button("Salvar Obra"):
            supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
            st.success("Obra cadastrada!")
            st.rerun()
