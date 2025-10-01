# app.py — Sistema de Gratificações (Streamlit) — Versão corrigida
import streamlit as st
import pandas as pd
import os
from auth import init_db, authenticate, create_user, list_users, delete_user, change_password, set_meta, get_meta, list_metas
from calculo import calcular_gratificacao
from pdfgen import generate_pdf_report
from emailer import send_email

# Inicializa DB (cria admin/admin se necessário)
init_db()

st.set_page_config(page_title="Sistema de Gratificações", layout="wide")

# ----------------------
# Helper functions
# ----------------------
def ensure_session_state():
    if 'auth_checked' not in st.session_state:
        st.session_state['auth_checked'] = True
    # keep 'user' as stored user dict after login

def login_sidebar():
    """Renderiza o formulário de login na sidebar — com keys únicos para evitar duplicidade."""
    st.sidebar.title("🔐 Autenticação")
    # If user already logged in, show status and logout
    if 'user' in st.session_state:
        u = st.session_state['user']
        st.sidebar.markdown(f"**Logado como:** {u.get('username')} — `{u.get('role')}`")
        if st.sidebar.button("Logout", key="btn_logout"):
            del st.session_state['user']
            st.experimental_rerun()
        return

    # Login form inputs (unique keys)
    username = st.sidebar.text_input("Usuário", key="login_username")
    password = st.sidebar.text_input("Senha", type="password", key="login_password")
    if st.sidebar.button("Entrar", key="login_button"):
        ok, user = authenticate(username.strip(), password)
        if ok:
            st.session_state['user'] = user
            st.sidebar.success(f"Bem-vindo(a), {user.get('fullname') or user.get('username')}!")
            st.experimental_rerun()
        else:
            st.sidebar.error("Usuário ou senha inválidos")

def require_login_or_stop():
    """Se não estiver logado, bloqueia o app mostrando apenas o login na sidebar."""
    if 'user' not in st.session_state:
        st.info("Por favor, faça login usando o painel lateral para acessar o sistema.")
        # Render login controls
        login_sidebar()
        st.stop()

# ----------------------
# Main UI
# ----------------------
ensure_session_state()
login_sidebar()
require_login_or_stop()

user = st.session_state['user']

# Show a small header and summary
st.title("📊 Sistema de Gratificações - Painel")
st.markdown(f"Usuário autenticado: **{user.get('username')}** — Papel: **{user.get('role')}**")

# Admin quick link in sidebar
if user.get('role') == 'ADMIN':
    st.sidebar.markdown("---")
    if st.sidebar.button("Ir para Painel Admin", key="btn_goto_admin"):
        st.experimental_set_query_params(page='admin')

# Determine current page
page = st.experimental_get_query_params().get('page', ['main'])[0]

