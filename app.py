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

# Inicialização de IDs de edição
for key in ['forn_edit_id', 'clie_edit_id', 'obra_edit_id']:
    if key not in st.session_state: st.session_state[key] = None

def limpar_campos():
    st.session_state.form_version += 1
    st.session_state.forn_edit_id = None
    st.session_state.clie_edit_id = None
    st.session_state.obra_edit_id = None

def realizar_login(email, senha):
    try:
        res = supabase.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
        if res.data:
            user = res.data[0]
            st.session_state.logado = True
            st.session_state.user_perfil = user['perfil']
            st.session_state.pagina = 'GASTO' if user['perfil'] == 'LANCADOR_EXTERNO' else 'RESUMO'
            return True
    except: pass
    return False

# --- 3. FORMATADORES ---
def aplicar_mask_cnpj(cnpj):
    if not cnpj: return ""
    num = re.sub(r'\D', '', str(cnpj))
    return f"{num[:2]}.{num[2:5]}.{num[5:8]}/{num[8:12]}-{num[12:]}" if len(num) == 14 else cnpj

def aplicar_mask_tel(tel):
    if not tel: return ""
    num = re.sub(r'\D', '', str(tel))
    if len(num) == 11: return f"({num[:2]}) {num[2:7]}-{num[7:]}"
    elif len(num) == 10: return f"({num[:2]}) {num[2:6]}-{num[6:]}"
    return tel

def formatar_real(valor):
    try:
        val = float(valor) if valor else 0.0
        return f"R$ {val:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except: return "R$ 0,00"

