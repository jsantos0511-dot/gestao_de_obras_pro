import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURAÇÕES DO BANCO DE DADOS ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- FUNÇÕES AUXILIARES ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Obras Pro", layout="centered") # Centered é melhor para celular

# Estilização CSS para botões e cards
st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .metric-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ Gestor de Obras")

# --- NOVO SISTEMA DE MENU POR ABAS ---
aba_dash, aba_gasto, aba_config = st.tabs(["📊 Resumo", "💸 Novo Gasto", "⚙️ Ajustes"])

# --- ABA 1: DASHBOARD ---
with aba_dash:
    obras_dict = listar_obras()
    if obras_dict:
        obra_nome = st.selectbox("Selecione a Obra", list(obras_dict.keys()))
        id_obra = obras_dict[obra_nome]

        # Busca dados financeiros
        obra_info = supabase.table("obras").select("*").eq("id", id_obra).single().execute().data
        gastos = supabase.table("lancamentos_obra").select("valor").eq("obra_id", id_obra).execute().data
        
        total_gasto = sum(float(item['valor']) for item in gastos)
        orcamento = float(obra_info['orcamento_previsto'])
        saldo = orcamento - total_gasto

        # Cards verticais (melhor para celular)
        st.markdown(f"""
            <div class="metric-card">
                <small>Orçamento Total</small><br>
                <b>R$ {orcamento:,.2f}</b>
            </div>
            <div class="metric-card">
                <small>Total Gasto</small><br>
                <b style="color:#ff4b4b">R$ {total_gasto:,.2f}</b>
            </div>
            <div class="metric-card">
                <small>Saldo Disponível</small><br>
                <b style="color:#28a745">R$ {saldo:,.2f}</b>
            </div>
        """, unsafe_allow_html=True)

        if total_gasto > 0:
            st.subheader("Gastos por Categoria")
            res_gastos = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': id_obra}).execute()
            if res_gastos.data:
                df = pd.DataFrame(res_gastos.data)
                st.bar_chart(df.set_index('nome_categoria'))
    else:
        st.info("Toque em 'Ajustes' para cadastrar sua primeira obra.")

# --- ABA 2: LANÇAR GASTO ---
with aba_gasto:
    st.subheader("Registrar Despesa")
    obras_dict = listar_obras()
    categorias_dict = listar_categorias()
    
    if obras_dict:
        obra_venda = st.selectbox("Obra destino", list(obras_dict.keys()), key="sel_obra")
        cat_venda = st.selectbox("Categoria", list(categorias_dict.keys()), key="sel_cat")
        desc = st.text_input("O que foi comprado?")
        val = st.number_input("Valor pago (R$)", min_value=0.0, step=10.0)
        data = st.date_input("Data", datetime.now())
        
        if st.button("Confirmar Lançamento"):
            if desc and val > 0:
                payload = {
                    "obra_id": obras_dict[obra_venda],
                    "categoria_id": categorias_dict[cat_venda],
                    "descricao": desc,
                    "valor": val,
                    "data_gasto": data.isoformat()
                }
                supabase.table("lancamentos_obra").insert(payload).execute()
                st.success("Gasto salvo!")
                st.balloons()
            else:
                st.error("Preencha a descrição e o valor.")
    else:
        st.warning("Cadastre uma obra primeiro.")

# --- ABA 3: AJUSTES ---
with aba_config:
    st.subheader("Gerenciar Obras")
    with st.expander("➕ Adicionar Nova Obra"):
        nova_obra = st.text_input("Nome do Empreendimento")
        verba = st.number_input("Verba Total Planejada", min_value=0.0)
        if st.button("Cadastrar Obra"):
            if nova_obra:
                supabase.table("obras").insert({"nome_obra": nova_obra, "orcamento_previsto": verba}).execute()
                st.success("Obra criada!")
                st.rerun()

    st.subheader("Categorias Ativas")
    st.write(list(listar_categorias().keys()))
