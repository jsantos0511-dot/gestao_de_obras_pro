import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURAÇÕES DO BANCO DE DADOS ---
# Reutilizando suas credenciais existentes
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return None

supabase = get_supabase()

# --- FUNÇÕES DE DADOS ---
def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").order("nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

# --- INTERFACE ---
st.set_page_config(page_title="Obras Pro", layout="wide")

# Estilo para os cards de resumo
st.markdown("""
    <style>
    .metric-container {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ Gestão de Obras do Zero")

menu = st.sidebar.radio("Navegação", ["Dashboard", "Lançar Gasto", "Cadastrar Obra"])

# --- ABA: CADASTRAR OBRA ---
if menu == "Cadastrar Obra":
    st.subheader("Configurar Nova Construção")
    with st.form("form_obra"):
        nome = st.text_input("Nome da Obra (ex: Casa de Praia)")
        orcamento = st.number_input("Orçamento Previsto (R$)", min_value=0.0, step=1000.0)
        if st.form_submit_button("Salvar Obra"):
            if nome:
                supabase.table("obras").insert({"nome_obra": nome, "orcamento_previsto": orcamento}).execute()
                st.success(f"Obra '{nome}' cadastrada com sucesso!")
                st.rerun()
            else:
                st.warning("O nome da obra é obrigatório.")

# --- ABA: LANÇAR GASTO ---
elif menu == "Lançar Gasto":
    st.subheader("Registrar Despesa")
    obras_dict = listar_obras()
    categorias_dict = listar_categorias()
    
    if not obras_dict:
        st.info("Cadastre uma obra primeiro para começar os lançamentos.")
    else:
        with st.form("form_gasto"):
            obra_nome = st.selectbox("Obra", list(obras_dict.keys()))
            categoria_nome = st.selectbox("Categoria", list(categorias_dict.keys()))
            descricao = st.text_input("Descrição (ex: 50 sacos de cimento)")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
            fornecedor = st.text_input("Fornecedor (opcional)")
            data = st.date_input("Data da Compra", datetime.now())
            
            if st.form_submit_button("Salvar Gasto"):
                if descricao and valor > 0:
                    dados = {
                        "obra_id": obras_dict[obra_nome],
                        "categoria_id": categorias_dict[categoria_nome],
                        "descricao": descricao,
                        "valor": valor,
                        "fornecedor": fornecedor,
                        "data_gasto": data.isoformat()
                    }
                    supabase.table("lancamentos_obra").insert(dados).execute()
                    st.toast("✅ Gasto registrado!")
                else:
                    st.error("Preencha a descrição e o valor.")

# --- ABA: DASHBOARD ---
else:
    st.subheader("Dashboard Financeiro")
    obras_dict = listar_obras()
    
    if obras_dict:
        obra_nome = st.selectbox("Selecione a Obra para Ver o Resumo", list(obras_dict.keys()))
        obra_id = obras_dict[obra_nome]
        
        # Buscar dados da obra
        obra_info = supabase.table("obras").select("*").eq("id", obra_id).single().execute().data
        gastos = supabase.table("lancamentos_obra").select("valor, categoria_id").eq("obra_id", obra_id).execute().data
        
        total_gasto = sum(item['valor'] for item in gastos)
        orcamento = float(obra_info['orcamento_previsto'])
        saldo = orcamento - total_gasto
        
        # Exibição dos cards
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-container">Previsto<br><b>R$ {orcamento:,.2f}</b></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-container">Gasto<br><b style="color:#f85149">R$ {total_gasto:,.2f}</b></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-container">Saldo<br><b style="color:#3fb950">R$ {saldo:,.2f}</b></div>', unsafe_allow_html=True)
        
        st.divider()
        
        if total_gasto > 0:
            st.write("### Detalhes por Categoria")
            # Unir gastos com nomes das categorias para o gráfico
            res_gastos = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': obra_id}).execute()
            if res_gastos.data:
                df = pd.DataFrame(res_gastos.data)
                st.bar_chart(df.set_index('nome_categoria'))
            
            # Tabela de lançamentos recentes
            st.write("### Últimos Lançamentos")
            ultimos = supabase.table("lancamentos_obra").select("data_gasto, descricao, valor").eq("obra_id", obra_id).order("data_gasto", desc=True).limit(5).execute()
            st.table(pd.DataFrame(ultimos.data))
    else:
        st.info("Nenhuma obra cadastrada ainda.")
