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
def formatar_cnpj(cnpj):
    # Remove tudo que não é número
    num = re.sub(r'\D', '', cnpj)
    if len(num) == 14:
        return f"{num[:2]}.{num[2:5]}.{num[5:8]}/{num[8:12]}-{num[12:]}"
    return cnpj

def formatar_telefone(tel):
    num = re.sub(r'\D', '', tel)
    if len(num) == 11:
        return f"({num[:2]}) {num[2:7]}-{num[7:]}"
    elif len(num) == 10:
        return f"({num[:2]}) {num[2:6]}-{num[6:]}"
    return tel

# --- 4. ESTILO VISUAL ---
st.markdown(f"""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {{display: none;}}
    .block-container {{ padding-top: 1rem !important; }}
    img {{ border-radius: 0px !important; }}
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
        font-size: 35px !important; padding: 0 !important; display: flex !important;
        align-items: center !important; justify-content: center !important;
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
            sel = st.selectbox("Selecione a Obra", list(obras.keys()), label_visibility="collapsed")
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
            o = st.selectbox("Obra", list(obras.keys()))
            c = st.selectbox("Categoria", list(cats.keys()))
            f_sel = st.selectbox("Fornecedor", list(forns.keys()))
            d = st.text_input("Descrição")
            v = st.number_input("Valor Pago", min_value=0.0)
            foto = st.camera_input("Foto do Recibo")
            if st.button("SALVAR GASTO", use_container_width=True, type="primary"):
                url = None
                if foto:
                    n_arq = f"{uuid.uuid4()}.jpg"
                    supabase.storage.from_("comprovantes").upload(n_arq, foto.getvalue())
                    url = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{n_arq}"
                supabase.table("lancamentos_obra").insert({"obra_id": obras[o], "categoria_id": cats[c], "fornecedor_id": forns[f_sel], "descricao": d, "valor": v, "url_comprovante": url}).execute()
                st.success("Salvo!"); st.session_state.pagina = 'LISTA'; st.rerun()

    elif pag == 'FORN':
        st.markdown("### 🤝 Gestão de Fornecedores")
        dados_edit = {"nome_fornecedor": "", "representante": "", "telefone": "", "whatsapp": "", "cnpj": "", "email": "", "endereco": ""}
        if st.session_state.forn_edit_id:
            res_edit = supabase.table("fornecedores").select("*").eq("id", st.session_state.forn_edit_id).single().execute()
            if res_edit.data: dados_edit = res_edit.data

        with st.container(border=True):
            fn = st.text_input("Nome da Empresa*", value=dados_edit["nome_fornecedor"])
            fr = st.text_input("Representante*", value=dados_edit["representante"])
            ft = st.text_input("Telefone*", value=dados_edit["telefone"], help="Somente números")
            fw = st.text_input("WhatsApp", value=dados_edit["whatsapp"], placeholder="(99) 99999-9999")
            fc = st.text_input("CNPJ", value=dados_edit["cnpj"], placeholder="00.000.000/0000-00")
            fe = st.text_input("E-mail", value=dados_edit["email"])
            fa = st.text_area("Endereço", value=dados_edit["endereco"])
            
            if st.button("SALVAR FORNECEDOR", use_container_width=True, type="primary"):
                # Aplica as máscaras antes de salvar
                ft_format = formatar_telefone(ft)
                fw_format = formatar_telefone(fw)
                fc_format = formatar_cnpj(fc)

                if not fn or not fr or not ft: st.error("Preencha os obrigatórios")
                else:
                    payload = {"nome_fornecedor": fn, "representante": fr, "telefone": ft_format, "whatsapp": fw_format, "cnpj": fc_format, "email": fe, "endereco": fa}
                    if st.session_state.forn_edit_id:
                        supabase.table("fornecedores").update(payload).eq("id", st.session_state.forn_edit_id).execute()
                        st.session_state.forn_edit_id = None
                    else:
                        supabase.table("fornecedores").insert(payload).execute()
                    st.success("Salvo com sucesso!"); st.rerun()
        
        st.markdown("---")
        lista_f = supabase.table("fornecedores").select("*").order("nome_fornecedor").execute().data
        for f in (lista_f or []):
            with st.expander(f"🏢 {f['nome_fornecedor']}"):
                st.write(f"**Contato:** {f['representante']} | **Tel:** {f['telefone']}")
                st.write(f"**WhatsApp:** {f['whatsapp']} | **CNPJ:** {f['cnpj']}")
                col1, col2 = st.columns(2)
                if col1.button("📝 Editar", key=f"ef_{f['id']}", use_container_width=True): st.session_state.forn_edit_id=f['id']; st.rerun()
                if col2.button("🗑️ Excluir", key=f"df_{f['id']}", use_container_width=True): supabase.table("fornecedores").delete().eq("id", f['id']).execute(); st.rerun()

    elif pag == 'CLIE':
        st.markdown("### 👤 Gestão de Clientes")
        dados_edit = {"nome_cliente": "", "representante": "", "telefone": "", "whatsapp": "", "cnpj": "", "email": "", "endereco": ""}
        if st.session_state.clie_edit_id:
            res_edit = supabase.table("clientes").select("*").eq("id", st.session_state.clie_edit_id).single().execute()
            if res_edit.data: dados_edit = res_edit.data

        with st.container(border=True):
            cn = st.text_input("Nome/Empresa*", value=dados_edit["nome_cliente"])
            cr = st.text_input("Representante*", value=dados_edit["representante"])
            ct = st.text_input("Telefone*", value=dados_edit["telefone"])
            cw = st.text_input("WhatsApp", value=dados_edit["whatsapp"])
            cc = st.text_input("CNPJ", value=dados_edit["cnpj"])
            ce = st.text_input("E-mail", value=dados_edit["email"])
            ca = st.text_area("Endereço", value=dados_edit["endereco"])

            if st.button("SALVAR CLIENTE", use_container_width=True, type="primary"):
                # Aplica as máscaras antes de salvar
                ct_f = formatar_telefone(ct)
                cw_f = formatar_telefone(cw)
                cc_f = formatar_cnpj(cc)

                if not cn or not cr or not ct: st.error("Preencha os obrigatórios")
                else:
                    payload = {"nome_cliente": cn, "representante": cr, "telefone": ct_f, "whatsapp": cw_f, "cnpj": cc_f, "email": ce, "endereco": ca}
                    if st.session_state.clie_edit_id:
                        supabase.table("clientes").update(payload).eq("id", st.session_state.clie_edit_id).execute()
                        st.session_state.clie_edit_id = None
                    else:
                        supabase.table("clientes").insert(payload).execute()
                    st.success("Cliente Salvo!"); st.rerun()

        st.markdown("---")
        lista_c = supabase.table("clientes").select("*").order("nome_cliente").execute().data
        for c in (lista_c or []):
            with st.expander(f"👤 {c['nome_cliente']}"):
                st.write(f"**Contato:** {c['representante']} | **Tel:** {c['telefone']}")
                st.write(f"**WhatsApp:** {c['whatsapp']} | **CNPJ:** {c['cnpj']}")
                ce_ed, ce_dl = st.columns(2)
                if ce_ed.button("📝 Editar", key=f"ec_{c['id']}", use_container_width=True): st.session_state.clie_edit_id = c['id']; st.rerun()
                if ce_dl.button("🗑️ Excluir", key=f"dc_{c['id']}", use_container_width=True): supabase.table("clientes").delete().eq("id", c['id']).execute(); st.rerun()

    elif pag == 'LISTA':
        st.markdown("### 📋 Histórico")
        obras = listar_obras()
        if obras:
            o_f = st.selectbox("Obra:", list(obras.keys()))
            dados = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria)").eq("obra_id", obras[o_f]).order("created_at", desc=True).execute().data
            if dados:
                for g in dados:
                    with st.expander(f"{g['descricao']} | {formatar_real(g['valor'])}"):
                        if g.get('url_comprovante'): st.image(g['url_comprovante'])
                        if st.button("🗑️ Excluir Gasto", key=f"dg_{g['id']}", use_container_width=True): supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute(); st.rerun()

    elif pag == 'OBRA' and perfil == 'ADMIN':
        st.markdown("### 🏗️ Gestão de Obras")
        with st.container(border=True):
            n, v = st.text_input("Nome"), st.number_input("Orçamento", min_value=0.0)
            if st.button("CADASTRAR", use_container_width=True):
                supabase.table("obras").insert({"nome_obra": n, "orcamento_previsto": v}).execute(); st.rerun()

    elif pag == 'USUARIOS' and perfil == 'ADMIN':
        st.markdown("### 👥 Equipe")
        with st.container(border=True):
            ne, ns, np = st.text_input("E-mail"), st.text_input("Senha"), st.selectbox("Perfil", ["LANCADOR", "ADMIN"])
            if st.button("CRIAR", use_container_width=True):
                supabase.table("usuarios").insert({"email": ne, "senha": ns, "perfil": np}).execute(); st.rerun()
        st.table(pd.DataFrame(supabase.table("usuarios").select("email, perfil").execute().data))
