import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import uuid

# --- CONEXÃO ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- INTERFACE E DESIGN ---
st.set_page_config(page_title="ROSECON Pro", layout="centered")

# (Funções de apoio e CSS omitidos para brevidade, mantendo os mesmos das versões anteriores)
# ... [Mesmo CSS e Funções de apoio das versões consolidadas] ...

# --- LÓGICA DE REGISTRO DE GASTO ---
if st.session_state.get('pagina') == 'GASTO':
    st.markdown("### 💸 Registrar Novo Gasto")
    # ... [Busca de obras e categorias] ...
    
    with st.container(border=True):
        # ... [Campos de preenchimento] ...
        foto = st.camera_input("Foto do Recibo")
        
        if st.button("FINALIZAR", use_container_width=True, type="primary"):
            url_f = None
            if foto:
                try:
                    f_name = f"{uuid.uuid4()}.jpg"
                    # Tentativa de upload
                    storage_res = supabase.storage.from_("comprovantes").upload(
                        path=f_name, 
                        file=foto.getvalue(),
                        file_options={"content-type": "image/jpeg"}
                    )
                    url_f = f"{SUPABASE_URL}/storage/v1/object/public/comprovantes/{f_name}"
                    st.toast("✅ Foto enviada com sucesso!")
                except Exception as e:
                    st.error(f"⚠️ Erro no Storage: {e}")
                    st.info("Dica: Verifique as 'Policies' do Bucket no Supabase.")
            
            # Salvamento no Banco
            try:
                supabase.table("lancamentos_obra").insert({
                    "obra_id": obras[o_sel], "categoria_id": cats[c_sel],
                    "descricao": desc, "valor": valor, "url_comprovante": url_f
                }).execute()
                st.success("Lançamento concluído no banco de dados!")
                st.session_state.pagina = 'RESUMO'; st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar dados: {e}")
