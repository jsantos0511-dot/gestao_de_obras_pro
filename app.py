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

def limpar_campos():
    st.session_state.form_version += 1
    st.session_state.forn_edit_id = None
    st.session_state.clie_edit_id = None

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
    .metric-container {{
        background: #1E1E1E; padding: 15px; border-radius: 10px; 
        border: 1px solid #333; margin-bottom: 10px; text-align: center;
    }}
    .metric-label {{ color: #AAAAAA; font-size: 0.70rem; font-weight: 600; text-transform: uppercase; }}
    .metric-value {{ color: #FFFFFF; font-size: 1.1rem; font-weight: 800; }}
    .data-card {{ 
        background: #F8F9FA; padding: 20px; border-radius: 8px; 
        border: 1px solid #E9ECEF; margin-bottom: 15px; color: #1e1e1e; 
    }}
    div.stButton > button[key="trigger"] {{
        background-color: transparent !important; color: #FFFFFF !important;
        width: 45px !important; height: 45px !important; border: none !important; font-size: 30px !important;
    }}
    .nav-card button {{ width: 100% !important; height: 50px !important; font-weight: 600 !important; margin-bottom: 8px !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. TELA DE LOGIN ---
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

# --- 6. CABEÇALHO ---
h1, h2 = st.columns([0.15, 0.85])
with h1:
    icon = "×" if st.session_state.menu_aberto else "☰"
    if st.button(icon, key="trigger"):
        st.session_state.menu_aberto = not st.session_state.menu_aberto
        st.rerun()
with h2:
    st.image(LOGO_URL, width=195)
st.markdown("---") 

# --- 7. FUNÇÕES DE APOIO ---
def listar_obras_unicas():
    try:
        res = supabase.table("lancamentos_obra").select("nome_obra, orcamento_previsto, lucro_estimado, impostos_estimados, tipo_obra").execute()
        df = pd.DataFrame(res.data)
        if df.empty: return {}
        # Pega o registro mais recente de cada obra para ter os valores configurados
        return df.drop_duplicates(subset=['nome_obra'], keep='last').set_index('nome_obra').to_dict('index')
    except: return {}

def listar_categorias():
    try:
        res = supabase.table("categorias_obra").select("id, nome_categoria").execute()
        return {item['nome_categoria']: item['id'] for item in res.data}
    except: return {}

def listar_fornecedores():
    try:
        res = supabase.table("fornecedores").select("*").order("nome_fornecedor").execute()
        return {item['nome_fornecedor']: item for item in res.data}
    except: return {}

def listar_clientes():
    try:
        res = supabase.table("clientes").select("*").order("nome_cliente").execute()
        return {item['nome_cliente']: item for item in res.data}
    except: return {}

def gerar_pdf(df, nome_obra):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, f"Relatorio ROSECON - {nome_obra}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(25, 10, "Data", 1); pdf.cell(60, 10, "Descricao", 1); pdf.cell(45, 10, "Categoria", 1); pdf.cell(30, 10, "Valor", 1); pdf.cell(30, 10, "Status", 1); pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    total = 0
    for _, row in df.iterrows():
        dt = datetime.strptime(row['created_at'][:10], '%Y-%m-%d').strftime('%d/%m/%Y')
        pdf.cell(25, 10, dt, 1); pdf.cell(60, 10, str(row['descricao'])[:30], 1)
        pdf.cell(45, 10, str(row['categorias_obra']['nome_categoria']), 1); pdf.cell(30, 10, f"R$ {row['valor']:,.2f}", 1)
        pdf.cell(30, 10, str(row.get('status_pagamento', 'N/A')), 1); pdf.ln()
        total += row['valor']
    pdf.ln(5); pdf.set_font("Helvetica", "B", 12)
    pdf.cell(190, 10, f"TOTAL: {formatar_real(total)}", ln=True, align="R")
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 8. MENU ---
if st.session_state.menu_aberto:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    perf = st.session_state.user_perfil
    if st.button("📊 Dashboard"): st.session_state.pagina='RESUMO'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("💸 Lançar Gasto"): st.session_state.pagina='GASTO'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("🏗️ Configurar Obras"): st.session_state.pagina='OBRA_ADAPT'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("📋 Relatórios"): st.session_state.pagina='LISTA'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("👤 Clientes"): st.session_state.pagina='CLIE'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("🤝 Fornecedores"): st.session_state.pagina='FORN'; st.session_state.menu_aberto=False; st.rerun()
    if perf == 'ADMIN':
        if st.button("👥 Gestão de Equipe"): st.session_state.pagina='USUARIOS'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("Sair"): st.session_state.logado = False; st.session_state.menu_aberto=False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 9. TELAS ---
else:
    pag, ver = st.session_state.pagina, st.session_state.form_version

    if pag == 'RESUMO':
        obras_data = listar_obras_unicas()
        if not obras_data: st.info("Nenhuma obra encontrada.")
        else:
            sel = st.selectbox("Selecione a Obra", [""] + list(obras_data.keys()), index=0, key=f"s_res_{ver}")
            if sel:
                d_obra = obras_data[sel]
                res_g = supabase.table("lancamentos_obra").select("valor").eq("nome_obra", sel).execute()
                gasto = sum(float(i['valor']) for i in res_g.data)
                
                orc = float(d_obra.get('orcamento_previsto', 0))
                imp_p = float(d_obra.get('impostos_estimados', 0))
                v_imp = orc * (imp_p/100)
                l_real = orc - gasto - v_imp
                
                c1,c2,c3,c4 = st.columns(4)
                c1.markdown(f'<div class="metric-container"><p class="metric-label">Orçado</p><p class="metric-value">{formatar_real(orc)}</p></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-container"><p class="metric-label">Tipo</p><p class="metric-value">{d_obra.get("tipo_obra", "N/A")}</p></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-container"><p class="metric-label">Imposto</p><p class="metric-value">{formatar_real(v_imp)}</p></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="metric-container"><p class="metric-label">Lucro Real</p><p class="metric-value">{formatar_real(l_real)}</p></div>', unsafe_allow_html=True)

    elif pag == 'GASTO':
        st.markdown("### Novo Lançamento")
        obras_dict = listar_obras_unicas()
        cats, forns = listar_categorias(), listar_fornecedores()
        with st.container(border=True):
            o_sel = st.selectbox("Obra Existente", [""] + list(obras_dict.keys()), index=0)
            o_nova = st.text_input("OU Nome de Nova Obra")
            obra_final = o_nova if o_nova else o_sel
            
            # Se for obra existente, puxa os valores automáticos
            ref = obras_dict.get(o_sel, {})
            v_orc = st.number_input("Orçamento Total (R$)", value=float(ref.get('orcamento_previsto', 0.0)))
            v_luc = st.number_input("Lucro (%)", value=float(ref.get('lucro_estimado', 0.0)))
            v_imp = st.number_input("Imposto (%)", value=float(ref.get('impostos_estimados', 0.0)))
            
            t_obra = st.selectbox("Tipo de Obra", ["", "Residencial", "Comercial", "Reforma", "Industrial", "Outro"], index=0)
            c_s = st.selectbox("Categoria*", [""] + list(cats.keys()), index=0)
            f_s = st.selectbox("Fornecedor*", [""] + list(forns.keys()), index=0)
            desc = st.text_input("Descrição")
            val = st.number_input("Valor do Gasto", min_value=0.0)
            status = st.selectbox("Status", ["", "Pago", "Pendente"], index=0)
            
            if st.button("SALVAR GASTO", use_container_width=True, type="primary"):
                if obra_final and c_s and val > 0:
                    dados = {
                        "nome_obra": obra_final, "categoria_id": cats[c_s], "fornecedor_id": forns[f_s]['id'] if f_s else None,
                        "descricao": desc, "valor": val, "status_pagamento": status, "tipo_obra": t_obra,
                        "orcamento_previsto": v_orc, "lucro_estimado": v_luc, "impostos_estimados": v_imp
                    }
                    supabase.table("lancamentos_obra").insert(dados).execute()
                    limpar_campos(); st.rerun()

    elif pag == 'OBRA_ADAPT':
        st.markdown("### Configuração de Obras (Histórico)")
        obras_dict = listar_obras_unicas()
        for nome, dados in obras_dict.items():
            with st.expander(f"🏗️ {nome}"):
                st.write(f"**Tipo:** {dados['tipo_obra']}")
                st.write(f"**Orçamento:** {formatar_real(dados['orcamento_previsto'])}")
                st.write(f"**Taxas:** Lucro {dados['lucro_estimado']}% | Imposto {dados['impostos_estimados']}%")
                st.info("Para alterar estes valores, realize um novo lançamento para esta obra com os dados atualizados.")

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
            cr = st.text_input("Contato", value=df_c["representante"])
            ct = st.text_input("Telefone", value=df_c["telefone"])
            cc = st.text_input("CPF/CNPJ", value=df_c["cnpj"])
            ce = st.text_input("E-mail", value=df_c["email"])
            ca = st.text_area("Endereço", value=df_c["endereco"])
            if st.button("SALVAR CLIENTE", use_container_width=True):
                p = {"nome_cliente": cn, "representante": cr, "telefone": ct, "cnpj": cc, "email": ce, "endereco": ca}
                if st.session_state.clie_edit_id: supabase.table("clientes").update(p).eq("id", st.session_state.clie_edit_id).execute()
                else: supabase.table("clientes").insert(p).execute()
                limpar_campos(); st.rerun()
        for c in (supabase.table("clientes").select("*").order("nome_cliente").execute().data or []):
            with st.expander(f"👤 {c['nome_cliente']}"):
                if st.button("Editar", key=f"ec_{c['id']}"): st.session_state.clie_edit_id=c['id']; st.rerun()

    elif pag == 'LISTA':
        st.markdown("### Relatórios")
        obras = listar_obras_unicas()
        if obras:
            o_f = st.selectbox("Obra", [""] + list(obras.keys()))
            if o_f:
                dados = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("nome_obra", o_f).execute().data
                if dados:
                    df_p = pd.DataFrame(dados)
                    st.download_button("📥 PDF", gerar_pdf(df_p, o_f), f"{o_f}.pdf")
                    for g in dados:
                        with st.expander(f"{g['descricao']} - {formatar_real(g['valor'])}"):
                            if st.button("Excluir", key=f"dg_{g['id']}"):
                                supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute(); st.rerun()

    elif pag == 'USUARIOS' and st.session_state.user_perfil == 'ADMIN':
        st.markdown("### Equipe")
        with st.container(border=True):
            ne = st.text_input("E-mail")
            ns = st.text_input("Senha", type="password")
            np = st.selectbox("Perfil", ["", "LANCADOR", "ADMIN"])
            if st.button("CRIAR"):
                if ne and ns and np:
                    supabase.table("usuarios").insert({"email": ne, "senha": ns, "perfil": np}).execute(); st.rerun()
        st.table(pd.DataFrame(supabase.table("usuarios").select("email, perfil").execute().data))
