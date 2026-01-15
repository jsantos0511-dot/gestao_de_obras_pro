import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import uuid
from fpdf import FPDF
from datetime import datetime

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

def exportar_pdf(df, nome_obra):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, f"Relatorio de Gastos - {nome_obra}", ln=True, align="C")
    pdf.set_font("Arial", "B", 10)
    pdf.ln(10)
    
    # Cabeçalho da Tabela
    pdf.cell(30, 10, "Data", 1)
    pdf.cell(80, 10, "Descricao", 1)
    pdf.cell(40, 10, "Categoria", 1)
    pdf.cell(40, 10, "Valor", 1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 10)
    total = 0
    for _, row in df.iterrows():
        data_f = datetime.strptime(row['created_at'][:10], '%Y-%m-%d').strftime('%d/%m/%Y')
        pdf.cell(30, 10, data_f, 1)
        pdf.cell(80, 10, str(row['descricao'])[:40], 1)
        pdf.cell(40, 10, row['categorias_obra']['nome_categoria'], 1)
        pdf.cell(40, 10, formatar_real(row['valor']), 1)
        pdf.ln()
        total += row['valor']
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, f"TOTAL ACUMULADO: {formatar_real(total)}", ln=True, align="R")
    return pdf.output(dest='S').encode('latin-1')

# --- 3. CSS (DESIGN PRESERVADO) ---
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
            st.markdown(f'<div class="data-card"><small>INVESTIMENTO</small><h2>{formatar_real(gasto)}</h2><hr><small>SALDO: {formatar_real(float(info["orcamento_previsto"]) - gasto)}</small></div>', unsafe_allow_html=True)
            if res_s.data: st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'GASTO':
        st.markdown("### 💸 Novo Lançamento")
        obras, cats = listar_obras(), listar_categorias()
        with st.container(border=True):
            o_sel = st.selectbox("Obra", list(obras.keys()))
            c_sel = st.selectbox("Categoria", list(cats.keys()))
            desc = st.text_input("Descrição")
            valor = st.number_input("Valor Pago", min_value=0.0)
            foto = st.camera_input("Capturar Recibo")
            
            if st.button("SALVAR", use_container_width=True, type="primary"):
                url_final = None
                if foto:
                    nome_img = f"{uuid.uuid4()}.jpg"
                    supabase.storage.from_("comprovantes").upload(nome_img, foto.getvalue())
                    url_final = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{nome_img}"
                
                supabase.table("lancamentos_obra").insert({
                    "obra_id": obras[o_sel], "categoria_id": cats[c_sel],
                    "descricao": desc, "valor": valor, "url_comprovante": url_final
                }).execute()
                st.success("Salvo com sucesso!"); st.session_state.pagina = 'RESUMO'; st.rerun()

    elif pag == 'LISTA':
        st.markdown("### 📋 Relatórios & Filtros")
        obras = listar_obras()
        if obras:
            o_f = st.selectbox("Selecione a Obra:", list(obras.keys()))
            
            # --- NOVO: FILTRO POR DATA ---
            col_d1, col_d2 = st.columns(2)
            data_ini = col_d1.date_input("De:", datetime.now().replace(day=1))
            data_fim = col_d2.date_input("Até:", datetime.now())
            
            query = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("obra_id", obras[o_f])
            query = query.gte("created_at", data_ini).lte("created_at", f"{data_fim} 23:59:59")
            dados = query.order("created_at", desc=True).execute().data
            
            if dados:
                df_dados = pd.DataFrame(dados)
                
                # --- NOVO: BOTÃO EXPORTAR PDF ---
                pdf_bytes = exportar_pdf(df_dados, o_f)
                st.download_button(label="📥 Baixar Relatório em PDF", data=pdf_bytes, file_name=f"Relatorio_{o_f}.pdf", mime="application/pdf", use_container_width=True)
                
                st.markdown("---")
                for g in dados:
                    with st.expander(f"{g['descricao']} | {formatar_real(g['valor'])}"):
                        st.write(f"Data: {datetime.strptime(g['created_at'][:10], '%Y-%m-%d').strftime('%d/%m/%Y')}")
                        if g.get('url_comprovante'): st.image(g['url_comprovante'])
                        
                        # --- NOVO: BOTÃO EXCLUIR ---
                        if st.button(f"🗑️ Excluir Lançamento", key=f"del_{g['id']}", use_container_width=True):
                            # Se tiver foto, apaga do Storage primeiro
                            if g.get('url_comprovante'):
                                nome_arq = g['url_comprovante'].split('/')[-1]
                                try: supabase.storage.from_("comprovantes").remove([nome_arq])
                                except: pass
                            
                            supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute()
                            st.toast("Lançamento excluído!")
                            st.rerun()
            else:
                st.info("Nenhum gasto encontrado neste período.")

    elif pag == 'OBRA':
        st.markdown("### 🏗️ Gestão de Obras")
        with st.container(border=True):
            n = st.text_input("Nome da Obra")
            v = st.number_input("Orçamento Total", min_value=0.0)
            if st.button("Cadastrar", use_container_width=True):
                supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
                st.success("Obra cadastrada!"); st.session_state.pagina = 'RESUMO'; st.rerun()
