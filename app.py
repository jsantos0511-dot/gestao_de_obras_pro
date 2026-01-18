import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
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
    if valor is None: valor = 0
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# --- 4. ESTILO VISUAL ---
st.markdown(f"""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {{display: none;}}
    .block-container {{ padding-top: 2rem !important; }}
    img {{ border-radius: 0px !important; }}
    .stImage > img {{ border-radius: 0px !important; display: block; margin: 0 auto; }}
    .main-title {{ color: #FFFFFF !important; font-size: 1.4rem; font-weight: 700; margin-bottom: 15px; }}
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
def listar_obras():
    try:
        res = supabase.table("obras").select("*").execute()
        return {str(item['nome_obra']): item for item in res.data}
    except: return {}

def listar_categorias():
    try:
        res = supabase.table("categorias_obra").select("id, nome_categoria").execute()
        return {item['nome_categoria']: item['id'] for item in res.data}
    except: return {}

def listar_fornecedores():
    try:
        res = supabase.table("fornecedores").select("id, nome_fornecedor").order("nome_fornecedor").execute()
        return {item['nome_fornecedor']: item['id'] for item in res.data}
    except: return {}

def listar_clientes():
    try:
        res = supabase.table("clientes").select("id, nome_cliente").order("nome_cliente").execute()
        return {item['nome_cliente']: item['id'] for item in res.data}
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

def gerar_excel(df):
    output = io.BytesIO()
    df_excel = df.copy()
    if 'categorias_obra' in df_excel.columns:
        df_excel['Categoria'] = df_excel['categorias_obra'].apply(lambda x: x['nome_categoria'] if isinstance(x, dict) else '')
    if 'fornecedores' in df_excel.columns:
        df_excel['Fornecedor'] = df_excel['fornecedores'].apply(lambda x: x['nome_fornecedor'] if isinstance(x, dict) else '')
    colunas_uteis = ['created_at', 'descricao', 'Categoria', 'Fornecedor', 'valor', 'status_pagamento']
    df_final = df_excel[[c for c in colunas_uteis if c in df_excel.columns]]
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Lancamentos')
    return output.getvalue()

def excluir_em_cascata_cliente(cliente_id):
    try:
        obras = supabase.table("obras").select("id").eq("cliente_id", cliente_id).execute().data
        for o in obras:
            supabase.table("lancamentos_obra").delete().eq("obra_id", o['id']).execute()
        supabase.table("obras").delete().eq("cliente_id", cliente_id).execute()
        supabase.table("clientes").delete().eq("id", cliente_id).execute()
    except: pass

# --- 8. MENU ---
if st.session_state.menu_aberto:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    perf = st.session_state.user_perfil
    if st.button("📊 Dashboard"): st.session_state.pagina='RESUMO'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("💸 Lançar Gasto"): st.session_state.pagina='GASTO'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("📋 Relatórios"): st.session_state.pagina='LISTA'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("👤 Clientes"): st.session_state.pagina='CLIE'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("🤝 Fornecedores"): st.session_state.pagina='FORN'; st.session_state.menu_aberto=False; st.rerun()
    if perf == 'ADMIN':
        if st.button("🏗️ Minhas Obras"): st.session_state.pagina='OBRA'; st.session_state.menu_aberto=False; st.rerun()
        if st.button("👥 Gestão de Equipe"): st.session_state.pagina='USUARIOS'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("Sair"): st.session_state.logado = False; st.session_state.menu_aberto=False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 9. TELAS ---
else:
    pag, perf, ver = st.session_state.pagina, st.session_state.user_perfil, st.session_state.form_version

    if pag == 'RESUMO':
        obs_dict = listar_obras()
        if not obs_dict: st.info("Cadastre uma obra em 'Minhas Obras'.")
        else:
            sel = st.selectbox("Selecione a Obra", [""] + list(obs_dict.keys()), index=0, key=f"s_res_{ver}")
            if sel:
                o = obs_dict[sel]
                res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': o['id']}).execute()
                gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
                orc, luc, imp = float(o.get('orcamento_previsto',0)), float(o.get('lucro_estimado',0)), float(o.get('impostos_estimados',0))
                v_imp = orc * (imp/100)
                l_real = orc - gasto - v_imp
                
                c1,c2,c3,c4 = st.columns(4)
                c1.markdown(f'<div class="metric-container"><p class="metric-label">Orçado</p><p class="metric-value">{formatar_real(orc)}</p></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-container"><p class="metric-label">Exp. Lucro</p><p class="metric-value">{formatar_real(orc*(luc/100))}</p></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-container"><p class="metric-label">Imposto</p><p class="metric-value">{formatar_real(v_imp)}</p></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="metric-container"><p class="metric-label">Lucro Real</p><p class="metric-value">{formatar_real(l_real)}</p></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="data-card"><h3>Gasto Acumulado: {formatar_real(gasto)}</h3></div>', unsafe_allow_html=True)
                if res_s.data: st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'GASTO':
        st.markdown("### Lançamento")
        obs_dict, cats, forns = listar_obras(), listar_categorias(), listar_fornecedores()
        with st.container(border=True):
            o_s = st.selectbox("Obra*", [""] + list(obs_dict.keys()), index=0, key=f"go_{ver}")
            c_s = st.selectbox("Categoria*", [""] + list(cats.keys()), index=0, key=f"gc_{ver}")
            f_s = st.selectbox("Fornecedor*", [""] + list(forns.keys()), index=0, key=f"gf_{ver}")
            d = st.text_input("Descrição", key=f"gd_{ver}")
            v = st.number_input("Valor", min_value=0.0, key=f"gv_{ver}")
            st_p = st.selectbox("Status", ["Pago", "Pendente"], index=0, key=f"gs_{ver}")
            foto = st.camera_input("Recibo", key=f"gp_{ver}")
            if st.button("SALVAR", use_container_width=True, type="primary"):
                if o_s and c_s and f_s and v > 0:
                    url = None
                    if foto:
                        n_arq = f"{uuid.uuid4()}.jpg"
                        supabase.storage.from_("comprovantes").upload(n_arq, foto.getvalue())
                        url = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{n_arq}"
                    supabase.table("lancamentos_obra").insert({"obra_id": obs_dict[o_s]['id'], "categoria_id": cats[c_s], "fornecedor_id": forns[f_s], "descricao": d, "valor": v, "url_comprovante": url, "status_pagamento": st_p}).execute()
                    limpar_campos(); st.rerun()

    elif pag == 'FORN':
        st.markdown("### Fornecedores")
        df = {"nome_fornecedor": "", "representante": "", "telefone": "", "whatsapp": "", "cnpj": "", "email": "", "endereco": ""}
        if st.session_state.forn_edit_id:
            res = supabase.table("fornecedores").select("*").eq("id", st.session_state.forn_edit_id).single().execute()
            if res.data: df = res.data
        with st.container(border=True):
            fn = st.text_input("Empresa*", value=df["nome_fornecedor"], key=f"fn_{ver}")
            fr = st.text_input("Representante*", value=df["representante"], key=f"fr_{ver}")
            ft = st.text_input("Telefone", value=df["telefone"], key=f"ft_{ver}")
            fw = st.text_input("WhatsApp", value=df["whatsapp"], key=f"fw_{ver}")
            fc = st.text_input("CNPJ", value=df["cnpj"], key=f"fc_{ver}")
            fe = st.text_input("E-mail", value=df["email"], key=f"fe_{ver}")
            fa = st.text_area("Endereço", value=df["endereco"], key=f"fa_{ver}")
            if st.button("SALVAR FORNECEDOR", use_container_width=True, type="primary"):
                p = {"nome_fornecedor": fn, "representante": fr, "telefone": ft, "whatsapp": fw, "cnpj": fc, "email": fe, "endereco": fa}
                if st.session_state.forn_edit_id: supabase.table("fornecedores").update(p).eq("id", st.session_state.forn_edit_id).execute()
                else: supabase.table("fornecedores").insert(p).execute()
                limpar_campos(); st.rerun()
        for f in (supabase.table("fornecedores").select("*").order("nome_fornecedor").execute().data or []):
            with st.expander(f"🏢 {f['nome_fornecedor']}"):
                c1, c2 = st.columns(2)
                if c1.button("📝", key=f"ef_{f['id']}"): st.session_state.forn_edit_id=f['id']; st.rerun()
                if c2.button("🗑️", key=f"df_{f['id']}"): supabase.table("fornecedores").delete().eq("id", f['id']).execute(); st.rerun()

    elif pag == 'CLIE':
        st.markdown("### Clientes")
        dc = {"nome_cliente": "", "representante": "", "telefone": "", "whatsapp": "", "cnpj": "", "email": "", "endereco": ""}
        if st.session_state.clie_edit_id:
            res = supabase.table("clientes").select("*").eq("id", st.session_state.clie_edit_id).single().execute()
            if res.data: dc = res.data
        with st.container(border=True):
            cn = st.text_input("Cliente*", value=dc["nome_cliente"], key=f"cn_{ver}")
            cr = st.text_input("Contato", value=dc["representante"], key=f"cr_{ver}")
            ct = st.text_input("Tel", value=dc["telefone"], key=f"ct_{ver}")
            cw = st.text_input("Zap", value=dc["whatsapp"], key=f"cw_{ver}")
            cc = st.text_input("CNPJ/CPF", value=dc["cnpj"], key=f"cc_{ver}")
            ce = st.text_input("E-mail", value=dc["email"], key=f"ce_{ver}")
            ca = st.text_area("Endereço", value=dc["endereco"], key=f"ca_{ver}")
            if st.button("SALVAR CLIENTE", use_container_width=True, type="primary"):
                p = {"nome_cliente": cn, "representante": cr, "telefone": ct, "whatsapp": cw, "cnpj": cc, "email": ce, "endereco": ca}
                if st.session_state.clie_edit_id: supabase.table("clientes").update(p).eq("id", st.session_state.clie_edit_id).execute()
                else: supabase.table("clientes").insert(p).execute()
                limpar_campos(); st.rerun()
        for c in (supabase.table("clientes").select("*").order("nome_cliente").execute().data or []):
            with st.expander(f"👤 {c['nome_cliente']}"):
                c1, c2 = st.columns(2)
                if c1.button("📝", key=f"ec_{c['id']}"): st.session_state.clie_edit_id=c['id']; st.rerun()
                if c2.button("🗑️", key=f"dc_{c['id']}"): excluir_em_cascata_cliente(c['id']); st.rerun()

    elif pag == 'LISTA':
        st.markdown("### Relatórios")
        obs_dict_l = listar_obras()
        if obs_dict_l:
            o_f = st.selectbox("Selecione a Obra", [""] + list(obs_dict_l.keys()), index=0, key=f"lo_{ver}")
            d_i, d_f = st.date_input("Período", [datetime.now().replace(day=1), datetime.now()])
            if o_f:
                query = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("obra_id", obs_dict_l[o_f]['id']).gte("created_at", d_i).lte("created_at", f"{d_f} 23:59:59")
                dados = query.execute().data
                if dados:
                    df_p = pd.DataFrame(dados)
                    st.download_button("📥 PDF", gerar_pdf(df_p, o_f), f"{o_f}.pdf")
                    st.download_button("📊 Excel", gerar_excel(df_p), f"{o_f}.xlsx")
                    for g in dados:
                        with st.expander(f"{g['descricao']} - {formatar_real(g['valor'])}"):
                            if g.get('url_comprovante'): st.image(g['url_comprovante'])
                            if st.button("Remover", key=f"dg_{g['id']}"):
                                supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute(); st.rerun()

    elif pag == 'OBRA' and perf == 'ADMIN':
        st.markdown("### Gestão de Obras")
        do = {"nome_obra":"","cliente_id":"","tipo_obra":"","local_obra":"","orcamento_previsto":0.0,"lucro_estimado":0.0,"impostos_estimados":0.0}
        if st.session_state.obra_edit_id:
            try:
                res = supabase.table("obras").select("*").eq("id", st.session_state.obra_edit_id).single().execute()
                if res.data: do = res.data
            except: pass
        clis = listar_clientes()
        with st.container(border=True):
            on = st.text_input("Nome*", value=do["nome_obra"], key=f"on_{ver}")
            oc = st.selectbox("Cliente*", [""] + list(clis.keys()), index=0, key=f"oc_{ver}")
            ov = st.number_input("Orçamento", value=float(do["orcamento_previsto"]), key=f"ov_{ver}")
            oluc = st.number_input("Lucro %", value=float(do["lucro_estimado"]), key=f"oluc_{ver}")
            oimp = st.number_input("Imposto %", value=float(do["impostos_estimados"]), key=f"oimp_{ver}")
            lista_tipos = ["", "Residencial", "Comercial", "Reforma", "Industrial", "Outro"]
            ot_idx = lista_tipos.index(do["tipo_obra"]) if do["tipo_obra"] in lista_tipos else 0
            ot = st.selectbox("Tipo", lista_tipos, index=ot_idx, key=f"ot_{ver}")
            ol = st.text_input("Local", value=do["local_obra"], key=f"ol_{ver}")
            if st.button("SALVAR OBRA", use_container_width=True, type="primary"):
                if on and oc and ot:
                    try:
                        p = {"nome_obra":on,"cliente_id":clis[oc],"tipo_obra":ot,"local_obra":ol,"orcamento_previsto":ov,"lucro_estimado":oluc,"impostos_estimados":oimp}
                        if st.session_state.obra_edit_id: supabase.table("obras").update(p).eq("id", st.session_state.obra_edit_id).execute()
                        else: supabase.table("obras").insert(p).execute()
                        limpar_campos(); st.rerun()
                    except Exception as e:
                        st.error("Erro ao salvar: Verifique se a tabela 'obras' foi criada no Supabase conforme as instruções do SQL.")

        obs_l = (supabase.table("obras").select("*").execute().data or [])
        for ob in obs_l:
            with st.expander(f"🏗️ {ob['nome_obra']}"):
                if st.button("Editar Obra", key=f"eob_{ob['id']}"): st.session_state.obra_edit_id=ob['id']; st.rerun()

    elif pag == 'USUARIOS' and perf == 'ADMIN':
        st.markdown("### Equipe")
        with st.container(border=True):
            ne, ns = st.text_input("E-mail"), st.text_input("Senha", type="password")
            np = st.selectbox("Perfil", ["", "LANCADOR", "ADMIN"], index=0)
            if st.button("CRIAR"):
                if ne and ns and np:
                    supabase.table("usuarios").insert({"email": ne, "senha": ns, "perfil": np}).execute(); st.rerun()
        st.table(pd.DataFrame(supabase.table("usuarios").select("email, perfil").execute().data))
