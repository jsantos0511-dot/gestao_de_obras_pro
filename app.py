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
    res = supabase.table("obras").select("*").execute()
    return {str(item['nome_obra']): item for item in res.data}

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
            gastos = supabase.table("lancamentos_obra").select("id, url_comprovante").eq("obra_id", o['id']).execute().data
            for g in gastos:
                if g.get('url_comprovante'):
                    try: supabase.storage.from_("comprovantes").remove([g['url_comprovante'].split('/')[-1]])
                    except: pass
            supabase.table("lancamentos_obra").delete().eq("id_obra", o['id']).execute() # Ajustado para bater com o banco se necessário
        supabase.table("obras").delete().eq("cliente_id", cliente_id).execute()
        supabase.table("clientes").delete().eq("id", cliente_id).execute()
    except Exception as e:
        st.error(f"Erro ao excluir cliente: Verifique se existem vínculos ativos.")

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
        obras_dict = listar_obras()
        if obras_dict:
            sel = st.selectbox("Selecione a Obra", [""] + list(obras_dict.keys()), index=0, key=f"sel_res_v{ver}")
            if sel:
                obra_info = obras_dict[sel]
                # Cálculo financeiro a partir dos lançamentos
                res_gastos = supabase.table("lancamentos_obra").select("valor").eq("obra_id", obra_info['id']).execute()
                gasto_total = sum(float(i['valor']) for i in res_gastos.data) if res_gastos.data else 0
                
                orcado = float(obra_info.get('orcamento_previsto', 0))
                perc_lucro = float(obra_info.get('lucro_estimado', 0))
                perc_imposto = float(obra_info.get('impostos_estimados', 0))
                
                valor_lucro_previsto = orcado * (perc_lucro / 100)
                valor_imposto = orcado * (perc_imposto / 100)
                lucro_real = orcado - gasto_total - valor_imposto
                
                st.markdown('<p class="main-title">Saúde Financeira</p>', unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f'<div class="metric-container"><p class="metric-label">Orçado</p><p class="metric-value">{formatar_real(orcado)}</p></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="metric-container"><p class="metric-label">Exp. Lucro</p><p class="metric-value">{formatar_real(valor_lucro_previsto)}</p></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="metric-container"><p class="metric-label">Imposto ({perc_imposto}%)</p><p class="metric-value">{formatar_real(valor_imposto)}</p></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="metric-container"><p class="metric-label">Lucro Real</p><p class="metric-value" style="color:{"#00FF00" if lucro_real > 0 else "#FF0000"}">{formatar_real(lucro_real)}</p></div>', unsafe_allow_html=True)
                
                st.markdown(f'<div class="data-card"><small>Gasto Acumulado (Realizado)</small><h3>{formatar_real(gasto_total)}</h3></div>', unsafe_allow_html=True)
                if orcado > 0:
                    st.progress(min(gasto_total / orcado, 1.0))
                    if gasto_total > orcado: st.error(f"Orçamento excedido em {formatar_real(gasto_total - orcado)}")

    elif pag == 'GASTO':
        st.markdown("### Lançamento")
        obs_dict = listar_obras()
        cats, forns = listar_categorias(), listar_fornecedores()
        with st.container(border=True):
            o_sel = st.selectbox("Obra*", [""] + list(obs_dict.keys()), index=0, key=f"go_{ver}")
            c = st.selectbox("Categoria*", [""] + list(cats.keys()), index=0, key=f"gc_{ver}")
            f_sel = st.selectbox("Fornecedor*", [""] + list(forns.keys()), index=0, key=f"gf_{ver}")
            d = st.text_input("Descrição", key=f"gd_{ver}")
            v = st.number_input("Valor", min_value=0.0, key=f"gv_{ver}")
            status_p = st.selectbox("Status de Pagamento", ["Pago", "Pendente"], key=f"gs_{ver}")
            foto = st.camera_input("Recibo", key=f"gp_{ver}")
            if st.button("SALVAR GASTO", use_container_width=True, type="primary"):
                if o_sel and c and f_sel and v > 0:
                    try:
                        url = None
                        if foto:
                            n_arq = f"{uuid.uuid4()}.jpg"
                            supabase.storage.from_("comprovantes").upload(n_arq, foto.getvalue())
                            url = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{n_arq}"
                        supabase.table("lancamentos_obra").insert({"obra_id": obs_dict[o_sel]['id'], "categoria_id": cats[c], "fornecedor_id": forns[f_sel], "descricao": d, "valor": v, "url_comprovante": url, "status_pagamento": status_p}).execute()
                        limpar_campos(); st.rerun()
                    except Exception as e: st.error(f"Erro ao salvar: Verifique os campos no Supabase.")

    elif pag == 'FORN':
        st.markdown("### Fornecedores")
        df = {"nome_fornecedor": "", "representante": "", "telefone": "", "whatsapp": "", "cnpj": "", "email": "", "endereco": ""}
        if st.session_state.forn_edit_id:
            res = supabase.table("fornecedores").select("*").eq("id", st.session_state.forn_edit_id).single().execute()
            if res.data: df = res.data
        with st.container(border=True):
            fn = st.text_input("Empresa*", value=df["nome_fornecedor"], key=f"fn_{ver}")
            fr = st.text_input("Representante*", value=df["representante"], key=f"fr_{ver}")
            ft = st.text_input("Telefone*", value=df["telefone"], key=f"ft_{ver}")
            fw = st.text_input("WhatsApp", value=df["whatsapp"], key=f"fw_{ver}")
            fc = st.text_input("CNPJ", value=df["cnpj"], key=f"fc_{ver}")
            fe = st.text_input("E-mail", value=df["email"], key=f"fe_{ver}")
            fa = st.text_area("Endereço", value=df["endereco"], key=f"fa_{ver}")
            if st.button("SALVAR", use_container_width=True, type="primary"):
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
        dc = {"nome_cliente": "", "representante": "", "telefone": "", "whatsapp": "", "cnpj": "", "email": "", "endereco": ""}
        if st.session_state.clie_edit_id:
            res = supabase.table("clientes").select("*").eq("id", st.session_state.clie_edit_id).single().execute()
            if res.data: dc = res.data
        with st.container(border=True):
            cn = st.text_input("Cliente*", value=dc["nome_cliente"], key=f"cn_{ver}")
            cr = st.text_input("Contato*", value=dc["representante"], key=f"cr_{ver}")
            ct = st.text_input("Tel*", value=dc["telefone"], key=f"ct_{ver}")
            cw = st.text_input("Zap", value=dc["whatsapp"], key=f"cw_{ver}")
            cc = st.text_input("CNPJ/CPF", value=dc["cnpj"], key=f"cc_{ver}")
            ce = st.text_input("E-mail", value=dc["email"], key=f"ce_{ver}")
            ca = st.text_area("Endereço", value=dc["endereco"], key=f"ca_{ver}")
            if st.button("SALVAR CLIENTE", use_container_width=True, type="primary"):
                p = {"nome_cliente": cn, "representante": cr, "telefone": aplicar_mask_tel(ct), "whatsapp": aplicar_mask_tel(cw), "cnpj": aplicar_mask_cnpj(cc), "email": ce, "endereco": ca}
                try:
                    if st.session_state.clie_edit_id: supabase.table("clientes").update(p).eq("id", st.session_state.clie_edit_id).execute()
                    else: supabase.table("clientes").insert(p).execute()
                    limpar_campos(); st.rerun()
                except: st.error("Erro ao salvar cliente. Verifique os dados.")
        for c in (supabase.table("clientes").select("*").order("nome_cliente").execute().data or []):
            with st.expander(f"👤 {c['nome_cliente']}"):
                c1, c2 = st.columns(2)
                if c1.button("📝 Editar", key=f"ec_{c['id']}"): st.session_state.clie_edit_id=c['id']; st.rerun()
                if c2.button("🗑️ Excluir", key=f"dc_{c['id']}"): excluir_em_cascata_cliente(c['id']); st.rerun()

    elif pag == 'LISTA':
        st.markdown("### Histórico")
        obs_dict_l = listar_obras()
        cats_l = listar_categorias()
        if obs_dict_l:
            with st.container(border=True):
                o_f = st.selectbox("Filtrar por Obra:", [""] + list(obs_dict_l.keys()), index=0, key=f"lo_{ver}")
                col_f1, col_f2 = st.columns(2)
                cat_f = col_f1.selectbox("Categoria:", ["Todas"] + list(cats_l.keys()), key=f"lf_cat_{ver}")
                stat_f = col_f2.selectbox("Status:", ["Todos", "Pago", "Pendente"], key=f"lf_stat_{ver}")
                d_i, d_f = st.date_input("Período:", [datetime.now().replace(day=1), datetime.now()])
            if o_f:
                query = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria), fornecedores(nome_fornecedor)").eq("obra_id", obs_dict_l[o_f]['id']).gte("created_at", d_i).lte("created_at", f"{d_f} 23:59:59")
                if cat_f != "Todas": query = query.eq("categoria_id", cats_l[cat_f])
                if stat_f != "Todos": query = query.eq("status_pagamento", stat_f)
                dados = query.order("created_at", desc=True).execute().data
                if dados:
                    c_down1, c_down2 = st.columns(2)
                    pdf_b = gerar_pdf(pd.DataFrame(dados), o_f)
                    c_down1.download_button("📥 PDF", pdf_b, f"Relatorio_{o_f}.pdf", use_container_width=True)
                    xls_b = gerar_excel(pd.DataFrame(dados))
                    c_down2.download_button("📊 Excel", xls_b, f"Relatorio_{o_f}.xlsx", use_container_width=True)
                    for g in dados:
                        cor = "🟢" if g.get('status_pagamento') == "Pago" else "🔴"
                        with st.expander(f"{cor} {g['descricao']} | {formatar_real(g['valor'])}"):
                            if g.get('url_comprovante'): st.image(g['url_comprovante'])
                            if st.button("🗑️ Excluir", key=f"dg_{g['id']}", use_container_width=True):
                                if g.get('url_comprovante'):
                                    try: supabase.storage.from_("comprovantes").remove([g['url_comprovante'].split('/')[-1]])
                                    except: pass
                                supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute(); st.rerun()

    elif pag == 'OBRA' and perf == 'ADMIN':
        st.markdown("### Cadastro de Obras")
        do = {"nome_obra": "", "cliente_id": "", "tipo_obra": "", "local_obra": "", "orcamento_previsto": 0.0, "lucro_estimado": 0.0, "impostos_estimados": 0.0}
        if st.session_state.obra_edit_id:
            res = supabase.table("obras").select("*").eq("id", st.session_state.obra_edit_id).single().execute()
            if res.data: do = res.data
        clis = listar_clientes(); id_to_name = {v: k for k, v in clis.items()}
        with st.container(border=True):
            on = st.text_input("Nome da Obra*", value=do["nome_obra"], key=f"on_{ver}")
            cl_idx = ([""] + list(clis.keys())).index(id_to_name.get(do["cliente_id"], "")) if do["cliente_id"] in id_to_name else 0
            oc = st.selectbox("Cliente*", [""] + list(clis.keys()), index=cl_idx, key=f"oc_{ver}")
            ov = st.number_input("Orçamento Previsto (R$)", min_value=0.0, value=float(do["orcamento_previsto"]), key=f"ov_{ver}")
            c_luc, c_imp = st.columns(2)
            olucro = c_luc.number_input("Lucro (%)", min_value=0.0, max_value=100.0, value=float(do.get("lucro_estimado", 0)), key=f"olucro_{ver}")
            oimposto = c_imp.number_input("Imposto (%)", min_value=0.0, max_value=100.0, value=float(do.get("impostos_estimados", 0)), key=f"oimposto_{ver}")
            ot_lista = ["", "Residencial", "Comercial", "Reforma", "Industrial", "Outro"]
            ot_idx = ot_lista.index(do["tipo_obra"]) if do["tipo_obra"] in ot_lista else 0
            ot = st.selectbox("Tipo*", ot_lista, index=ot_idx, key=f"ot_{ver}")
            ol = st.text_input("Localização", value=do["local_obra"], key=f"ol_{ver}")
            if st.button("SALVAR OBRA", type="primary", use_container_width=True):
                p = {"nome_obra":on,"cliente_id":clis[oc],"tipo_obra":ot,"local_obra":ol,"orcamento_previsto":ov,"lucro_estimado":olucro,"impostos_estimados":oimposto}
                try:
                    if st.session_state.obra_edit_id: supabase.table("obras").update(p).eq("id", st.session_state.obra_edit_id).execute()
                    else: supabase.table("obras").insert(p).execute()
                    limpar_campos(); st.rerun()
                except Exception as e: st.error(f"Erro ao salvar obra.")
        for ob in (supabase.table("obras").select("*, clientes(nome_cliente)").order("created_at", desc=True).execute().data or []):
            with st.expander(f"🏗️ {str(ob['nome_obra'])}"):
                st.write(f"**Orçamento:** {formatar_real(ob['orcamento_previsto'])} | **Lucro:** {ob.get('lucro_estimado')}%")
                b1, b2 = st.columns(2)
                if b1.button("📝 Editar", key=f"eob_{ob['id']}"): st.session_state.obra_edit_id=ob['id']; st.rerun()
                if b2.button("🗑️ Excluir", key=f"dob_{ob['id']}"):
                    supabase.table("lancamentos_obra").delete().eq("obra_id", ob['id']).execute()
                    supabase.table("obras").delete().eq("id", ob['id']).execute(); st.rerun()

    elif pag == 'USUARIOS' and perf == 'ADMIN':
        st.markdown("### Equipe")
        with st.container(border=True):
            ne, ns = st.text_input("E-mail", key=f"ue_{ver}"), st.text_input("Senha", type="password", key=f"us_{ver}")
            np = st.selectbox("Perfil", ["", "LANCADOR", "ADMIN"], index=0, key=f"up_{ver}")
            if st.button("CADASTRAR", use_container_width=True, type="primary"):
                if ne and ns and np:
                    supabase.table("usuarios").insert({"email": ne, "senha": ns, "perfil": np}).execute()
                    limpar_campos(); st.rerun()
        st.table(pd.DataFrame(supabase.table("usuarios").select("email, perfil").execute().data))
