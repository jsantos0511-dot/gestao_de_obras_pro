import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import uuid
from datetime import datetime
from fpdf import FPDF

# --- 1. CONEXÃO ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="ROSECON Pro", layout="centered")

# --- 2. FUNÇÕES DE APOIO ---
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def listar_obras():
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

def gerar_pdf(df, nome_obra):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Relatorio ROSECON - {nome_obra}", ln=True, align="C")
    pdf.ln(10)
    
    # Cabeçalho
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 10, "Data", 1)
    pdf.cell(90, 10, "Descricao", 1)
    pdf.cell(30, 10, "Categoria", 1)
    pdf.cell(40, 10, "Valor", 1)
    pdf.ln()
    
    # Itens
    pdf.set_font("Arial", "", 10)
    total = 0
    for _, row in df.iterrows():
        data_f = datetime.strptime(row['created_at'][:10], '%Y-%m-%d').strftime('%d/%m/%Y')
        pdf.cell(30, 10, data_f, 1)
        pdf.cell(90, 10, str(row['descricao'])[:40], 1)
        pdf.cell(30, 10, str(row['categorias_obra']['nome_categoria']), 1)
        pdf.cell(40, 10, f"R$ {row['valor']:,.2f}", 1)
        pdf.ln()
        total += row['valor']
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"TOTAL: {formatar_real(total)}", ln=True, align="R")
    
    # Retorna o PDF como string de bytes
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. ESTILO VISUAL ---
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 1rem !important; }
    div.stButton > button[key="trigger"] {
        background-color: #1E1E1E !important; width: 75px !important; height: 75px !important;
        border-radius: 22px !important; margin: 0 auto 20px auto !important; display: flex !important;
    }
    div.stButton > button[key="trigger"] p { font-size: 38px !important; color: #FFFFFF !important; }
    .nav-card button { width: 100% !important; height: 85px !important; border-radius: 18px !important; font-weight: 700 !important; }
    .data-card { background: #ffffff; padding: 24px; border-radius: 20px; border: 1px solid #f0f0f0; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

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
        obras = listar_obras()
        if obras:
            sel = st.selectbox("Obra Ativa", list(obras.keys()), label_visibility="collapsed")
            info = supabase.table("obras").select("*").eq("id", obras[sel]).single().execute().data
            res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': obras[sel]}).execute()
            gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
            st.markdown(f'<div class="data-card"><small>GASTO TOTAL</small><h2>{formatar_real(gasto)}</h2><hr><small>SALDO: {formatar_real(float(info["orcamento_previsto"]) - gasto)}</small></div>', unsafe_allow_html=True)
            if res_s.data: st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'GASTO':
        st.markdown("### 💸 Novo Lançamento")
        obras, cats = listar_obras(), listar_categorias()
        with st.container(border=True):
            o = st.selectbox("Obra", list(obras.keys()))
            c = st.selectbox("Categoria", list(cats.keys()))
            d = st.text_input("Descrição")
            v = st.number_input("Valor", min_value=0.0)
            foto = st.camera_input("Capturar Recibo")
            if st.button("SALVAR", use_container_width=True, type="primary"):
                url = None
                if foto:
                    n_arq = f"{uuid.uuid4()}.jpg"
                    supabase.storage.from_("comprovantes").upload(n_arq, foto.getvalue())
                    url = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{n_arq}"
                supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v, "url_comprovante": url}).execute()
                st.success("Salvo com sucesso!"); st.session_state.pagina = 'RESUMO'; st.rerun()

    elif pag == 'LISTA':
        st.markdown("### 📋 Histórico & PDF")
        obras = listar_obras()
        if obras:
            o_f = st.selectbox("Selecione a Obra:", list(obras.keys()))
            col1, col2 = st.columns(2)
            d_ini = col1.date_input("Início:", datetime.now().replace(day=1))
            d_fim = col2.date_input("Fim:", datetime.now())
            
            dados = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("obra_id", obras[o_f]).gte("created_at", d_ini).lte("created_at", f"{d_fim} 23:59:59").order("created_at", desc=True).execute().data
            
            if dados:
                # Gerar e disponibilizar PDF
                df_dados = pd.DataFrame(dados)
                pdf_bytes = gerar_pdf(df_dados, o_f)
                st.download_button("📥 Baixar Relatório PDF", pdf_bytes, f"Relatorio_{o_f}.pdf", "application/pdf", use_container_width=True)
                
                for g in dados:
                    with st.expander(f"{g['descricao']} | {formatar_real(g['valor'])}"):
                        if g.get('url_comprovante'): st.image(g['url_comprovante'])
                        if st.button("🗑️ Excluir Gasto", key=f"del_{g['id']}", use_container_width=True):
                            supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute()
                            st.rerun()
            else:
                st.warning("Nenhum gasto neste período.")

    elif pag == 'OBRA':
        st.markdown("### 🏗️ Gestão de Obras")
        with st.container(border=True):
            n = st.text_input("Nome"); v = st.number_input("Orçamento", min_value=0.0)
            if st.button("Cadastrar", use_container_width=True):
                supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
                st.success("Obra criada!"); st.session_state.pagina = 'RESUMO'; st.rerun()
