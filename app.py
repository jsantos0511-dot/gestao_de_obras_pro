import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import uuid
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURAÇÃO DA MARCA ---
LOGO_URL = "https://ryzcivhjohgtzixqflwo.supabase.co/storage/v1/object/public/comprovantes/logo_rosecon.png" 

# --- 1. CONEXÃO ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="ROSECON Pro", layout="centered")

# --- 2. GESTÃO DE SESSÃO E LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'user_perfil' not in st.session_state: st.session_state.user_perfil = None
if 'pagina' not in st.session_state: st.session_state.pagina = 'RESUMO'

def realizar_login(email, senha):
    try:
        res = supabase.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
        if res.data:
            st.session_state.logado = True
            st.session_state.user_perfil = res.data[0]['perfil']
            st.session_state.pagina = 'RESUMO'
            return True
    except: pass
    return False

# --- 3. ESTILO VISUAL (BRANDING + MENU + LARGURA 70%) ---
st.markdown(f"""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {{display: none;}}
    .block-container {{ padding-top: 1rem !important; }}
    
    img {{
        border-radius: 0px !important;
    }}
    
    .data-card {{ 
        background: #ffffff; padding: 20px; border-radius: 15px; 
        border: 1px solid #eee; margin-bottom: 15px; color: #1e1e1e; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    .data-card h2 {{ color: #1E1E1E !important; margin: 0; font-weight: 800; }}
    .data-card small {{ color: #666 !important; font-weight: 700; text-transform: uppercase; }}
    
    div.stButton > button[key="trigger"] {{
        background-color: transparent !important; 
        color: #1E1E1E !important;
        width: 50px !important; height: 50px !important;
        border: none !important;
        font-size: 35px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-top: 5px !important;
    }}
    
    /* Menu de Navegação - Largura 70% e Centralizado */
    .nav-card {{
        width: 70% !important;
        margin: 0 auto !important;
    }}
    
    .nav-card button {{ 
        width: 100% !important; height: 70px !important; 
        border-radius: 12px !important; font-weight: 700 !important; 
        margin-bottom: 10px !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 4. TELA DE LOGIN ---
if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.image(LOGO_URL, width=220)
        st.markdown("<h4 style='text-align:center;'>Acesso ao Sistema</h4>", unsafe_allow_html=True)
        with st.container(border=True):
            u_email = st.text_input("E-mail")
            u_senha = st.text_input("Senha", type="password")
            if st.button("ENTRAR", use_container_width=True, type="primary"):
                if realizar_login(u_email, u_senha): st.rerun()
                else: st.error("E-mail ou senha inválidos.")
    st.stop()

# --- 5. CABEÇALHO ALINHADO ---
# Colunas ajustadas para permitir a logo maior na mesma linha
head_col1, head_col2 = st.columns([0.2, 0.8])
with head_col1:
    icon = "×" if st.session_state.get('menu_aberto', False) else "☰"
    if st.button(icon, key="trigger"):
        st.session_state.menu_aberto = not st.session_state.get('menu_aberto', False)
        st.rerun()
with head_col2:
    # Logo aumentada em 20% (de 160 para 195)
    st.image(LOGO_URL, width=195)

st.markdown("---") 

# --- 6. FUNÇÕES DE APOIO ---
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
    pdf.set_font("Arial", "B", 10)
    pdf.cell(25, 10, "Data", 1); pdf.cell(75, 10, "Descricao", 1); pdf.cell(55, 10, "Categoria", 1); pdf.cell(35, 10, "Valor", 1); pdf.ln()
    pdf.set_font("Arial", "", 9)
    total = 0
    for _, row in df.iterrows():
        dt = datetime.strptime(row['created_at'][:10], '%Y-%m-%d').strftime('%d/%m/%Y')
        pdf.cell(25, 10, dt, 1); pdf.cell(75, 10, str(row['descricao'])[:40], 1)
        pdf.cell(55, 10, str(row['categorias_obra']['nome_categoria']), 1); pdf.cell(35, 10, f"R$ {row['valor']:,.2f}", 1); pdf.ln()
        total += row['valor']
    pdf.ln(5); pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"TOTAL: {formatar_real(total)}", ln=True, align="R")
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 7. LOGICA DO MENU (70% LARGURA) ---
if st.session_state.get('menu_aberto', False):
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    perfil = st.session_state.user_perfil
    
    if st.button("📊 Dashboard"): st.session_state.pagina='RESUMO'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("💸 Lançar Gasto"): st.session_state.pagina='GASTO'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("📋 Relatórios"): st.session_state.pagina='LISTA'; st.session_state.menu_aberto=False; st.rerun()
    
    if perfil == 'ADMIN':
        if st.button("🏗️ Minhas Obras"): st.session_state.pagina='OBRA'; st.session_state.menu_aberto=False; st.rerun()
        if st.button("👥 Gestão de Equipe"): st.session_state.pagina='USUARIOS'; st.session_state.menu_aberto=False; st.rerun()
            
    if st.button("Sair (Logout)", type="secondary"):
        st.session_state.logado = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. TELAS ---
else:
    pag = st.session_state.pagina
    perfil = st.session_state.user_perfil

    if pag == 'RESUMO':
        obras = listar_obras()
        if obras:
            sel = st.selectbox("Selecione a Obra", list(obras.keys()), label_visibility="collapsed")
            res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': obras[sel]}).execute()
            gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
            
            if perfil == 'ADMIN':
                info = supabase.table("obras").select("*").eq("id", obras[sel]).single().execute().data
                st.markdown(f'<div class="data-card"><small>INVESTIMENTO TOTAL</small><h2>{formatar_real(gasto)}</h2><hr style="border:0.5px solid #eee;"><small>SALDO EM CAIXA: <b>{formatar_real(float(info["orcamento_previsto"]) - gasto)}</b></small></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="data-card"><small>GASTO ACUMULADO</small><h2>{formatar_real(gasto)}</h2></div>', unsafe_allow_html=True)
            
            if res_s.data:
                df_chart = pd.DataFrame(res_s.data).set_index('nome_categoria')
                st.bar_chart(df_chart)

    elif pag == 'GASTO':
        st.markdown("### 💸 Lançamento de Despesa")
        obras, cats = listar_obras(), listar_categorias()
        with st.container(border=True):
            o = st.selectbox("Selecione a Obra", list(obras.keys())); c = st.selectbox("Categoria", list(cats.keys()))
            d = st.text_input("Descrição"); v = st.number_input("Valor Pago", min_value=0.0)
            foto = st.camera_input("Foto do Recibo")
            if st.button("SALVAR LANÇAMENTO", use_container_width=True, type="primary"):
                url = None
                if foto:
                    n_arq = f"{uuid.uuid4()}.jpg"
                    supabase.storage.from_("comprovantes").upload(n_arq, foto.getvalue())
                    url = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{n_arq}"
                supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "descricao": d, "valor": v, "url_comprovante": url}).execute()
                st.success("Lançamento efetuado!"); st.session_state.pagina = 'LISTA'; st.rerun()

    elif pag == 'LISTA':
        st.markdown("### 📋 Histórico & Relatórios")
        obras = listar_obras()
        if obras:
            o_f = st.selectbox("Filtrar por Obra:", list(obras.keys()))
            c1, c2 = st.columns(2)
            d_i = c1.date_input("Início:", datetime.now().replace(day=1))
            d_f = c2.date_input("Fim:", datetime.now())
            
            dados = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("obra_id", obras[o_f]).gte("created_at", d_i).lte("created_at", f"{d_f} 23:59:59").order("created_at", desc=True).execute().data
            
            if dados:
                if perfil == 'ADMIN':
                    pdf_b = gerar_pdf(pd.DataFrame(dados), o_f)
                    st.download_button("📥 Baixar Relatório PDF", pdf_b, f"Relatorio_{o_f}.pdf", "application/pdf", use_container_width=True)
                
                for g in dados:
                    with st.expander(f"{g['descricao']} | {formatar_real(g['valor'])}"):
                        if g.get('url_comprovante'): st.image(g['url_comprovante'])
                        if st.button("🗑️ Excluir Registro", key=f"del_{g['id']}", use_container_width=True):
                            if g.get('url_comprovante'):
                                try: supabase.storage.from_("comprovantes").remove([g['url_comprovante'].split('/')[-1]])
                                except: pass
                            supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute()
                            st.rerun()

    elif pag == 'OBRA' and perfil == 'ADMIN':
        st.markdown("### 🏗️ Cadastrar Obras")
        with st.container(border=True):
            n = st.text_input("Nome da Obra"); v = st.number_input("Orçamento Previsto", min_value=0.0)
            if st.button("CADASTRAR OBRA", use_container_width=True):
                supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute()
                st.success("Obra cadastrada!"); st.session_state.pagina = 'RESUMO'; st.rerun()

    elif pag == 'USUARIOS' and perfil == 'ADMIN':
        st.markdown("### 👥 Gestão de Equipe")
        with st.container(border=True):
            nv_email = st.text_input("E-mail"); nv_senha = st.text_input("Senha")
            nv_perfil = st.selectbox("Perfil", ["LANCADOR", "ADMIN"])
            if st.button("CRIAR NOVA CONTA", use_container_width=True, type="primary"):
                supabase.table("usuarios").insert({"email": nv_email, "senha": nv_senha, "perfil": nv_perfil}).execute()
                st.success("Usuário criado!"); st.rerun()
        st.markdown("---")
        lista = supabase.table("usuarios").select("email, perfil").execute().data
        st.table(pd.DataFrame(lista))
