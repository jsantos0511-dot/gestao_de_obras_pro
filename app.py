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

# --- 2. GESTÃO DE SESSÃO ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'user_perfil' not in st.session_state: st.session_state.user_perfil = None

def realizar_login(email, senha):
    res = supabase.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
    if res.data:
        st.session_state.logado = True
        st.session_state.user_perfil = res.data[0]['perfil']
        st.session_state.pagina = 'RESUMO'
        return True
    return False

# --- 3. ESTILO VISUAL ---
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
    .block-container { padding-top: 1rem !important; }
    .data-card { background: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #eee; margin-bottom: 15px; color: #1e1e1e; box-shadow: 0 4px 6px rgba(0,0,0,0.05);}
    .data-card h2 { color: #1E1E1E !important; margin: 0; }
    div.stButton > button[key="trigger"] {
        background-color: #1E1E1E !important; width: 70px !important; height: 70px !important;
        border-radius: 20px !important; margin: 0 auto 15px auto !important; display: flex !important;
    }
    .nav-card button { width: 100% !important; height: 80px !important; border-radius: 15px !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if not st.session_state.logado:
    st.markdown("<h2 style='text-align:center;'>ROSECON Pro</h2>", unsafe_allow_html=True)
    with st.container(border=True):
        u_email = st.text_input("E-mail")
        u_senha = st.text_input("Senha", type="password")
        if st.button("ACESSAR", use_container_width=True, type="primary"):
            if realizar_login(u_email, u_senha): st.rerun()
            else: st.error("Erro: Verifique suas credenciais.")
    st.stop()

# --- FUNÇÕES ---
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
    pdf.add_page(); pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Relatorio - {nome_obra}", ln=True, align="C"); pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(25, 10, "Data", 1); pdf.cell(75, 10, "Descricao", 1); pdf.cell(55, 10, "Categoria", 1); pdf.cell(35, 10, "Valor", 1); pdf.ln()
    pdf.set_font("Arial", "", 9)
    total = 0
    for _, row in df.iterrows():
        dt = datetime.strptime(row['created_at'][:10], '%Y-%m-%d').strftime('%d/%m/%Y')
        pdf.cell(25, 10, dt, 1); pdf.cell(75, 10, str(row['descricao'])[:40], 1)
        pdf.cell(55, 10, str(row['categorias_obra']['nome_categoria']), 1); pdf.cell(35, 10, f"R$ {row['valor']:,.2f}", 1); pdf.ln()
        total += row['valor']
    pdf.ln(5); pdf.set_font("Arial", "B", 12); pdf.cell(190, 10, f"TOTAL: {formatar_real(total)}", ln=True, align="R")
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- NAVEGAÇÃO ---
if 'menu_aberto' not in st.session_state: st.session_state.menu_aberto = False

icon = "×" if st.session_state.menu_aberto else "☰"
if st.button(icon, key="trigger"):
    st.session_state.menu_aberto = not st.session_state.menu_aberto; st.rerun()

if st.session_state.menu_aberto:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊\nDashboard"): st.session_state.pagina='RESUMO'; st.session_state.menu_aberto=False; st.rerun()
        if st.button("💸\nLançar Gasto"): st.session_state.pagina='GASTO'; st.session_state.menu_aberto=False; st.rerun()
    with c2:
        if st.session_state.user_perfil == 'ADMIN':
            if st.button("🏗️\nCadastrar Obras"): st.session_state.pagina='OBRA'; st.session_state.menu_aberto=False; st.rerun()
        else:
            st.button("🏗️\nCadastrar Obras", disabled=True)
        if st.button("📋\nRelatórios"): st.session_state.pagina='LISTA'; st.session_state.menu_aberto=False; st.rerun()
    
    if st.button("Sair (Logout)", use_container_width=True):
        st.session_state.logado = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    pag = st.session_state.pagina
    perfil = st.session_state.user_perfil

    if pag == 'RESUMO':
        obras = listar_obras()
        if obras:
            sel = st.selectbox("Obra Ativa", list(obras.keys()), label_visibility="collapsed")
            res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': obras[sel]}).execute()
            gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
            
            # ADMIN vê saldo, LANCADOR vê apenas gasto acumulado
            if perfil == 'ADMIN':
                info = supabase.table("obras").select("*").eq("id", obras[sel]).single().execute().data
                st.markdown(f'<div class="data-card"><small>GASTO TOTAL</small><h2>{formatar_real(gasto)}</h2><hr><small>SALDO: <b>{formatar_real(float(info["orcamento_previsto"]) - gasto)}</b></small></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="data-card"><small>GASTO ACUMULADO NA OBRA</small><h2>{formatar_real(gasto)}</h2></div>', unsafe_allow_html=True)
            
            if res_s.data: st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'GASTO':
        st.markdown("### 💸 Lançamento de Gasto")
        obras, cats = listar_obras(), listar_categorias()
        with st.container(border=True):
            o = st.selectbox("Obra", list(obras.keys())); c = st.selectbox("Categoria", list(cats.keys()))
            d = st.text_input("Descrição"); v = st.number_input("Valor Pago", min_value=0.0)
            foto = st.camera_input("Foto do Recibo")
            if st.button("FINALIZAR LANÇAMENTO", use_container_width=True, type="primary"):
                url = None
                if foto:
                    n_arq = f"{uuid.uuid4()}.jpg"
                    supabase.storage.from_("comprovantes").upload(n_arq, foto.getvalue())
                    url = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{n_arq}"
                supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v, "url_comprovante": url}).execute()
                st.success("Lançamento salvo!"); st.session_state.pagina = 'LISTA'; st.rerun()

    elif pag == 'LISTA':
        st.markdown("### 📋 Histórico e Relatórios")
        obras = listar_obras()
        if obras:
            o_f = st.selectbox("Selecione a Obra:", list(obras.keys()))
            col1, col2 = st.columns(2)
            d_ini = col1.date_input("De:", datetime.now().replace(day=1))
            d_fim = col2.date_input("Até:", datetime.now())
            
            dados = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("obra_id", obras[o_f]).gte("created_at", d_ini).lte("created_at", f"{d_fim} 23:59:59").order("created_at", desc=True).execute().data
            
            if dados:
                # PDF só para ADMIN
                if perfil == 'ADMIN':
                    pdf_bytes = gerar_pdf(pd.DataFrame(dados), o_f)
                    st.download_button("📥 Baixar Relatório PDF", pdf_bytes, f"Relatorio_{o_f}.pdf", "application/pdf", use_container_width=True)
                
                for g in dados:
                    with st.expander(f"{g['descricao']} | {formatar_real(g['valor'])}"):
                        if g.get('url_comprovante'): st.image(g['url_comprovante'])
                        # Ambos podem excluir (Lançador corrige erros, Admin audita)
                        if st.button("🗑️ Excluir Registro", key=f"del_{g['id']}", use_container_width=True):
                            if g.get('url_comprovante'):
                                try: supabase.storage.from_("comprovantes").remove([g['url_comprovante'].split('/')[-1]])
                                except: pass
                            supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute()
                            st.rerun()
            else:
                st.info("Nenhum registro encontrado.")

    elif pag == 'OBRA' and perfil == 'ADMIN':
        st.markdown("### 🏗️ Cadastrar Obras")
        with st.container(border=True):
            n = st.text_input("Nome da Obra"); v = st.number_input("Orçamento Previsto", min_value=0.0)
            if st.button("CADASTRAR OBRA", use_container_width=True):
                supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
                st.success("Obra cadastrada!"); st.session_state.pagina = 'RESUMO'; st.rerun()