# ----------------------
# Admin Page
# ----------------------
if page == 'admin' and user.get('role') == 'ADMIN':
    st.header("🔧 Painel de Administração")
    st.write("Aqui você pode criar/excluir usuários e gerenciar metas por vendedor.")

    with st.expander("Criar novo usuário"):
        with st.form("form_create_user"):
            uname = st.text_input("Nome de usuário", key="create_user_username")
            fullname = st.text_input("Nome completo", key="create_user_fullname")
            email = st.text_input("Email", key="create_user_email")
            role = st.selectbox("Papel", ["USER", "ADMIN", "FINANCEIRO"], key="create_user_role")
            pwd = st.text_input("Senha inicial", value="changeme", type="password", key="create_user_password")
            submitted = st.form_submit_button("Criar usuário")
            if submitted:
                if not uname:
                    st.error("Informe um nome de usuário.")
                else:
                    ok, err = create_user(uname.strip(), pwd, role, fullname, email)
                    if ok:
                        st.success("Usuário criado com sucesso.")
                    else:
                        st.error(f"Erro ao criar usuário: {err}")

    st.markdown("---")
    st.subheader("Gerenciar Metas por Vendedor")
    with st.form("form_metas"):
        vend = st.text_input("Vendedor (nome)", key="meta_vendedor")
        meta_min = st.number_input("Meta mínima (R$)", min_value=0.0, value=0.0, step=100.0, key="meta_min")
        meta_100 = st.number_input("Meta 100% (R$)", min_value=0.0, value=10000.0, step=100.0, key="meta_100")
        grat100 = st.number_input("Gratificação ao atingir 100% (R$)", min_value=0.0, value=500.0, step=1.0, key="meta_grat100")
        bonus_pct = st.number_input("Bônus % sobre excedente (ex: 0.10 = 10%)", min_value=0.0, value=0.10, step=0.01, format="%f", key="meta_bonus")
        save_meta = st.form_submit_button("Salvar Meta")
        if save_meta:
            if not vend:
                st.error("Informe o nome do vendedor")
            else:
                set_meta(vend.strip(), meta_min if meta_min>0 else None, meta_100 if meta_100>0 else None, grat100 if grat100>0 else None, bonus_pct if bonus_pct>0 else None)
                st.success("Meta salva")

    st.markdown("---")
    st.subheader("Lista de Metas")
    metas = list_metas()
    if metas:
        st.dataframe(pd.DataFrame(metas))
    else:
        st.info("Nenhuma meta cadastrada ainda.")

    st.markdown("---")
    st.subheader("Gerenciar Usuários")
    users = list_users()
    st.dataframe(pd.DataFrame(users))

    st.write("Excluir usuário (não é possível excluir 'admin'):")
    del_user = st.text_input("Usuário para excluir", key="del_user_input")
    if st.button("Excluir usuário", key="btn_delete_user"):
        if del_user.strip() == 'admin':
            st.error("Não é permitido excluir usuário 'admin'")
        else:
            delete_user(del_user.strip())
            st.success("Usuário excluído (se existia).")
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Alterar senha de usuário")
    with st.form("form_change_pass"):
        user_cp = st.text_input("Usuário", key="chg_user")
        new_pass = st.text_input("Nova senha", type="password", key="chg_new_pass")
        if st.form_submit_button("Alterar senha"):
            if user_cp.strip():
                change_password(user_cp.strip(), new_pass)
                st.success("Senha alterada.")
            else:
                st.error("Informe o usuário.")

