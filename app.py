import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import uuid
import re
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
if 'menu_aberto' not in st.session_state: st.session_state.menu_aberto = False
if 'form_version' not in st.session_state: st.session_state.form_version = 0

# Controles de Edição
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

# --- 3. FUNÇÕES DE FORMATAÇÃO ---
def aplicar_mask_cnpj(cnpj):
    if not cnpj: return ""
    num = re.sub(r'\D', '', str(cnpj))
    if len(num) == 14:
        return f"{num[:2]}.{num[2:5]}.{num[5:8]}/{num[8:12]}-{num[12:]}"
    return cnpj

def aplicar_mask_tel(tel):
    if not tel: return ""
    num = re.sub(r'\D', '', str(tel))
    if len(num) == 11:
        return f"({num[:2]}) {num[2:7]}-{num[7:]}"
    elif len(num) == 10:
        return f"({num[:2]}) {num[2:6]}-{num[6:]}"
    return tel

# --- 4. ESTILO VISUAL (PADRONIZAÇÃO TOTAL) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    html, body, [class*="st-"] {{
        font-family: 'Inter', sans-serif !important;
    }}

    [data-testid="stSidebar"], [data-testid="stHeader"] {{display: none;}}
    .block-container {{ padding-top: 2rem !important; }}
    
    .stImage > img {{ border-radius: 0px !important; display: block; margin-left: auto; margin-right: auto; }}
    
    /* Títulos principais */
    .main-title {{
        color: #FFFFFF !important;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 20px;
    }}

    /* Cards de Dashboard */
    .metric-container {{
        background: #1E1E1E;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333;
        margin-bottom: 15px;
        text-align: center;
    }}
    .metric-label {{
        color: #AAAAAA;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 5px;
    }}
    .metric-value {{
        color: #FFFFFF;
        font-size: 1.6rem;
        font-weight: 800;
    }}
    
    /* Gasto Acumulado em destaque */
    .data-card {{ 
        background: #F8F9FA; padding: 24px; border-radius: 12px; 
        border: 1px solid #E9ECEF; margin-bottom: 20px; color: #1e1e1e; 
    }}
    .data-card small {{ color: #6C757D; text-transform: uppercase; font-weight: 600; font-size: 0.75rem; }}
    .data-card h2 {{ color: #1E1E1E !important; margin-top: 5px; font-weight: 800; font-size: 2rem; }}
    
    /* Navegação */
    div.stButton > button[key="trigger"] {{
        background-color: transparent !important; color: #FFFFFF !important;
        width: 45px !important; height: 45px !important; border: none !important;
        font-size: 30px !important;
    }}
    .nav-card button {{ 
        width: 100% !important; height: 55px !important; font-weight: 600 !important; 
        margin-bottom: 10px !important; border-radius: 8px !important;
    }}
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
head_col1, head_col2 = st.columns([0.15, 0.85])
with head_col1:
    icon = "×" if st.session_state.menu_aberto else "☰"
    if st.button(icon, key="trigger"):
        st.session_state.menu_aberto = not st.session_state.menu_aberto
        st.rerun()
with head_col2:
    st.image(LOGO_URL, width=195)
st.markdown("---") 

# --- 7. FUNÇÕES DE APOIO ---
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def listar_obras():
    res = supabase.table("obras").select("id, nome_obra, orcamento_previsto").execute()
    return {item['nome_obra']: {"id": item['id'], "orcamento": item['orcamento_previsto']} for item in res.data}

def listar_categorias():
    res = supabase.table("categorias_obra").select("id, nome_categoria").execute()
    return {item['nome_categoria']: item['id'] for item in res.data}

def listar_fornecedores():
    res = supabase.table("fornecedores").select("id, nome_fornecedor").order("nome_fornecedor").execute()
    return {item['nome_fornecedor']: item['id'] for item in res.data}

def listar_clientes():
    res = supabase.table("clientes").select("id, nome_cliente").order("nome_cliente").execute()
    return {item['nome_cliente']: item['id'] for item in res.data}

def gerar_pdf(df, nome_obra):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, f"Relatório ROSECON - {nome_obra}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(25, 10, "Data", 1); pdf.cell(75, 10, "Descrição", 1); pdf.cell(55, 10, "Categoria", 1); pdf.cell(35, 10, "Valor", 1); pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    total = 0
    for _, row in df.iterrows():
        dt = datetime.strptime(row['created_at'][:10], '%Y-%m-%d').strftime('%d/%m/%Y')
        pdf.cell(25, 10, dt, 1); pdf.cell(75, 10, str(row['descricao'])[:40], 1)
        pdf.cell(55, 10, str(row['categorias_obra']['nome_categoria']), 1); pdf.cell(35, 10, f"R$ {row['valor']:,.2f}", 1); pdf.ln()
        total += row['valor']
    pdf.ln(5); pdf.set_font("Helvetica", "B", 12)
    pdf.cell(190, 10, f"TOTAL: {formatar_real(total)}", ln=True, align="R")
    return pdf.output(dest='S').encode('latin-1', 'replace')

def excluir_em_cascata_cliente(cliente_id):
    obras = supabase.table("obras").select("id").eq("cliente_id", cliente_id).execute().data
    for o in obras:
        gastos = supabase.table("lancamentos_obra").select("id, url_comprovante").eq("obra_id", o['id']).execute().data
        for g in gastos:
            if g.get('url_comprovante'):
                try:
                    nome_f = g['url_comprovante'].split('/')[-1]
                    supabase.storage.from_("comprovantes").remove([nome_f])
                except: pass
        supabase.table("lancamentos_obra").delete().eq("obra_id", o['id']).execute()
    supabase.table("obras").delete().eq("cliente_id", cliente_id).execute()
    supabase.table("clientes").delete().eq("id", cliente_id).execute()

# --- 8. LÓGICA DO MENU ---
if st.session_state.menu_aberto:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    perfil = st.session_state.user_perfil
    if st.button("📊 Dashboard"): st.session_state.pagina='RESUMO'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("💸 Lançar Gasto"): st.session_state.pagina='GASTO'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("📋 Relatórios"): st.session_state.pagina='LISTA'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("👤 Clientes"): st.session_state.pagina='CLIE'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("🤝 Fornecedores"): st.session_state.pagina='FORN'; st.session_state.menu_aberto=False; st.rerun()
    if perfil == 'ADMIN':
        if st.button("🏗️ Minhas Obras"): st.session_state.pagina='OBRA'; st.session_state.menu_aberto=False; st.rerun()
        if st.button("👥 Gestão de Equipe"): st.session_state.pagina='USUARIOS'; st.session_state.menu_aberto=False; st.rerun()
    if st.button("Sair (Logout)"): st.session_state.logado = False; st.session_state.menu_aberto=False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 9. TELAS ---
else:
    pag, perfil, ver = st.session_state.pagina, st.session_state.user_perfil, st.session_state.form_version

    if pag == 'RESUMO':
        obras_dict = listar_obras()
        if obras_dict:
            sel = st.selectbox("Selecione a Obra", [""] + list(obras_dict.keys()), index=0, key=f"sel_res_v{ver}")
            if sel:
                obra_info = obras_dict[sel]
                res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': obra_info['id']}).execute()
                gasto_total = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
                orcado = float(obra_info['orcamento']) if obra_info['orcamento'] else 0
                
                st.markdown('<p class="main-title">Saúde Financeira</p>', unsafe_allow_html=True)
                
                # --- KPI CARDS PADRONIZADOS ---
                kpi_col1, kpi_col2 = st.columns(2)
                with kpi_col1:
                    st.markdown(f'<div class="metric-container"><p class="metric-label">Valor Orçado</p><p class="metric-value">{formatar_real(orcado)}</p></div>', unsafe_allow_html=True)
                with kpi_col2:
                    st.markdown(f'<div class="metric-container"><p class="metric-label">Valor Realizado</p><p class="metric-value">{formatar_real(gasto_total)}</p></div>', unsafe_allow_html=True)
                
                if orcado > 0:
                    progresso = min(gasto_total / orcado, 1.0)
                    st.progress(progresso)
                    if gasto_total > orcado:
                        st.error(f"⚠️ Orçamento ultrapassado em {formatar_real(gasto_total - orcado)}")
                
                st.markdown(f'<div class="data-card"><small>Gasto Acumulado</small><h2>{formatar_real(gasto_total)}</h2></div>', unsafe_allow_html=True)
                if res_s.data: 
                    st.write("**Distribuição por Categoria:**")
                    st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'GASTO':
        st.markdown("### Lançamento de Gasto")
        obras, cats, forns = listar_obras(), listar_categorias(), listar_fornecedores()
        with st.container(border=True):
            o_sel = st.selectbox("Obra*", [""] + list(obras.keys()), index=0, key=f"go_{ver}")
            c = st.selectbox("Categoria*", [""] + list(cats.keys()), index=0, key=f"gc_{ver}")
            f_sel = st.selectbox("Fornecedor*", [""] + list(forns.keys()), index=0, key=f"gf_{ver}")
            d = st.text_input("Descrição", key=f"gd_{ver}")
            v = st.number_input("Valor Pago", min_value=0.0, key=f"gv_{ver}")
            foto = st.camera_input("Foto do Recibo", key=f"gp_{ver}")
            if st.button("SALVAR GASTO", use_container_width=True, type="primary"):
                if o_sel and c and f_sel and v > 0:
                    url = None
                    if foto:
                        n_arq = f"{uuid.uuid4()}.jpg"
                        supabase.storage.from_("comprovantes").upload(n_arq, foto.getvalue())
                        url = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{n_arq}"
                    supabase.table("lancamentos_obra").insert({"obra_id": obras[o_sel]['id'], "categoria_id": cats[c], "fornecedor_id": forns[f_sel], "descricao": d, "valor": v, "url_comprovante": url}).execute()
                    limpar_campos(); st.rerun()

    elif pag == 'FORN':
        st.markdown("### Fornecedores")
        dados_f = {"nome_fornecedor": "", "representante": "", "telefone": "", "whatsapp": "", "cnpj": "", "email": "", "endereco": ""}
        if st.session_state.forn_edit_id:
            res_f = supabase.table("fornecedores").select("*").eq("id", st.session_state.forn_edit_id).single().execute()
            if res_f.data: dados_f = res_f.data
        with st.container(border=True):
            fn = st.text_input("Empresa*", value=dados_f["nome_fornecedor"], key=f"fn_{ver}")
            fr = st.text_input("Representante*", value=dados_f["representante"], key=f"fr_{ver}")
            ft = st.text_input("Telefone*", value=dados_f["telefone"], key=f"ft_{ver}")
            fw = st.text_input("WhatsApp", value=dados_f["whatsapp"], key=f"fw_{ver}")
            fc = st.text_input("CNPJ", value=dados_f["cnpj"], key=f"fc_{ver}")
            fe = st.text_input("E-mail", value=dados_f["email"], key=f"fe_{ver}")
            fa = st.text_area("Endereço", value=dados_f["endereco"], key=f"fa_{ver}")
            if st.button("SALVAR FORNECEDOR", use_container_width=True, type="primary"):
                p = {"nome_fornecedor": fn, "representante": fr, "telefone": aplicar_mask_tel(ft), "whatsapp": aplicar_mask_tel(fw), "cnpj": aplicar_mask_cnpj(fc), "email": fe, "endereco": fa}
                if st.session_state.forn_edit_id: supabase.table("fornecedores").update(p).eq("id", st.session_state.forn_edit_id).execute()
                else: supabase.table("fornecedores").insert(p).execute()
                limpar_campos(); st.rerun()
        for f in (supabase.table("fornecedores").select("*").order("nome_fornecedor").execute().data or []):
            with st.expander(f"🏢 {f['nome_fornecedor']}"):
                c1, c2 = st.columns(2)
                if c1.button("📝 Editar", key=f"ef_{f['id']}"): st.session_state.forn_edit_id=f['id']; st.rerun()
                if c2.button("🗑️ Excluir", key=f"df_{f['id']}"): supabase.table("fornecedores").delete().eq("id", f['id']).execute(); st.rerun()

    elif pag == 'CLIE':
        st.markdown("### Clientes")
        dados_c = {"nome_cliente": "", "representante": "", "telefone": "", "whatsapp": "", "cnpj": "", "email": "", "endereco": ""}
        if st.session_state.clie_edit_id:
            res_c = supabase.table("clientes").select("*").eq("id", st.session_state.clie_edit_id).single().execute()
            if res_c.data: dados_c = res_c.data
        with st.container(border=True):
            cn = st.text_input("Nome/Empresa*", value=dados_c["nome_cliente"], key=f"cn_{ver}")
            cr = st.text_input("Pessoa de Contato*", value=dados_c["representante"], key=f"cr_{ver}")
            ct = st.text_input("Telefone*", value=dados_c["telefone"], key=f"ct_{ver}")
            cw = st.text_input("WhatsApp", value=dados_c["whatsapp"], key=f"cw_{ver}")
            cc = st.text_input("CNPJ/CPF", value=dados_c["cnpj"], key=f"cc_{ver}")
            ce = st.text_input("E-mail", value=dados_c["email"], key=f"ce_{ver}")
            ca = st.text_area("Endereço", value=dados_c["endereco"], key=f"ca_{ver}")
            if st.button("SALVAR CLIENTE", use_container_width=True, type="primary"):
                p = {"nome_cliente": cn, "representante": cr, "telefone": aplicar_mask_tel(ct), "whatsapp": aplicar_mask_tel(cw), "cnpj": aplicar_mask_cnpj(cc), "email": ce, "endereco": ca}
                if st.session_state.clie_edit_id: supabase.table("clientes").update(p).eq("id", st.session_state.clie_edit_id).execute()
                else: supabase.table("clientes").insert(p).execute()
                limpar_campos(); st.rerun()
        for c in (supabase.table("clientes").select("*").order("nome_cliente").execute().data or []):
            with st.expander(f"👤 {c['nome_cliente']}"):
                c1, c2 = st.columns(2)
                if c1.button("📝 Editar", key=f"ec_{c['id']}"): st.session_state.clie_edit_id=c['id']; st.rerun()
                if c2.button("🗑️ Excluir", key=f"dc_{c['id']}"):
                    excluir_em_cascata_cliente(c['id'])
                    st.rerun()

    elif pag == 'LISTA':
        st.markdown("### Histórico")
        obras_lista = listar_obras()
        if obras_lista:
            o_f = st.selectbox("Filtrar por Obra:", [""] + list(obras_lista.keys()), index=0, key=f"lo_{ver}")
            if o_f:
                c1, c2 = st.columns(2)
                d_i, d_f = c1.date_input("Início:", datetime.now().replace(day=1)), c2.date_input("Fim:", datetime.now())
                dados = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("obra_id", obras_lista[o_f]['id']).gte("created_at", d_i).lte("created_at", f"{d_f} 23:59:59").order("created_at", desc=True).execute().data
                if dados:
                    if perfil == 'ADMIN':
                        pdf_b = gerar_pdf(pd.DataFrame(dados), o_f)
                        st.download_button("📥 Baixar PDF", pdf_b, f"Relatorio_{o_f}.pdf", "application/pdf", use_container_width=True)
                    for g in dados:
                        with st.expander(f"{g['descricao']} | {formatar_real(g['valor'])}"):
                            if g.get('url_comprovante'): st.image(g['url_comprovante'])
                            if st.button("🗑️ Excluir Lançamento", key=f"dg_{g['id']}", use_container_width=True):
                                if g.get('url_comprovante'):
                                    try: supabase.storage.from_("comprovantes").remove([g['url_comprovante'].split('/')[-1]])
                                    except: pass
                                supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute(); st.rerun()

    elif pag == 'OBRA' and perfil == 'ADMIN':
        st.markdown("### Minhas Obras")
        dados_o = {"nome_obra": "", "cliente_id": "", "tipo_obra": "", "local_obra": "", "orcamento_previsto": 0.0}
        if st.session_state.obra_edit_id:
            res_eo = supabase.table("obras").select("*").eq("id", st.session_state.obra_edit_id).single().execute()
            if res_eo.data: dados_o = res_eo.data
        clis = listar_clientes(); id_to_name = {v: k for k, v in clis.items()}
        with st.container(border=True):
            on = st.text_input("Nome da Obra*", value=dados_o["nome_obra"], key=f"on_{ver}")
            cl_lista = [""] + list(clis.keys())
            cl_idx = cl_lista.index(id_to_name.get(dados_o["cliente_id"], "")) if dados_o["cliente_id"] in id_to_name else 0
            oc = st.selectbox("Cliente*", cl_lista, index=cl_idx, key=f"oc_{ver}")
            ot_lista = ["", "Residencial", "Comercial", "Reforma", "Industrial", "Outro"]
            ot_idx = ot_lista.index(dados_o["tipo_obra"]) if dados_o["tipo_obra"] in ot_lista else 0
            ot = st.selectbox("Tipo de Obra*", ot_lista, index=ot_idx, key=f"ot_{ver}")
            ol = st.text_input("Localização", value=dados_o["local_obra"], key=f"ol_{ver}")
            ov = st.number_input("Orçamento Previsto", min_value=0.0, value=float(dados_o["orcamento_previsto"]), key=f"ov_{ver}")
            if st.button("SALVAR OBRA", type="primary", use_container_width=True):
                p = {"nome_obra":on,"cliente_id":clis[oc],"tipo_obra":ot,"local_obra":ol,"orcamento_previsto":ov}
                if st.session_state.obra_edit_id: supabase.table("obras").update(p).eq("id", st.session_state.obra_edit_id).execute()
                else: supabase.table("obras").insert(p).execute()
                limpar_campos(); st.rerun()
        for ob in (supabase.table("obras").select("*, clientes(nome_cliente)").order("created_at", desc=True).execute().data or []):
            with st.expander(f"🏗️ {ob['nome_obra']}"):
                b1, b2 = st.columns(2)
                if b1.button("📝 Editar", key=f"eob_{ob['id']}"): st.session_state.obra_edit_id=ob['id']; st.rerun()
                if b2.button("🗑️ Excluir", key=f"dob_{ob['id']}"):
                    gastos = supabase.table("lancamentos_obra").select("url_comprovante").eq("obra_id", ob['id']).execute().data
                    for g in gastos:
                        if g.get('url_comprovante'):
                            try: supabase.storage.from_("comprovantes").remove([g['url_comprovante'].split('/')[-1]])
                            except: pass
                    supabase.table("lancamentos_obra").delete().eq("obra_id", ob['id']).execute()
                    supabase.table("obras").delete().eq("id", ob['id']).execute(); st.rerun()

    elif pag == 'USUARIOS' and perfil == 'ADMIN':
        st.markdown("### Gestão de Equipe")
        with st.container(border=True):
            ne, ns = st.text_input("E-mail", key=f"ue_{ver}"), st.text_input("Senha", type="password", key=f"us_{ver}")
            np = st.selectbox("Perfil", ["", "LANCADOR", "ADMIN"], index=0, key=f"up_{ver}")
            if st.button("CRIAR USUÁRIO", use_container_width=True, type="primary"):
                if ne and ns and np:
                    supabase.table("usuarios").insert({"email": ne, "senha": ns, "perfil": np}).execute()
                    limpar_campos(); st.rerun()
        st.table(pd.DataFrame(supabase.table("usuarios").select("email, perfil").execute().data))
