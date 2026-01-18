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

# Inicialização de IDs de edição para evitar erros de navegação
for key in ['forn_edit_id', 'clie_edit_id', 'obra_edit_id']:
    if key not in st.session_state:
        st.session_state[key] = None

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
    except:
        pass
    return False

# --- 3. FORMATADORES ---
def aplicar_mask_cnpj(cnpj):
    if not cnpj: return ""
    num = re.sub(r'\D', '', str(cnpj))
    if len(num) == 14:
        return f"{num[:2]}.{num[2:5]}.{num[5:8]}/{num[8:12]}-{num[12:]}"
    return cnpj

def aplicar_mask_tel(tel):
    if not tel: return ""
    num = re.sub(r'\D', '', str(tel))
    if len(num) == 11: return f"({num[:2]}) {num[2:7]}-{num[7:]}"
    elif len(num) == 10: return f"({num[:2]}) {num[2:6]}-{num[6:]}"
    return tel

def formatar_real(valor):
    if valor is None: valor = 0
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# --- 4. ESTILO VISUAL (LOGO COM CANTOS RETOS) ---
st.markdown(f"""
    <style>
    [data-testid="stSidebar"], [data-testid="stHeader"] {{display: none;}}
    .block-container {{ padding-top: 2rem !important; }}
    
    /* Garantir que a logo não tenha arredondamento */
    [data-testid="stImage"] img {{ 
        border-radius: 0px !important; 
        object-fit: contain;
    }}
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
        st.markdown('<p class="main-title">Saúde Financeira</p>', unsafe_allow_html=True)
        clis = listar_clientes()
        c_sel = st.selectbox("Selecione o Cliente", [""] + list(clis.keys()), key=f"dash_cli_{ver}")
        
        if c_sel:
            obs_dict = listar_obras_por_cliente(clis[c_sel])
            if obs_dict:
                o_sel = st.selectbox("Selecione a Obra", [""] + list(obs_dict.keys()), key=f"dash_obra_{ver}")
                if o_sel:
                    obra_info = obs_dict[o_sel]
                    res_s = supabase.rpc('get_gastos_por_categoria', {'p_obra_id': obra_info['id']}).execute()
                    g_total = sum(float(i['total']) for i in res_s.data) if res_s.data else 0
                    orc = float(obra_info.get('orcamento_previsto', 0))
                    p_luc = float(obra_info.get('lucro_estimado', 0) or 0)
                    p_imp = float(obra_info.get('impostos_estimados', 0) or 0)
                    
                    v_luc_p = orc * (p_luc / 100)
                    v_imp = orc * (p_imp / 100)
                    l_real = orc - g_total - v_imp
                    
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.markdown(f'<div class="metric-container"><p class="metric-label">Orçado</p><p class="metric-value">{formatar_real(orc)}</p></div>', unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="metric-container"><p class="metric-label">Lucro Prev ({p_luc}%)</p><p class="metric-value">{formatar_real(v_luc_p)}</p></div>', unsafe_allow_html=True)
                    with c3: st.markdown(f'<div class="metric-container"><p class="metric-label">Imposto ({p_imp}%)</p><p class="metric-value">{formatar_real(v_imp)}</p></div>', unsafe_allow_html=True)
                    with c4: st.markdown(f'<div class="metric-container"><p class="metric-label">Lucro Real</p><p class="metric-value" style="color:{"#00FF00" if l_real > 0 else "#FF0000"}">{formatar_real(l_real)}</p></div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="data-card"><small>Gasto Acumulado (Realizado)</small><h3>{formatar_real(g_total)}</h3></div>', unsafe_allow_html=True)
                    if orc > 0: st.progress(min(g_total / orc, 1.0))
                    if res_s.data: st.bar_chart(pd.DataFrame(res_s.data).set_index('nome_categoria'))

    elif pag == 'GASTO':
        st.markdown("### Lançamento de Gasto")
        clis = listar_clientes()
        cats, forns = listar_categorias(), listar_fornecedores()
        with st.container(border=True):
            c_sel = st.selectbox("Cliente*", [""] + list(clis.keys()), key=f"g_cli_{ver}")
            o_sel = ""
            if c_sel:
                obs_dict = listar_obras_por_cliente(clis[c_sel])
                o_sel = st.selectbox("Obra*", [""] + list(obs_dict.keys()), key=f"g_obra_{ver}")
            
            cat_sel = st.selectbox("Categoria*", [""] + list(cats.keys()), key=f"gc_{ver}")
            f_sel = st.selectbox("Fornecedor*", [""] + list(forns.keys()), key=f"gf_{ver}")
            desc = st.text_input("Descrição", key=f"gd_{ver}")
            val = st.number_input("Valor", min_value=0.0, key=f"gv_{ver}")
            status_p = st.selectbox("Status de Pagamento", ["Pago", "Pendente"], key=f"gs_{ver}")
            foto = st.camera_input("Recibo/Comprovante", key=f"gp_{ver}")
            
            if st.button("SALVAR GASTO", use_container_width=True, type="primary"):
                if c_sel and o_sel and cat_sel and f_sel and val > 0:
                    try:
                        url = None
                        if foto:
                            n_arq = f"{uuid.uuid4()}.jpg"
                            supabase.storage.from_("comprovantes").upload(n_arq, foto.getvalue())
                            url = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{n_arq}"
                        supabase.table("lancamentos_obra").insert({
                            "obra_id": obs_dict[o_sel]['id'], 
                            "categoria_id": cats[cat_sel], 
                            "fornecedor_id": forns[f_sel], 
                            "descricao": desc, 
                            "valor": val, 
                            "url_comprovante": url, 
                            "status_pagamento": status_p
                        }).execute()
                        st.success("Gasto registrado com sucesso!"); limpar_campos(); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

    elif pag == 'CLIE':
        st.markdown("### Gestão de Clientes")
        dc = {"nome_cliente": "", "representante": "", "telefone": "", "whatsapp": "", "email": "", "cnpj": "", "endereco": ""}
        if st.session_state.clie_edit_id:
            res = supabase.table("clientes").select("*").eq("id", st.session_state.clie_edit_id).single().execute()
            if res.data: dc = res.data
        with st.container(border=True):
            cn = st.text_input("Nome/Razão Social*", value=dc["nome_cliente"], key=f"cn_{ver}")
            cr = st.text_input("Representante/Contato", value=dc["representante"], key=f"cr_{ver}")
            c_tel = st.text_input("Telefone Fixo", value=dc["telefone"], key=f"ct_{ver}")
            c_zap = st.text_input("WhatsApp*", value=dc["whatsapp"], key=f"cz_{ver}")
            c_mail = st.text_input("E-mail*", value=dc["email"], key=f"cm_{ver}")
            cc = st.text_input("CNPJ/CPF", value=dc["cnpj"], key=f"cc_{ver}")
            ce = st.text_input("Endereço Completo", value=dc["endereco"], key=f"ce_{ver}")
            
            if st.button("SALVAR CLIENTE", use_container_width=True, type="primary"):
                p = {
                    "nome_cliente": cn, "representante": cr, 
                    "telefone": aplicar_mask_tel(c_tel), "whatsapp": aplicar_mask_tel(c_zap), 
                    "email": c_mail, "cnpj": aplicar_mask_cnpj(cc), "endereco": ce
                }
                if st.session_state.clie_edit_id: supabase.table("clientes").update(p).eq("id", st.session_state.clie_edit_id).execute()
                else: supabase.table("clientes").insert(p).execute()
                st.success("Cliente salvo!"); limpar_campos(); st.rerun()

        for c in (supabase.table("clientes").select("*").order("nome_cliente").execute().data or []):
            with st.expander(f"👤 {c['nome_cliente']}"):
                st.write(f"**WhatsApp:** {c.get('whatsapp')} | **E-mail:** {c.get('email')}")
                st.write(f"**Endereço:** {c.get('endereco')}")
                b1, b2 = st.columns(2)
                if b1.button("Editar", key=f"ec_{c['id']}"): st.session_state.clie_edit_id=c['id']; st.rerun()
                if b2.button("Excluir", key=f"dc_{c['id']}"): supabase.table("clientes").delete().eq("id", c['id']).execute(); st.rerun()

    elif pag == 'FORN':
        st.markdown("### Gestão de Fornecedores")
        df_f = {"nome_fornecedor": "", "representante": "", "telefone": "", "email": ""}
        if st.session_state.forn_edit_id:
            res = supabase.table("fornecedores").select("*").eq("id", st.session_state.forn_edit_id).single().execute()
            if res.data: df_f = res.data
        with st.container(border=True):
            fn = st.text_input("Empresa/Nome*", value=df_f["nome_fornecedor"], key=f"fn_{ver}")
            fr = st.text_input("Contato/Vendedor", value=df_f["representante"], key=f"fr_{ver}")
            ft = st.text_input("Telefone/WhatsApp", value=df_f["telefone"], key=f"ft_{ver}")
            fm = st.text_input("E-mail para Pedidos", value=df_f["email"], key=f"fm_{ver}")
            
            if st.button("SALVAR FORNECEDOR", use_container_width=True, type="primary"):
                p = {"nome_fornecedor": fn, "representante": fr, "telefone": aplicar_mask_tel(ft), "email": fm}
                if st.session_state.forn_edit_id: supabase.table("fornecedores").update(p).eq("id", st.session_state.forn_edit_id).execute()
                else: supabase.table("fornecedores").insert(p).execute()
                st.success("Fornecedor salvo!"); limpar_campos(); st.rerun()
        
        for f in (supabase.table("fornecedores").select("*").order("nome_fornecedor").execute().data or []):
            with st.expander(f"🤝 {f['nome_fornecedor']}"):
                st.write(f"**Contato:** {f.get('representante')} | **Tel:** {f.get('telefone')}")
                st.write(f"**E-mail:** {f.get('email')}")
                b1, b2 = st.columns(2)
                if b1.button("Editar", key=f"ef_{f['id']}"): st.session_state.forn_edit_id=f['id']; st.rerun()
                if b2.button("Excluir", key=f"df_{f['id']}"): supabase.table("fornecedores").delete().eq("id", f['id']).execute(); st.rerun()

    elif pag == 'OBRA' and perf == 'ADMIN':
        st.markdown("### Gestão de Obras")
        do = {"nome_obra": "", "cliente_id": "", "orcamento_previsto": 0.0, "lucro_estimado": 0.0, "impostos_estimados": 0.0, "local_obra": ""}
        if st.session_state.obra_edit_id:
            res = supabase.table("obras").select("*").eq("id", st.session_state.obra_edit_id).single().execute()
            if res.data: do = res.data
        
        clis = listar_clientes()
        with st.container(border=True):
            on = st.text_input("Nome da Obra*", value=do["nome_obra"], key=f"on_{ver}")
            id_to_name = {v: k for k, v in clis.items()}
            idx_cli = ([""] + list(clis.keys())).index(id_to_name.get(do["cliente_id"], "")) if do["cliente_id"] in id_to_name else 0
            oc = st.selectbox("Cliente*", [""] + list(clis.keys()), index=idx_cli, key=f"oc_{ver}")
            ol = st.text_input("Localização da Obra*", value=do.get("local_obra", ""), key=f"ol_{ver}")
            ov = st.number_input("Orçamento Total (R$)", min_value=0.0, value=float(do["orcamento_previsto"]), key=f"ov_{ver}")
            
            c_luc, c_imp = st.columns(2)
            olucro = c_luc.number_input("Lucro Previsto (%)", min_value=0.0, value=float(do.get("lucro_estimado", 0) or 0))
            oimposto = c_imp.number_input("Imposto Estimado (%)", min_value=0.0, value=float(do.get("impostos_estimados", 0) or 0))
            
            if st.button("SALVAR OBRA", type="primary", use_container_width=True):
                if on and oc:
                    p = {
                        "nome_obra": on, "cliente_id": clis[oc], "orcamento_previsto": float(ov),
                        "lucro_estimado": float(olucro), "impostos_estimados": float(oimposto),
                        "local_obra": ol
                    }
                    if st.session_state.obra_edit_id: supabase.table("obras").update(p).eq("id", st.session_state.obra_edit_id).execute()
                    else: supabase.table("obras").insert(p).execute()
                    st.success("Obra salva!"); limpar_campos(); st.rerun()

        for ob in (supabase.table("obras").select("*").execute().data or []):
            with st.expander(f"🏗️ {ob['nome_obra']}"):
                st.write(f"**Local:** {ob.get('local_obra')}")
                b1, b2 = st.columns(2)
                if b1.button("Editar Obra", key=f"eob_{ob['id']}"): st.session_state.obra_edit_id=ob['id']; st.rerun()
                if b2.button("Excluir Obra", key=f"dob_{ob['id']}"):
                    supabase.table("lancamentos_obra").delete().eq("obra_id", ob['id']).execute()
                    supabase.table("obras").delete().eq("id", ob['id']).execute(); st.rerun()

    elif pag == 'LISTA':
        st.markdown("### Histórico de Lançamentos")
        clis = listar_clientes()
        c_sel = st.selectbox("Filtrar por Cliente:", [""] + list(clis.keys()), key=f"l_cli_{ver}")
        if c_sel:
            obs = listar_obras_por_cliente(clis[c_sel])
            o_f = st.selectbox("Selecione a Obra:", [""] + list(obs.keys()), key=f"lo_{ver}")
            if o_f:
                dados = supabase.table("lancamentos_obra").select("*, categorias_obra(nome_categoria), fornecedores(nome_fornecedor)").eq("obra_id", obs[o_f]['id']).order("created_at", desc=True).execute().data
                if dados:
                    df_d = pd.DataFrame(dados)
                    c1, c2 = st.columns(2)
                    c1.download_button("📥 PDF", gerar_pdf(df_d, o_f), f"Relatorio_{o_f}.pdf", use_container_width=True)
                    c2.download_button("📊 Excel", gerar_excel(df_d), f"Relatorio_{o_f}.xlsx", use_container_width=True)
                    for g in dados:
                        cor = "🟢" if g.get('status_pagamento') == "Pago" else "🔴"
                        with st.expander(f"{cor} {g['descricao']} | {formatar_real(g['valor'])}"):
                            if g.get('url_comprovante'): st.image(g['url_comprovante'])
                            st.write(f"**Fornecedor:** {g['fornecedores']['nome_fornecedor']}")
                            if st.button("Excluir Gasto", key=f"dg_{g['id']}"):
                                supabase.table("lancamentos_obra").delete().eq("id", g['id']).execute(); st.rerun()

    elif pag == 'USUARIOS' and perf == 'ADMIN':
        st.markdown("### Gestão de Equipe")
        with st.container(border=True):
            ne = st.text_input("E-mail do Novo Usuário", key=f"ue_{ver}")
            ns = st.text_input("Senha Temporária", type="password", key=f"us_{ver}")
            np = st.selectbox("Perfil de Acesso", ["LANCADOR", "ADMIN"], key=f"up_{ver}")
            if st.button("CRIAR USUÁRIO", use_container_width=True, type="primary"):
                if ne and ns:
                    supabase.table("usuarios").insert({"email": ne, "senha": ns, "perfil": np}).execute()
                    st.success("Usuário criado com sucesso!"); limpar_campos(); st.rerun()
        u_list = supabase.table("usuarios").select("id, email, perfil").execute().data
        if u_list: st.table(pd.DataFrame(u_list))