# --- 4. ESTILO VISUAL ---
st.markdown(f"""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {{display: none;}}
    .block-container {{ padding-top: 2rem !important; }}
    .main-title {{ color: #FFFFFF !important; font-size: 1.4rem; font-weight: 700; margin-bottom: 15px; }}
    
    img, [data-testid="stImage"] img {{ 
        border-radius: 0px !important; 
        object-fit: contain !important;
    }}
    
    .metric-container {{ background: #1E1E1E; padding: 15px; border-radius: 10px; border: 1px solid #333; margin-bottom: 10px; text-align: center; }}
    .metric-label {{ color: #AAAAAA; font-size: 0.70rem; font-weight: 600; text-transform: uppercase; }}
    .metric-value {{ color: #FFFFFF; font-size: 1.1rem; font-weight: 800; }}
    div.stButton > button[key="trigger"] {{ background-color: transparent !important; color: #FFFFFF !important; width: 45px !important; height: 45px !important; border: none !important; font-size: 30px !important; }}
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
def listar_clientes():
    res = supabase.table("clientes").select("id, nome_cliente").order("nome_cliente").execute()
    return {item['nome_cliente']: item['id'] for item in res.data}

def listar_obras_por_cliente(cliente_id):
    if not cliente_id: return {}
    res = supabase.table("obras").select("*").eq("cliente_id", cliente_id).execute()
    return {item['nome_obra']: item for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

def listar_fornecedores():
    res = supabase.table("fornecedores").select("id, nome_fornecedor").order("nome_fornecedor").execute()
    return {item['nome_fornecedor']: item['id'] for item in res.data}

def gerar_pdf(df, nome_obra):
    pdf = FPDF()
    pdf.add_page(); pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, f"Relatorio ROSECON - {nome_obra}", ln=True, align="C"); pdf.ln(10)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(25, 10, "Data", 1); pdf.cell(60, 10, "Descricao", 1); pdf.cell(45, 10, "Categoria", 1); pdf.cell(30, 10, "Valor", 1); pdf.cell(30, 10, "Status", 1); pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    total = 0
    for _, row in df.iterrows():
        dt = str(row.get('created_at', ''))[:10]
        pdf.cell(25, 10, dt, 1); pdf.cell(60, 10, str(row.get('descricao', ''))[:30], 1)
        cat = row['categorias_obra']['nome_categoria'] if isinstance(row.get('categorias_obra'), dict) else "N/A"
        pdf.cell(45, 10, cat, 1); pdf.cell(30, 10, f"R$ {row.get('valor', 0):,.2f}", 1)
        pdf.cell(30, 10, str(row.get('status_pagamento', 'N/A')), 1); pdf.ln()
        total += row.get('valor', 0)
    pdf.ln(5); pdf.set_font("Helvetica", "B", 12)
    pdf.cell(190, 10, f"TOTAL: {formatar_real(total)}", ln=True, align="R")
    return pdf.output(dest='S').encode('latin-1', 'replace')

def gerar_excel(df):
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Gastos')
        return output.getvalue()
    except: return None

# --- 8. LOGICA DE NAVEGAÇÃO ---
pag, perf, ver = st.session_state.pagina, st.session_state.user_perfil, st.session_state.form_version

if st.session_state.menu_aberto:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    if perf != 'LANCADOR_EXTERNO':
        if st.button("📊 Dashboard"): st.session_state.pagina='RESUMO'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("💸 Lançar Gasto"): st.session_state.pagina='GASTO'; st.session_state.menu_aberto=False; st.rerun()
    if perf != 'LANCADOR_EXTERNO':
        if st.button("📋 Relatórios"): st.session_state.pagina='LISTA'; st.session_state.menu_aberto=False; st.rerun()
        if st.button("👤 Clientes"): st.session_state.pagina='CLIE'; st.session_state.menu_aberto=False; st.rerun()
        if st.button("🤝 Fornecedores"): st.session_state.pagina='FORN'; st.session_state.menu_aberto=False; st.rerun()
    if perf == 'ADMIN':
        if st.button("🏗️ Minhas Obras"): st.session_state.pagina='OBRA'; st.session_state.menu_aberto=False; st.rerun()
        if st.button("👥 Equipe"): st.session_state.pagina='USUARIOS'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("Sair"): st.session_state.logado = False; st.session_state.menu_aberto=False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 9. TELAS ---
else:
    if pag == 'RESUMO' and perf != 'LANCADOR_EXTERNO':
        st.markdown('<p class="main-title">Saúde Financeira</p>', unsafe_allow_html=True)
        clis = listar_clientes()
        c_sel = st.selectbox("Cliente", [""] + list(clis.keys()), key=f"d_cli_{ver}")
        if c_sel:
            obs = listar_obras_por_cliente(clis[c_sel])
            o_sel = st.selectbox("Obra", [""] + list(obs.keys()), key=f"d_obr_{ver}")
            if o_sel:
                inf = obs[o_sel]
                res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': inf['id']}).execute()
                gt = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
                orc = float(inf.get('orcamento_previsto') or 0)
                p_luc = float(inf.get('lucro_estimado') or 0); p_imp = float(inf.get('impostos_estimados') or 0)
                v_luc = orc * (p_luc/100); v_imp = orc * (p_imp/100); l_real = orc - gt - v_imp
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f'<div class="metric-container"><small class="metric-label">Orçado</small><br><span class="metric-value">{formatar_real(orc)}</span></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="metric-container"><small class="metric-label">Lucro Prev</small><br><span class="metric-value">{formatar_real(v_luc)}</span></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="metric-container"><small class="metric-label">Imposto</small><br><span class="metric-value">{formatar_real(v_imp)}</span></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="metric-container"><small class="metric-label">Lucro Real</small><br><span class="metric-value" style="color:{"#00FF00" if l_real > 0 else "#FF0000"}">{formatar_real(l_real)}</span></div>', unsafe_allow_html=True)
                if orc > 0: st.progress(min(gt / orc, 1.0))
                if res_s.data: st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'CLIE' and perf != 'LANCADOR_EXTERNO':
        st.markdown("### Gestão de Clientes")
        if st.session_state.clie_edit_id and st.button("➕ NOVO"): limpar_campos(); st.rerun()
        dc = {"nome_cliente":"", "representante":"", "telefone":"", "whatsapp":"", "email":"", "cnpj":"", "endereco":""}
        if st.session_state.clie_edit_id:
            try:
                res = supabase.table("clientes").select("*").eq("id", st.session_state.clie_edit_id).single().execute()
                if res.data: dc = res.data
            except: st.session_state.clie_edit_id = None
        with st.container(border=True):
            cn = st.text_input("Nome*", value=dc["nome_cliente"], key=f"cn_{ver}")
            cr = st.text_input("Representante", value=dc["representante"], key=f"cr_{ver}")
            ct = st.text_input("Telefone", value=dc["telefone"], key=f"ct_{ver}")
            cz = st.text_input("WhatsApp*", value=dc["whatsapp"], key=f"cz_{ver}")
            ce = st.text_input("E-mail*", value=dc["email"], key=f"ce_{ver}")
            cc = st.text_input("CNPJ/CPF", value=dc["cnpj"], key=f"cc_{ver}")
            cend = st.text_input("Endereço", value=dc["endereco"], key=f"cend_{ver}")
            if st.button("SALVAR CLIENTE", use_container_width=True, type="primary"):
                p = {"nome_cliente": cn, "representante": cr, "telefone": ct, "whatsapp": aplicar_mask_tel(cz), "email": ce, "cnpj": aplicar_mask_cnpj(cc), "endereco": cend}
                if st.session_state.clie_edit_id: supabase.table("clientes").update(p).eq("id", st.session_state.clie_edit_id).execute()
                else: supabase.table("clientes").insert(p).execute()
                limpar_campos(); st.rerun()
        for c in (supabase.table("clientes").select("*").order("nome_cliente").execute().data or []):
            with st.expander(f"👤 {c['nome_cliente']}"):
                st.write(f"📍 {c.get('endereco','')}\n📞 {c.get('whatsapp','')}")
                c1, c2 = st.columns(2)
                if c1.button("Editar", key=f"e_cl_{c['id']}"): st.session_state.clie_edit_id = c['id']; st.rerun()
                if c2.button("Excluir", key=f"d_cl_{c['id']}"): 
                    try:
                        st.session_state.clie_edit_id = None
                        supabase.table("clientes").delete().eq("id", c['id']).execute(); limpar_campos(); st.rerun()
                    except: st.error("Erro ao excluir cliente.")

    elif pag == 'FORN' and perf != 'LANCADOR_EXTERNO':
        st.markdown("### Gestão de Fornecedores")
        if st.session_state.forn_edit_id and st.button("➕ NOVO"): limpar_campos(); st.rerun()
        df_f = {"nome_fornecedor":"", "representante":"", "telefone":"", "whatsapp":"", "email":"", "cnpj":"", "endereco":""}
        if st.session_state.forn_edit_id:
            try:
                res = supabase.table("fornecedores").select("*").eq("id", st.session_state.forn_edit_id).single().execute()
                if res.data: df_f = res.data
            except: st.session_state.forn_edit_id = None
        with st.container(border=True):
            fn = st.text_input("Empresa*", value=df_f["nome_fornecedor"], key=f"fn_{ver}")
            fr = st.text_input("Contato", value=df_f["representante"], key=f"fr_{ver}")
            ft = st.text_input("Telefone", value=df_f["telefone"], key=f"ft_{ver}")
            fz = st.text_input("WhatsApp*", value=df_f["whatsapp"], key=f"fz_{ver}")
            fe = st.text_input("E-mail*", value=df_f["email"], key=f"fe_{ver}")
            fc = st.text_input("CNPJ/CPF", value=df_f["cnpj"], key=f"fc_{ver}")
            fend = st.text_input("Endereço", value=df_f["endereco"], key=f"fend_{ver}")
            if st.button("SALVAR FORNECEDOR", use_container_width=True, type="primary"):
                p = {"nome_fornecedor": fn, "representante": fr, "telefone": ft, "whatsapp": aplicar_mask_tel(fz), "email": fe, "cnpj": aplicar_mask_cnpj(fc), "endereco": fend}
                if st.session_state.forn_edit_id: supabase.table("fornecedores").update(p).eq("id", st.session_state.forn_edit_id).execute()
                else: supabase.table("fornecedores").insert(p).execute()
                limpar_campos(); st.rerun()
        for f in (supabase.table("fornecedores").select("*").order("nome_fornecedor").execute().data or []):
            with st.expander(f"🤝 {f['nome_fornecedor']}"):
                st.write(f"📍 {f.get('endereco','')}\n📞 {f.get('whatsapp','')}")
                c1, c2 = st.columns(2)
                if c1.button("Editar", key=f"e_f_{f['id']}"): st.session_state.forn_edit_id = f['id']; st.rerun()
                if c2.button("Excluir", key=f"d_f_{f['id']}"): 
                    try:
                        st.session_state.forn_edit_id = None
                        supabase.table("fornecedores").delete().eq("id", f['id']).execute(); limpar_campos(); st.rerun()
                    except: st.error("Erro ao excluir fornecedor.")

    elif pag == 'OBRA' and perf == 'ADMIN':
        st.markdown("### Gestão de Obras")
        if st.session_state.obra_edit_id and st.button("➕ NOVA OBRA"): limpar_campos(); st.rerun()
        
        do = {"nome_obra":"", "cliente_id":"", "orcamento_previsto":0.0, "lucro_estimado":0.0, "impostos_estimados":0.0, "local_obra":""}
        if st.session_state.obra_edit_id:
            try:
                res = supabase.table("obras").select("*").eq("id", st.session_state.obra_edit_id).single().execute()
                if res.data: do = res.data
            except: st.session_state.obra_edit_id = None
            
        clis = listar_clientes()
        with st.container(border=True):
            on = st.text_input("Nome*", value=do["nome_obra"], key=f"on_{ver}")
            idx = ([""] + list(clis.keys())).index(next((k for k, v in clis.items() if v == do["cliente_id"]), "")) if do["cliente_id"] else 0
            oc = st.selectbox("Cliente*", [""] + list(clis.keys()), index=idx, key=f"oc_{ver}")
            ol = st.text_input("Local da Obra", value=do.get("local_obra",""), key=f"ol_{ver}")
            ov = st.number_input("Orçamento", value=float(do["orcamento_previsto"]), key=f"ov_{ver}")
            c1, c2 = st.columns(2)
            oluc = c1.number_input("Lucro %", value=float(do.get("lucro_estimado") or 0), key=f"oluc_{ver}")
            oimp = c2.number_input("Imposto %", value=float(do.get("impostos_estimados") or 0), key=f"oimp_{ver}")
            if st.button("SALVAR OBRA", use_container_width=True, type="primary"):
                if on and oc:
                    p = {"nome_obra": on, "cliente_id": clis[oc], "orcamento_previsto": ov, "lucro_estimado": oluc, "impostos_estimados": oimp, "local_obra": ol}
                    if st.session_state.obra_edit_id: supabase.table("obras").update(p).eq("id", st.session_state.obra_edit_id).execute()
                    else: supabase.table("obras").insert(p).execute()
                    limpar_campos(); st.rerun()
                else: st.warning("Preencha os campos obrigatórios.")
        
        # --- LISTA DE OBRAS PARA EDITAR/EXCLUIR ---
        st.markdown("---")
        obras_lista = supabase.table("obras").select("*, clientes(nome_cliente)").order("nome_obra").execute().data
        for o in (obras_lista or []):
            with st.expander(f"🏗️ {o['nome_obra']} ({o['clientes']['nome_cliente']})"):
                st.write(f"📍 Local: {o.get('local_obra','Não informado')}")
                st.write(f"💰 Orçamento: {formatar_real(o['orcamento_previsto'])}")
                c1, c2 = st.columns(2)
                if c1.button("Editar", key=f"e_ob_{o['id']}"): 
                    st.session_state.obra_edit_id = o['id']
                    st.rerun()
                if c2.button("Excluir", key=f"d_ob_{o['id']}"): 
                    try:
                        st.session_state.obra_edit_id = None
                        supabase.table("obras").delete().eq("id", o['id']).execute()
                        limpar_campos(); st.rerun()
                    except: st.error("Esta obra possui lançamentos e não pode ser excluída.")

    elif pag == 'GASTO':
        st.markdown("### Lançar Gasto")
        clis, cats, forns = listar_clientes(), listar_categorias(), listar_fornecedores()
        with st.container(border=True):
            c_sel = st.selectbox("Cliente*", [""] + list(clis.keys()), key=f"g_cli_{ver}")
            o_sel = ""
            if c_sel:
                obs = listar_obras_por_cliente(clis[c_sel])
                o_sel = st.selectbox("Obra*", [""] + list(obs.keys()), key=f"g_obr_{ver}")
            cat_sel = st.selectbox("Categoria*", [""] + list(cats.keys()), key=f"g_cat_{ver}")
            forn_sel = st.selectbox("Fornecedor*", [""] + list(forns.keys()), key=f"g_forn_{ver}")
            desc = st.text_input("Descrição", key=f"g_desc_{ver}")
            val = st.number_input("Valor", min_value=0.0, key=f"g_val_{ver}")
            status = st.selectbox("Status", ["Pago", "Pendente"], key=f"g_stat_{ver}")
            foto = st.camera_input("Recibo", key=f"g_cam_{ver}")
            if st.button("SALVAR GASTO", use_container_width=True, type="primary"):
                if c_sel and o_sel and cat_sel and forn_sel and val > 0:
                    oid = obs[o_sel].get('id')
                    url = None
                    if foto:
                        n_arq = f"{uuid.uuid4()}.jpg"
                        supabase.storage.from_("comprovantes").upload(n_arq, foto.getvalue())
                        url = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{n_arq}"
                    supabase.table("lancamentos_obra").insert({"obra_id": oid, "categoria_id": cats[cat_sel], "fornecedor_id": forns[forn_sel], "descricao": desc, "valor": val, "url_comprovante": url, "status_pagamento": status}).execute()
                    st.success("Salvo!"); limpar_campos(); st.rerun()

    elif pag == 'LISTA' and perf != 'LANCADOR_EXTERNO':
        st.markdown("### Relatórios")
        clis = listar_clientes()
        c_sel = st.selectbox("Filtrar Cliente", [""] + list(clis.keys()))
        if c_sel:
            obs = listar_obras_por_cliente(clis[c_sel])
            o_f = st.selectbox("Filtrar Obra", [""] + list(obs.keys()))
            if o_f:
                oid = obs[o_f].get('id')
                d = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria), fornecedores(nome_fornecedor)").eq("obra_id", oid).order("created_at", desc=True).execute().data
                if d:
                    df_d = pd.DataFrame(d)
                    c1, c2 = st.columns(2)
                    c1.download_button("📥 PDF", gerar_pdf(df_d, o_f), f"{o_f}.pdf", use_container_width=True)
                    ex = gerar_excel(df_d)
                    if ex: c2.download_button("📊 Excel", ex, f"{o_f}.xlsx", use_container_width=True)
                    for g in d:
                        cor = "🟢" if g.get('status_pagamento') == "Pago" else "🔴"
                        with st.expander(f"{cor} {g['descricao']} | {formatar_real(g['valor'])}"):
                            if g.get('url_comprovante'): st.image(g['url_comprovante'])
                            if st.button("Excluir", key=f"dg_{g['id']}"): 
                                supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute(); st.rerun()

    elif pag == 'USUARIOS' and perf == 'ADMIN':
        st.markdown("### Gestão de Equipe")
        with st.container(border=True):
            ne = st.text_input("Novo E-mail", key=f"ne_{ver}")
            ns = st.text_input("Nova Senha", type="password", key=f"ns_{ver}")
            np = st.selectbox("Perfil", ["ADMIN", "LANCADOR", "LANCADOR_EXTERNO"], key=f"np_{ver}")
            if st.button("CADASTRAR"):
                if ne and ns:
                    try:
                        supabase.table("usuarios").insert({"email": ne, "senha": ns, "perfil": np}).execute()
                        st.success("Sucesso!"); limpar_campos(); st.rerun()
                    except Exception as e: st.error("Erro ao cadastrar usuário.")
        u_l = supabase.table("usuarios").select("id, email, perfil").execute().data
        if u_l: st.table(pd.DataFrame(u_l))
