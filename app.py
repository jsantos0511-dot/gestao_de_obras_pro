import streamlit as st
import pandas as pd
from supabase import create_client, Client
import uuid
import re
from datetime import datetime
from fpdf import FPDF
import io

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

# --- 2. GESTÃO DE SESSÃO ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'user_perfil' not in st.session_state: st.session_state.user_perfil = None
if 'pagina' not in st.session_state: st.session_state.pagina = 'RESUMO'
if 'menu_aberto' not in st.session_state: st.session_state.menu_aberto = False
if 'form_version' not in st.session_state: st.session_state.form_version = 0

if 'forn_edit_id' not in st.session_state: st.session_state.forn_edit_id = None
if 'clie_edit_id' not in st.session_state: st.session_state.clie_edit_id = None
if 'obra_edit_id' not in st.session_state: st.session_state.obra_edit_id = None

def limpar_campos():
    st.session_state.form_version += 1
    st.session_state.forn_edit_id = None
    st.session_state.clie_edit_id = None
    st.session_state.obra_edit_id = None

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

# --- 3. FORMATADORES ---
def formatar_real(valor):
    if valor is None: valor = 0
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# --- 4. ESTILO VISUAL ---
st.markdown(f"""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {{display: none;}}
    .block-container {{ padding-top: 2rem !important; }}
    .stImage > img {{ border-radius: 0px !important; display: block; margin: 0 auto; }}
    .main-title {{ color: #FFFFFF !important; font-size: 1.4rem; font-weight: 700; margin-bottom: 15px; }}
    .metric-container {{
        background: #1E1E1E; padding: 15px; border-radius: 10px; 
        border: 1px solid #333; margin-bottom: 10px; text-align: center;
    }}
    .metric-label {{ color: #AAAAAA; font-size: 0.70rem; font-weight: 600; text-transform: uppercase; }}
    .metric-value {{ color: #FFFFFF; font-size: 1.1rem; font-weight: 800; }}
    .data-card {{ background: #F8F9FA; padding: 20px; border-radius: 8px; border: 1px solid #E9ECEF; margin-bottom: 15px; color: #1e1e1e; }}
    div.stButton > button[key="trigger"] {{ background-color: transparent !important; color: #FFFFFF !important; width: 45px !important; height: 45px !important; border: none !important; font-size: 30px !important; }}
    .nav-card button {{ width: 100% !important; height: 50px !important; font-weight: 600 !important; margin-bottom: 8px !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. CABEÇALHO E LOGIN ---
if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image(LOGO_URL, width=220)
        with st.container(border=True):
            u_email = st.text_input("E-mail")
            u_senha = st.text_input("Senha", type="password")
            if st.button("ENTRAR", use_container_width=True, type="primary"):
                if realizar_login(u_email, u_senha): st.rerun()
                else: st.error("Acesso negado.")
    st.stop()

h1, h2 = st.columns([0.15, 0.85])
with h1:
    icon = "×" if st.session_state.menu_aberto else "☰"
    if st.button(icon, key="trigger"):
        st.session_state.menu_aberto = not st.session_state.menu_aberto
        st.rerun()
with h2:
    st.image(LOGO_URL, width=195)
st.markdown("---") 

# --- 6. FUNÇÕES DE DADOS ---
def listar_obras():
    try: return {i['nome_obra']: i for i in supabase.table("obras").select("*").execute().data}
    except: return {}

def listar_categorias():
    try: return {i['nome_categoria']: i['id'] for i in supabase.table("categorias_obra").select("*").execute().data}
    except: return {}

def listar_fornecedores():
    try: return {i['nome_fornecedor']: i for i in supabase.table("fornecedores").select("*").order("nome_fornecedor").execute().data}
    except: return {}

def listar_clientes():
    try: return {i['nome_cliente']: i for i in supabase.table("clientes").select("*").order("nome_cliente").execute().data}
    except: return {}

def gerar_pdf(df, nome_obra):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, f"Relatorio - {nome_obra}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(30, 10, "Data", 1); pdf.cell(80, 10, "Descricao", 1); pdf.cell(40, 10, "Categoria", 1); pdf.cell(40, 10, "Valor", 1); pdf.ln()
    pdf.set_font("Helvetica", "", 10)
    for _, r in df.iterrows():
        pdf.cell(30, 10, str(r['created_at'])[:10], 1)
        pdf.cell(80, 10, str(r['descricao'])[:40], 1)
        pdf.cell(40, 10, str(r.get('categorias_obra', {}).get('nome_categoria', 'N/A')), 1)
        pdf.cell(40, 10, f"R$ {r['valor']:,.2f}", 1); pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 7. MENU ---
if st.session_state.menu_aberto:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    if st.button("📊 Dashboard"): st.session_state.pagina='RESUMO'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("💸 Lançar Gasto"): st.session_state.pagina='GASTO'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("🏗️ Minhas Obras"): st.session_state.pagina='OBRA'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("📋 Relatórios"): st.session_state.pagina='LISTA'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("👤 Clientes"): st.session_state.pagina='CLIE'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("🤝 Fornecedores"): st.session_state.pagina='FORN'; st.session_state.menu_aberto=False; st.rerun()
    if st.session_state.user_perfil == 'ADMIN':
        if st.button("👥 Equipe"): st.session_state.pagina='USUARIOS'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("Sair"): st.session_state.logado = False; st.session_state.menu_aberto=False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. TELAS ---
else:
    pag, ver = st.session_state.pagina, st.session_state.form_version

    if pag == 'RESUMO':
        obs = listar_obras()
        if obs:
            sel = st.selectbox("Selecione a Obra", [""] + list(obs.keys()))
            if sel:
                o = obs[sel]
                gastos = supabase.table("lancamentos_obra").select("valor").eq("obra_id", o['id']).execute().data
                total_g = sum(float(g['valor']) for g in gastos)
                orc, luc_p, imp_p = float(o['orcamento_previsto']), float(o['lucro_estimado']), float(o['impostos_estimados'])
                v_imp = orc * (imp_p/100)
                l_real = orc - total_g - v_imp
                
                c1,c2,c3,c4 = st.columns(4)
                c1.markdown(f'<div class="metric-container"><p class="metric-label">Orçado</p><p class="metric-value">{formatar_real(orc)}</p></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-container"><p class="metric-label">Exp. Lucro</p><p class="metric-value">{formatar_real(orc*(luc_p/100))}</p></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-container"><p class="metric-label">Imposto</p><p class="metric-value">{formatar_real(v_imp)}</p></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="metric-container"><p class="metric-label">Lucro Real</p><p class="metric-value">{formatar_real(l_real)}</p></div>', unsafe_allow_html=True)

    elif pag == 'GASTO':
        st.markdown("### Lançar Gasto")
        obs, cats, forns = listar_obras(), listar_categorias(), listar_fornecedores()
        with st.container(border=True):
            o_s = st.selectbox("Obra*", [""] + list(obs.keys()))
            c_s = st.selectbox("Categoria*", [""] + list(cats.keys()))
            f_s = st.selectbox("Fornecedor*", [""] + list(forns.keys()))
            desc = st.text_input("Descrição")
            val = st.number_input("Valor (R$)", min_value=0.0)
            status = st.selectbox("Status", ["", "Pago", "Pendente"])
            foto = st.camera_input("Recibo")
            if st.button("SALVAR GASTO", use_container_width=True, type="primary"):
                if o_s and c_s and val > 0:
                    url = None
                    if foto:
                        n = f"{uuid.uuid4()}.jpg"
                        supabase.storage.from_("comprovantes").upload(n, foto.getvalue())
                        url = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{n}"
                    d = {"obra_id": obs[o_s]['id'], "categoria_id": cats[c_s], "fornecedor_id": forns[f_s]['id'], "descricao": desc, "valor": val, "status_pagamento": status, "url_comprovante": url}
                    supabase.table("lancamentos_obra").insert(d).execute()
                    st.success("Salvo!"); st.rerun()

    elif pag == 'OBRA':
        st.markdown("### Gestão de Obras")
        clis = listar_clientes()
        with st.container(border=True):
            nome = st.text_input("Nome da Obra*")
            cli = st.selectbox("Cliente*", [""] + list(clis.keys()))
            orc = st.number_input("Orçamento Previsto", min_value=0.0)
            luc = st.number_input("Lucro Estimado (%)", min_value=0.0)
            imp = st.number_input("Imposto (%)", min_value=0.0)
            tipo = st.selectbox("Tipo", ["", "Residencial", "Comercial", "Industrial", "Reforma"])
            loc = st.text_input("Localização")
            if st.button("CADASTRAR OBRA", use_container_width=True, type="primary"):
                if nome and cli:
                    p = {"nome_obra": nome, "cliente_id": clis[cli]['id'], "orcamento_previsto": orc, "lucro_estimado": luc, "impostos_estimados": imp, "tipo_obra": tipo, "local_obra": loc}
                    supabase.table("obras").insert(p).execute(); st.rerun()
        for o in (supabase.table("obras").select("*").execute().data or []):
            with st.expander(f"🏗️ {o['nome_obra']}"):
                st.write(f"Orçamento: {formatar_real(o['orcamento_previsto'])} | Imposto: {o['impostos_estimados']}%")

    elif pag == 'FORN':
        st.markdown("### Fornecedores")
        df_f = {"nome_fornecedor": "", "representante": "", "telefone": "", "whatsapp": "", "cnpj": "", "email": "", "endereco": ""}
        if st.session_state.forn_edit_id:
            res = supabase.table("fornecedores").select("*").eq("id", st.session_state.forn_edit_id).single().execute()
            if res.data: df_f = res.data
        with st.container(border=True):
            fn = st.text_input("Empresa*", value=df_f["nome_fornecedor"])
            fr = st.text_input("Representante", value=df_f["representante"])
            ft = st.text_input("Telefone", value=df_f["telefone"])
            fc = st.text_input("CNPJ", value=df_f["cnpj"])
            fe = st.text_input("E-mail", value=df_f["email"])
            fa = st.text_area("Endereço", value=df_f["endereco"])
            if st.button("SALVAR FORNECEDOR", use_container_width=True):
                p = {"nome_fornecedor": fn, "representante": fr, "telefone": ft, "cnpj": fc, "email": fe, "endereco": fa}
                if st.session_state.forn_edit_id: supabase.table("fornecedores").update(p).eq("id", st.session_state.forn_edit_id).execute()
                else: supabase.table("fornecedores").insert(p).execute()
                limpar_campos(); st.rerun()
        for f in (supabase.table("fornecedores").select("*").order("nome_fornecedor").execute().data or []):
            with st.expander(f"🏢 {f['nome_fornecedor']}"):
                if st.button("Editar", key=f"ef_{f['id']}"): st.session_state.forn_edit_id=f['id']; st.rerun()

    elif pag == 'CLIE':
        st.markdown("### Clientes")
        df_c = {"nome_cliente": "", "representante": "", "telefone": "", "cnpj": "", "email": "", "endereco": ""}
        if st.session_state.clie_edit_id:
            res = supabase.table("clientes").select("*").eq("id", st.session_state.clie_edit_id).single().execute()
            if res.data: df_c = res.data
        with st.container(border=True):
            cn = st.text_input("Nome*", value=df_c["nome_cliente"])
            ct = st.text_input("Telefone", value=df_c["telefone"])
            cc = st.text_input("CNPJ/CPF", value=df_c["cnpj"])
            ce = st.text_input("E-mail", value=df_c["email"])
            if st.button("SALVAR CLIENTE", use_container_width=True):
                p = {"nome_cliente": cn, "telefone": ct, "cnpj": cc, "email": ce}
                if st.session_state.clie_edit_id: supabase.table("clientes").update(p).eq("id", st.session_state.clie_edit_id).execute()
                else: supabase.table("clientes").insert(p).execute()
                limpar_campos(); st.rerun()

    elif pag == 'LISTA':
        st.markdown("### Relatórios")
        obs = listar_obras()
        if obs:
            o_f = st.selectbox("Obra", [""] + list(obs.keys()))
            if o_f:
                dados = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("obra_id", obs[o_f]['id']).execute().data
                if dados:
                    df = pd.DataFrame(dados)
                    st.download_button("📥 PDF", gerar_pdf(df, o_f), f"{o_f}.pdf")
                    for g in dados:
                        with st.expander(f"{g['descricao']} - {formatar_real(g['valor'])}"):
                            if st.button("Excluir", key=f"del_{g['id']}"):
                                supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute(); st.rerun()

    elif pag == 'USUARIOS' and st.session_state.user_perfil == 'ADMIN':
        st.markdown("### Gestão de Equipe")
        with st.container(border=True):
            em = st.text_input("E-mail")
            se = st.text_input("Senha", type="password")
            pe = st.selectbox("Perfil", ["", "LANCADOR", "ADMIN"])
            if st.button("CADASTRAR"):
                supabase.table("usuarios").insert({"email": em, "senha": se, "perfil": pe}).execute(); st.rerun()