# ----------------------
# Main (non-admin) Page — Upload, cálculos, PDF, envio
# ----------------------
else:
    st.header("📥 Upload de Vendas e Cálculo de Gratificações")
    st.markdown("Faça upload da planilha (aba contendo colunas: `VENDEDOR`, `VALOR DE VENDA`)")

    uploaded = st.file_uploader("Escolha um arquivo .xlsx", type=['xlsx','xls'], key="upload_sales_file")
    if uploaded is not None:
        try:
            # read all sheets; use first sheet by default
            sheets = pd.read_excel(uploaded, sheet_name=None)
            first_sheet_name = list(sheets.keys())[0]
            df_raw = sheets[first_sheet_name].copy()

            st.success(f"Arquivo carregado — usando aba: `{first_sheet_name}`")
            st.dataframe(df_raw.head(50))

            # normalize column names to uppercase stripped
            col_map = {c.strip().upper(): c for c in df_raw.columns}
            seller_col = None
            value_col = None
            for k, v in col_map.items():
                if 'VENDEDOR' in k:
                    seller_col = v
                if 'VALOR' in k and 'VENDA' in k:
                    value_col = v

            if seller_col is None or value_col is None:
                st.error("Não foi possível identificar automaticamente as colunas 'VENDEDOR' e 'VALOR DE VENDA'. Renomeie-as e envie novamente.")
            else:
                # prepare rows for calculation
                results = []
                total_paid = 0.0
                for _, row in df_raw.iterrows():
                    vendedor = str(row.get(seller_col)).strip() if pd.notna(row.get(seller_col)) else ""
                    raw_vendas = row.get(value_col)
                    # normalize numeric values (handle strings with R$ etc)
                    vendas = None
                    try:
                        # if it's string like "R$ 1.234,56", try to clean
                        if isinstance(raw_vendas, str):
                            vstr = raw_vendas.replace("R$", "").replace(".", "").replace(",", ".").strip()
                            vendas = float(vstr) if vstr not in ["", "-"] else None
                        else:
                            vendas = float(raw_vendas) if pd.notna(raw_vendas) else None
                    except Exception:
                        vendas = None

                    meta = get_meta(vendedor) or {}
                    meta_min = meta.get('meta_min') if meta.get('meta_min') is not None else 0.0
                    meta_100 = meta.get('meta_100') if meta.get('meta_100') is not None else 0.0
                    grat100 = meta.get('gratificacao_100') if meta.get('gratificacao_100') is not None else 0.0
                    bonus_pct = meta.get('bonus_pct') if meta.get('bonus_pct') is not None else 0.0

                    calc = calcular_gratificacao(vendas, meta_min, meta_100, grat100, bonus_pct)
                    results.append({
                        'vendedor': vendedor or '(sem nome)',
                        'vendas': round(vendas,2) if vendas is not None else 0.0,
                        'meta_100': meta_100,
                        'atingimento': calc['atingimento'],
                        'grat_base': calc['grat_base'],
                        'bonus': calc['bonus'],
                        'total': calc['total']
                    })
                    total_paid += calc['total']

                df_results = pd.DataFrame(results)
                st.subheader("Resultados")
                st.dataframe(df_results)

                st.markdown("---")
                st.subheader("Gerar Relatório PDF")
                if st.button("Gerar PDF (download local)", key="btn_gen_pdf"):
                    out_file = "relatorio_gratificacoes.pdf"
                    generate_pdf_report(out_file, "Relatório de Gratificações", results, totals=round(total_paid,2), footer_text="Relatório gerado automaticamente.")
                    with open(out_file, "rb") as f:
                        st.download_button("Baixar PDF", f, file_name=out_file, mime="application/pdf", key="download_pdf")

                st.markdown("---")
                st.subheader("Enviar por E-mail (teste)")
                st.info("Para envio real, preencha as configurações SMTP nas variáveis de ambiente do deploy (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, RECIPIENTS).")
                smtp_host = st.text_input("SMTP Host (para teste)", value=os.environ.get("SMTP_HOST",""), key="smtp_host")
                smtp_port = st.text_input("SMTP Port", value=os.environ.get("SMTP_PORT","587"), key="smtp_port")
                smtp_user = st.text_input("SMTP User", value=os.environ.get("SMTP_USER",""), key="smtp_user")
                smtp_pass = st.text_input("SMTP Pass", value=os.environ.get("SMTP_PASS",""), type="password", key="smtp_pass")
                sender = st.text_input("From (ex: Relatorios <rel@empresa.com>)", value=os.environ.get("EMAIL_FROM","no-reply@example.com"), key="smtp_from")
                recipients = st.text_area("Destinatários (vírgula separado)", value=os.environ.get("RECIPIENTS","gestor@empresa.com"), key="smtp_recipients")
                if st.button("Gerar PDF e Enviar (teste)", key="btn_send_email"):
                    out_file = "relatorio_envio.pdf"
                    generate_pdf_report(out_file, "Relatório de Gratificações", results, totals=round(total_paid,2), footer_text="Relatório gerado automaticamente.")
                    try:
                        recips = [r.strip() for r in recipients.split(",") if r.strip()]
                        send_email(smtp_host, smtp_port, smtp_user, smtp_pass, sender, recips, "Relatório de Gratificações", "Segue em anexo o relatório.", out_file)
                        st.success("Email enviado (se credenciais estiverem corretas).")
                    except Exception as e:
                        st.error(f"Erro ao enviar email: {e}")

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")

# End of app.py
