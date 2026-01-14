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
st.set_page_config(
    page_title="ROSECON Pro", 
    layout="centered", 
    initial_sidebar_state="collapsed" # Força o menu a começar escondido
)

def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# CSS para limpar o visual e ajustar o topo
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .header-box { text-align: center; margin-bottom: 10px; }
    
    /* Melhora a aparência do menu lateral */
    [data-testid="stSidebar"] {
        background-color: #1a1c23;
    }
    [data-testid="stSidebar"] .stMarkdown h2 {
        color: white;
        font-size: 20px;
    }
    
    .data-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #eee;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<div class="header-box">', unsafe_allow_html=True)
if os.path.exists("LOGOMARCA.jpeg"):
    st.image("LOGOMARCA.jpeg", width=160)
else:
    st.markdown("<h3 style='margin:0;'>ROSECON ENGENHARIA</h3>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- MENU RETRÁTIL (SIDEBAR) ---
with st.sidebar:
    st.markdown("## 🏗️ Navegação")
    # O segredo: No celular, ao selecionar o rádio, o Streamlit recarrega e fecha a sidebar
    pagina = st.radio(
        "Selecione a tela:",
        ["📊 Resumo Geral", "👷 Gerenciar Obras", "💸 Lançar Gasto", "📋 Histórico de Gastos"],
        key="menu_principal"
    )
    st.markdown("---")
    st.caption("ROSECON Pro v1.0")

# --- FUNÇÕES ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- TELAS ---

if pagina == "📊 Resumo Geral":
    obras = listar_obras()
    if obras:
        o_nome = st.selectbox("Escolha a Obra", list(obras.keys()))
        id_o = obras[o_nome]
        info = supabase.table("obras").select("*").eq("id", id_o).single().execute().data
        res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_o}).execute()
        gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
        orc = float(info['orcamento_previsto'])
        
        st.markdown(f"""
            <div class="data-card">
                <small style="color:#888;">GASTO ACUMULADO</small>
                <h2 style="margin:0; color:#e63946;">{formatar_real(gasto)}</h2>
                <div style="display:flex; justify-content:space-between; margin-top:10px; border-top:1px solid #eee; padding-top:8px;">
                    <div><small><b>ORÇADO</b></small><br>{formatar_real(orc)}</div>
                    <div style="text-align:right;"><small><b>SALDO</b></small><br>{formatar_real(orc-gasto)}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if res_s.data:
            st.write("---")
            st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))
    else:
        st.info("Abra o menu lateral e cadastre uma Obra.")

elif pagina == "👷 Gerenciar Obras":
    st.write("### 🏗️ Cadastro de Obras")
    with st.form("nova_obra"):
        n = st.text_input("Nome do Empreendimento")
        v = st.number_input("Orçamento Previsto (R$)", min_value=0.0)
        if st.form_submit_button("CADASTRAR"):
            supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
            st.success("Obra cadastrada!")

elif pagina == "💸 Lançar Gasto":
    st.write("### 💸 Novo Gasto")
    obras, cats = listar_obras(), listar_categorias()
    if obras:
        with st.form("f_gasto"):
            o = st.selectbox("Obra", list(obras.keys()))
            c = st.selectbox("Categoria", list(cats.keys()))
            d = st.text_input("Descrição do Gasto")
            v = st.number_input("Valor Pago", min_value=0.0)
            if st.form_submit_button("REGISTRAR"):
                supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v}).execute()
                st.success("Lançado!")

elif pagina == "📋 Histórico de Gastos":
    st.write("### 📋 Lista de Lançamentos")
    obras = listar_obras()
    if obras:
        o_sel = st.selectbox("Filtrar por:", list(obras.keys()))
        dados = supabase.table("lancamentos_obra").select("id, descricao, valor").eq("obra_id", obras[o_sel]).execute().data
        for d in dados:
            st.markdown(f"""
                <div class="data-card" style="margin-bottom:8px; display:flex; justify-content:space-between;">
                    <span style="font-size:13px;">{d['descricao']}</span>
                    <b style="color:#d32f2f;">{formatar_real(d['valor'])}</b>
                </div>
            """, unsafe_allow_html=True)
