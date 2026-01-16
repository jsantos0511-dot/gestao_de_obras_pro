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
if 'forn_edit_id' not in st.session_state: st.session_state.forn_edit_id = None
if 'clie_edit_id' not in st.session_state: st.session_state.clie_edit_id = None
if 'obra_edit_id' not in st.session_state: st.session_state.obra_edit_id = None

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

# --- 3. FUNÇÕES DE FORMATAÇÃO (MÁSCARAS) ---
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

# --- 4. ESTILO VISUAL (LOGO QUADRADA E CARDS) ---
st.markdown(f"""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {{display: none;}}
    .block-container {{ padding-top: 1rem !important; }}
    img {{ border-radius: 0px !important; }}
    .stImage > img {{ border-radius: 0px !important; display: block; margin-left: auto; margin-right: auto; }}
    .data-card {{ 
        background: #ffffff; padding: 20px; border-radius: 15px; 
        border: 1px solid #eee; margin-bottom: 15px; color: #1e1e1e; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    .data-card h2 {{ color: #1E1E1E !important; margin: 0; font-weight: 800; }}
    .data-card small {{ color: #666 !important; font-weight: 700; text-transform: uppercase; }}
    div.stButton > button[key="trigger"] {{
        background-color: transparent !important; color: #1E1E1E !important;
        width: 45px !important; height: 45px !important; border: none !important;
        font-size: 35px !important; display: flex !important; align-items: center !important; justify-content: center !important;
    }}
    .nav-card {{ width: 70% !important; margin: 0 auto !important; text-align: center; }}
    .nav-card button {{ width: 100% !important; height: 60px !important; border-radius: 8px !important; font-weight: 700 !important; margin-bottom: 8px !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. TELA DE LOGIN ---
if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image(LOGO_URL, width=220)
        st.markdown("<br>", unsafe_allow_html=True)
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
    res = supabase.table("obras").select("id, nome_obra").execute()
    return {item['nome_obra']: item['id'] for item in res.data}

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
    if st.button("Sair (Logout)", type="secondary"): st.session_state.logado = False; st.session_state.menu_aberto=False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 9. TELAS ---
else:
    pag, perfil = st.session_state.pagina, st.session_state.user_perfil

    if pag == 'RESUMO':
        obras = listar_obras()
        if obras:
            sel = st.selectbox("Selecione a Obra", [""] + list(obras.keys()), index=0)
            if sel:
                res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': obras[sel]}).execute()
                gasto = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
                if perfil == 'ADMIN':
                    info = supabase.table("obras").select("*").eq("id", obras[sel]).single().execute().data
                    st.markdown(f'<div class="data-card"><small>INVESTIMENTO TOTAL</small><h2>{formatar_real(gasto)}</h2><hr style="border:0.5px solid #eee;"><small>SALDO: <b>{formatar_real(float(info["orcamento_previsto"]) - gasto)}</b></small></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="data-card"><small>GASTO ACUMULADO</small><h2>{formatar_real(gasto)}</h2></div>', unsafe_allow_html=True)
                if res_s.data: st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'GASTO':
        st.markdown("### 💸 Lançamento")
        obras, cats, forns = listar_obras(), listar_categorias(), listar_fornecedores()
        with st.container(border=True):
            o = st.selectbox("Obra*", [""] + list(obras.keys()), index=0)
            c = st.selectbox("Categoria*", [""] + list(cats.keys()), index=0)
            f_sel = st.selectbox("Fornecedor*", [""] + list(forns.keys()), index=0)
            d = st.text_input("Descrição")
            v = st.number_input("Valor Pago", min_value=0.0)
            foto = st.camera_input("Foto do Recibo")
            if st.button("SALVAR GASTO", use_container_width=True, type="primary"):
                if o and c and f_sel and v > 0:
                    url = None
                    if foto:
                        n_arq = f"{uuid.uuid4()}.jpg"; supabase.storage.from_("comprovantes").upload(n_arq, foto.getvalue())
                        url = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{n_arq}"
                    supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "fornecedor_id": forns[f_sel], "descricao": d, "valor": v, "url_comprovante": url}).execute()
                    st.success("Salvo!"); st.rerun()
                else: st.error("Preencha os campos obrigatórios.")

    elif pag == 'FORN':
        st.markdown("### 🤝 Gestão de Fornecedores")
        dados_f = {"nome_fornecedor": "", "telefone": "", "cnpj": ""}
        if st.session_state.forn_edit_id:
            res_f = supabase.table("fornecedores").select("*").eq("id", st.session_state.forn_edit_id).single().execute()
            if res_f.data: dados_f = res_f.data
        with st.container(border=True):
            fn = st.text_input("Nome da Empresa*", value=dados_f["nome_fornecedor"])
            ft = st.text_input("Telefone*", value=dados_f["telefone"])
            fc = st.text_input("CNPJ", value=dados_f["cnpj"])
            if st.button("SALVAR FORNECEDOR", use_container_width=True, type="primary"):
                p = {"nome_fornecedor": fn, "telefone": aplicar_mask_tel(ft), "cnpj": aplicar_mask_cnpj(fc)}
                if st.session_state.forn_edit_id:
                    supabase.table("fornecedores").update(p).eq("id", st.session_state.forn_edit_id).execute()
                    st.session_state.forn_edit_id = None
                else: supabase.table("fornecedores").insert(p).execute()
                st.rerun()
        for f in (supabase.table("fornecedores").select("*").order("nome_fornecedor").execute().data or []):
            with st.expander(f"🏢 {f['nome_fornecedor']}"):
                st.write(f"CNPJ: {f['cnpj']} | Tel: {f['telefone']}")
                c1, c2 = st.columns(2)
                if c1.button("📝 Editar", key=f"ef_{f['id']}"): st.session_state.forn_edit_id=f['id']; st.rerun()
                if c2.button("🗑️ Excluir", key=f"df_{f['id']}"): supabase.table("fornecedores").delete().eq("id", f['id']).execute(); st.rerun()

    elif pag == 'CLIE':
        st.markdown("### 👤 Gestão de Clientes")
        dados_c = {"nome_cliente": "", "telefone": "", "cnpj": ""}
        if st.session_state.clie_edit_id:
            res_c = supabase.table("clientes").select("*").eq("id", st.session_state.clie_edit_id).single().execute()
            if res_c.data: dados_c = res_c.data
        with st.container(border=True):
            cn = st.text_input("Nome/Empresa*", value=dados_c["nome_cliente"])
            ct = st.text_input("Telefone*", value=dados_c["telefone"])
            cc = st.text_input("CNPJ", value=dados_c["cnpj"])
            if st.button("SALVAR CLIENTE", use_container_width=True, type="primary"):
                p = {"nome_cliente": cn, "telefone": aplicar_mask_tel(ct), "cnpj": aplicar_mask_cnpj(cc)}
                if st.session_state.clie_edit_id:
                    supabase.table("clientes").update(p).eq("id", st.session_state.clie_edit_id).execute()
                    st.session_state.clie_edit_id = None
                else: supabase.table("clientes").insert(p).execute()
                st.rerun()
        for c in (supabase.table("clientes").select("*").order("nome_cliente").execute().data or []):
            with st.expander(f"👤 {c['nome_cliente']}"):
                st.write(f"CNPJ: {c['cnpj']} | Tel: {c['telefone']}")
                c1, c2 = st.columns(2)
                if c1.button("📝 Editar", key=f"ec_{c['id']}"): st.session_state.clie_edit_id=c['id']; st.rerun()
                if c2.button("🗑️ Excluir", key=f"dc_{c['id']}"): supabase.table("clientes").delete().eq("id", c['id']).execute(); st.rerun()

    elif pag == 'LISTA':
        st.markdown("### 📋 Histórico")
        obras = listar_obras()
        if obras:
            o_f = st.selectbox("Obra:", [""] + list(obras.keys()), index=0)
            if o_f:
                c1, c2 = st.columns(2)
                d_i, d_f = c1.date_input("Início:", datetime.now().replace(day=1)), c2.date_input("Fim:", datetime.now())
                dados = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("obra_id", obras[o_f]).gte("created_at", d_i).lte("created_at", f"{d_f} 23:59:59").order("created_at", desc=True).execute().data
                if dados:
                    if perfil == 'ADMIN':
                        pdf_b = gerar_pdf(pd.DataFrame(dados), o_f)
                        st.download_button("📥 PDF", pdf_b, f"Relatorio_{o_f}.pdf", "application/pdf", use_container_width=True)
                    for g in dados:
                        with st.expander(f"{g['descricao']} | {formatar_real(g['valor'])}"):
                            if g.get('url_comprovante'): st.image(g['url_comprovante'])
                            if st.button("🗑️ Excluir", key=f"dg_{g['id']}", use_container_width=True):
                                supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute(); st.rerun()

    elif pag == 'OBRA' and perfil == 'ADMIN':
        st.markdown("### 🏗️ Gestão de Obras")
        dados_o = {"nome_obra": "", "cliente_id": "", "tipo_obra": "", "local_obra": "", "orcamento_previsto": 0.0}
        if st.session_state.obra_edit_id:
            res_eo = supabase.table("obras").select("*").eq("id", st.session_state.obra_edit_id).single().execute()
            if res_eo.data: dados_o = res_eo.data
        clis = listar_clientes(); id_to_name = {v: k for k, v in clis.items()}
        with st.container(border=True):
            on = st.text_input("Nome da Obra*", value=dados_o["nome_obra"])
            cl_lista = [""] + list(clis.keys())
            cl_idx = cl_lista.index(id_to_name.get(dados_o["cliente_id"], "")) if dados_o["cliente_id"] in id_to_name else 0
            oc = st.selectbox("Cliente*", cl_lista, index=cl_idx)
            ot_lista = ["", "Residencial", "Comercial", "Reforma", "Industrial", "Outro"]
            ot_idx = ot_lista.index(dados_o["tipo_obra"]) if dados_o["tipo_obra"] in ot_lista else 0
            ot = st.selectbox("Tipo*", ot_lista, index=ot_idx)
            ol = st.text_input("Local", value=dados_o["local_obra"])
            ov = st.number_input("Orçamento", min_value=0.0, value=float(dados_o["orcamento_previsto"]))
            c1, c2 = st.columns(2)
            if st.session_state.obra_edit_id:
                if c1.button("ATUALIZAR", type="primary", use_container_width=True):
                    supabase.table("obras").update({"nome_obra":on,"cliente_id":clis[oc],"tipo_obra":ot,"local_obra":ol,"orcamento_previsto":ov}).eq("id", st.session_state.obra_edit_id).execute()
                    st.session_state.obra_edit_id = None; st.rerun()
                if c2.button("CANCELAR", use_container_width=True): st.session_state.obra_edit_id = None; st.rerun()
            else:
                if st.button("CADASTRAR", type="primary", use_container_width=True):
                    if on and oc:
                        supabase.table("obras").insert({"nome_obra":on,"cliente_id":clis[oc],"tipo_obra":ot,"local_obra":ol,"orcamento_previsto":ov}).execute(); st.rerun()
        for ob in (supabase.table("obras").select("*, clientes(nome_cliente)").order("created_at", desc=True).execute().data or []):
            with st.expander(f"🏗️ {ob['nome_obra']}"):
                st.write(f"Cli: {ob['clientes']['nome_cliente'] if ob.get('clientes') else 'N/A'} | Orç: {formatar_real(ob['orcamento_previsto'])}")
                b1, b2 = st.columns(2)
                if b1.button("📝", key=f"eob_{ob['id']}"): st.session_state.obra_edit_id=ob['id']; st.rerun()
                if b2.button("🗑️", key=f"dob_{ob['id']}"): supabase.table("obras").delete().eq("id", ob['id']).execute(); st.rerun()

    elif pag == 'USUARIOS' and perfil == 'ADMIN':
        st.markdown("### 👥 Equipe")
        with st.container(border=True):
            ne, ns = st.text_input("E-mail"), st.text_input("Senha", type="password")
            np = st.selectbox("Perfil", ["", "LANCADOR", "ADMIN"], index=0)
            if st.button("CRIAR USUÁRIO", use_container_width=True, type="primary"):
                if ne and ns and np:
                    supabase.table("usuarios").insert({"email": ne, "senha": ns, "perfil": np}).execute(); st.rerun()
        st.table(pd.DataFrame(supabase.table("usuarios").select("email, perfil").execute().data))
