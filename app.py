
import streamlit as st
from auth import init_db, authenticate, create_user, list_users, delete_user, change_password, set_meta, get_meta, list_metas
import pandas as pd, io, os
from calculo import calcular_gratificacao
from pdfgen import generate_pdf_report
from emailer import send_email

init_db()
st.set_page_config(page_title='Sistema Gratificacoes', layout='wide')

def login_form():
    st.sidebar.title('Login')
    username = st.sidebar.text_input('Usuário')
    password = st.sidebar.text_input('Senha', type='password')
    if st.sidebar.button('Entrar'):
        ok, user = authenticate(username.strip(), password)
        if ok:
            st.session_state['user'] = user
            st.experimental_rerun()
        else:
            st.sidebar.error('Usuário ou senha inválidos.')

def logout():
    if 'user' in st.session_state: del st.session_state['user']
    st.experimental_rerun()

def require_login():
    if 'user' not in st.session_state:
        login_form()
        st.stop()

if 'user' not in st.session_state:
    login_form()

require_login()
user = st.session_state['user']

st.sidebar.write(f"Logado como: {user.get('username')} ({user.get('role')})")
if st.sidebar.button('Logout'):
    logout()

if user.get('role') == 'ADMIN':
    st.sidebar.markdown('---')
    if st.sidebar.button('Admin'):
        st.experimental_set_query_params(page='admin')

page = st.experimental_get_query_params().get('page', ['main'])[0]

if page == 'admin' and user.get('role') == 'ADMIN':
    st.header('Painel Admin - Configurações e Usuários')
    st.subheader('Criar usuário')
    with st.form('create'):
        uname = st.text_input('Usuário')
        pwd = st.text_input('Senha', type='password', value='changeme')
        role = st.selectbox('Papel', ['USER','ADMIN','FINANCEIRO'])
        fullname = st.text_input('Nome completo')
        email = st.text_input('Email')
        if st.form_submit_button('Criar'):
            ok, err = create_user(uname, pwd, role, fullname, email)
            if ok: st.success('Usuário criado'); st.experimental_rerun()
            else: st.error('Erro: '+str(err))
    st.subheader('Metas por Vendedor')
    with st.form('metas'):
        vend = st.text_input('Vendedor (nome)')
        mm = st.number_input('Meta mínima', min_value=0.0, value=0.0, step=100.0)
        m100 = st.number_input('Meta 100%', min_value=0.0, value=10000.0, step=100.0)
        grat = st.number_input('Gratificação ao atingir 100%', min_value=0.0, value=500.0, step=1.0)
        bonus = st.number_input('Bônus % sobre excedente (ex: 0.10 = 10%)', min_value=0.0, value=0.10, step=0.01, format='%f')
        if st.form_submit_button('Salvar Meta'):
            set_meta(vend, mm if mm>0 else None, m100 if m100>0 else None, grat if grat>0 else None, bonus if bonus>0 else None)
            st.success('Meta salva')
    st.subheader('Lista de metas')
    metas = list_metas()
    st.table(metas)
    st.subheader('Usuários')
    users = list_users()
    st.table(pd.DataFrame(users))
    st.markdown('Apagar usuário')
    delu = st.text_input('Usuário para apagar')
    if st.button('Apagar'):
        if delu == 'admin': st.error('Não é possível apagar admin')
        else:
            delete_user(delu); st.success('Usuário apagado'); st.experimental_rerun()
else:
    st.header('Painel de Cálculos - Upload')
    uploaded = st.file_uploader('Envie planilha Excel com vendas (aba com colunas: VENDEDOR, VALOR DE VENDA)', type=['xlsx','xls'])
    df = None
    if uploaded:
        try:
            x = pd.read_excel(uploaded, sheet_name=0)
            st.success('Arquivo carregado. Usando primeira aba: '+str(x.shape))
            st.dataframe(x.head(50))
            # Normalize column names to expected names
            cols = {c.strip().upper():c for c in x.columns}
            # find seller and value cols
            seller_col = None; value_col = None
            for k,v in cols.items():
                if 'VENDEDOR' in k: seller_col = v
                if 'VALOR' in k and 'VENDA' in k: value_col = v
            if seller_col is None or value_col is None:
                st.error('Não foi possível identificar colunas VENDEDOR e VALOR DE VENDA automaticamente. Renomeie e reenvie.')
            else:
                rows = []
                total_pagos = 0.0
                for _, r in x.iterrows():
                    vendedor = str(r.get(seller_col)).strip()
                    vendas = r.get(value_col)
                    try:
                        vendas = float(vendas)
                    except:
                        vendas = None
                    meta = get_meta(vendedor)
                    if meta:
                        meta_min = meta.get('meta_min') or 0.0
                        meta_100 = meta.get('meta_100') or 0.0
                        grat_100 = meta.get('gratificacao_100') or 0.0
                        bonus_pct = meta.get('bonus_pct') or 0.0
                    else:
                        # fallback defaults from env or constants
                        meta_min = 0.0; meta_100 = 100000.0; grat_100 = 500.0; bonus_pct = 0.10
                    res = calcular_gratificacao(vendas, meta_min, meta_100, grat_100, bonus_pct)
                    rows.append({'vendedor':vendedor,'vendas':vendas or 0.0,'meta_100':meta_100,'atingimento':res['atingimento'],'grat_base':res['grat_base'],'bonus':res['bonus'],'total':res['total']})
                    total_pagos += res['total']
                st.subheader('Resultados calculados')
                st.dataframe(pd.DataFrame(rows))
                st.markdown('---')
                st.subheader('Gerar PDF e enviar por email')
                if st.button('Gerar PDF de exemplo (local)'):
                    out = 'relatorio_exemplo.pdf'
                    generate_pdf_report(out, 'Relatório de Gratificações', rows, totals=round(total_pagos,2), footer_text='Relatório gerado pelo sistema.')
                    with open(out,'rb') as f:
                        st.download_button('Download PDF', f, file_name=out, mime='application/pdf')
                st.markdown('Enviar por e-mail (usar variáveis de ambiente no deploy para SMTP)')
                smtp_host = st.text_input('SMTP Host (teste)', value=os.environ.get('SMTP_HOST',''))
                smtp_port = st.text_input('SMTP Port', value=os.environ.get('SMTP_PORT','587'))
                smtp_user = st.text_input('SMTP User', value=os.environ.get('SMTP_USER',''))
                smtp_pass = st.text_input('SMTP Pass', value=os.environ.get('SMTP_PASS',''), type='password')
                sender = st.text_input('From (ex: Relatorios <rel@empresa.com>)', value=os.environ.get('EMAIL_FROM','no-reply@example.com'))
                recipients = st.text_area('Destinatários (vírgula separado)', value=os.environ.get('RECIPIENTS','gestor@empresa.com'))
                if st.button('Gerar PDF e Enviar por Email'):
                    out = 'relatorio_envio.pdf'
                    generate_pdf_report(out, 'Relatório de Gratificações', rows, totals=round(total_pagos,2), footer_text='Relatório gerado pelo sistema.')
                    try:
                        send_email(smtp_host, smtp_port, smtp_user, smtp_pass, sender, [r.strip() for r in recipients.split(',')], 'Relatório de Gratificações', 'Segue em anexo', out)
                        st.success('E-mail enviado com sucesso (se credenciais estiverem corretas).')
                    except Exception as e:
                        st.error('Erro ao enviar e-mail: '+str(e))
        except Exception as e:
            st.error('Erro ao processar arquivo: '+str(e))
