import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Configurações do Supabase
SUPABASE_URL = "https://rdzgzvyxlaszygxchzlp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJkemd6dnl4bGFzenlneGNoemxwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3ODg0MzEsImV4cCI6MjA4NTM2NDQzMX0.NBQvzCzMYvUkxFQNR06gOK9otavlDKh3b9U4se5mEBA"  # Recomendo manter em segredo!
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Gestão Financeira", layout="centered")

# --- INICIALIZAÇÃO DO ESTADO (Previne erros de atributo) ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'name' not in st.session_state:
    st.session_state.name = None

# --- FUNÇÕES DE BANCO ---


def usuario_existe(user_id):
    res = supabase.table("users_plataform").select(
        "user_id").eq("user_id", user_id).execute()
    return len(res.data) > 0


def cadastrar_usuario(nome, celular, login, senha):
    dados = {"name": nome, "user_id": celular,
             "login": login, "password": senha}
    try:
        supabase.table("users_plataform").insert(dados).execute()
        return True, "✅ Cadastro realizado com sucesso! Faça o login."
    except Exception as e:
        return False, f"Erro: {str(e)}"


def verificar_login(login, senha):
    res = supabase.table("users_plataform").select(
        "*").eq("login", login).eq("password", senha).execute()
    return res.data[0] if len(res.data) > 0 else None


# --- INTERFACE DE ACESSO ---
if not st.session_state.logado:
    aba = st.tabs(["Login", "Criar Conta"])

    with aba[0]:
        st.header("Entrar")
        login_user = st.text_input("Login (ou Celular)")
        senha_user = st.text_input("Senha", type="password")

        if st.button("Acessar Sistema"):
            user = verificar_login(login_user, senha_user)
            if user:
                st.session_state.logado = True
                st.session_state.user_id = user['user_id']
                st.session_state.name = user['name']
                st.rerun()
            else:
                st.error("Login ou senha incorretos.")

    with aba[1]:
        st.header("Novo Cadastro")
        novo_nome = st.text_input("Nome Completo")
        novo_celular = st.text_input("Celular (Ex: 5573991770000)")
        novo_login = st.text_input("Crie um Nome de Usuário")
        nova_senha = st.text_input("Crie uma Senha", type="password")

        if st.button("Finalizar Cadastro"):
            if novo_nome and novo_celular and nova_senha:
                sucesso, msg = cadastrar_usuario(
                    novo_nome, novo_celular, novo_login, nova_senha)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.warning("Preencha todos os campos obrigatórios.")

# --- DASHBOARD (SÓ EXECUTA SE ESTIVER LOGADO) ---
else:
    st.sidebar.write(f"Bem-vindo, **{st.session_state.name}**")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.session_state.user_id = None
        st.rerun()

    # --- TRATAMENTO DO ID ---
    user_id_bruto = str(st.session_state.user_id).strip()

    # Lógica do 9º dígito (Brasil: 13 caracteres -> 12 caracteres)
    if len(user_id_bruto) == 13 and user_id_bruto.startswith("55"):
        user_id_consulta = user_id_bruto[:4] + user_id_bruto[5:]
    else:
        user_id_consulta = user_id_bruto

    # --- BUSCA DE DADOS ---
    res_financeiro = supabase.table("balanco").select(
        "*").eq("user_id", user_id_consulta).execute()
    df = pd.DataFrame(res_financeiro.data)

    st.title(f"📊 Dashboard de {st.session_state.name}")

    if df.empty:
        st.warning(f"Nenhum dado encontrado para o ID: {user_id_consulta}")
        st.info("Envie seus gastos pelo WhatsApp para atualizar esta página.")
    else:
        # Tratamento de dados
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
        df = df.dropna(subset=['data'])
        df['mes_ano'] = df['data'].dt.strftime('%m/%Y')

        # Filtros laterais
        st.sidebar.divider()
        meses_disponiveis = sorted(df['mes_ano'].unique(), reverse=True)
        mes_filtro = st.sidebar.multiselect(
            "Filtrar Meses:", meses_disponiveis, default=meses_disponiveis)

        df_filtrado = df[df['mes_ano'].isin(mes_filtro)]

        # --- MÉTRICAS ---
        col1, col2, col3 = st.columns(3)
        entradas = df_filtrado[df_filtrado['tipo'].str.contains(
            'entrada', case=False, na=False)]['valor'].sum()
        saidas = df_filtrado[df_filtrado['tipo'].str.contains(
            'saída|saida', case=False, na=False)]['valor'].sum()
        saldo = entradas - saidas

        col1.metric("Ganhos", f"R$ {entradas:,.2f}")
        col2.metric("Gastos", f"R$ {saidas:,.2f}", delta_color="inverse")
        col3.metric("Saldo", f"R$ {saldo:,.2f}")

        # --- GRÁFICOS ---
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.write("**💰 Gastos por Categoria**")
            gastos_cat = df_filtrado[df_filtrado['tipo'].str.contains(
                'saída|saida', case=False, na=False)].groupby('categoria')['valor'].sum()
            if not gastos_cat.empty:
                st.bar_chart(gastos_cat)
        with c2:
            st.write("**📈 Evolução Diária**")
            evolucao = df_filtrado.groupby(df_filtrado['data'].dt.date)[
                'valor'].sum()
            st.line_chart(evolucao)

        # --- TABELA ---
        st.divider()
        st.subheader("📝 Histórico Detalhado")
        df_display = df_filtrado[['data', 'item',
                                  'categoria', 'tipo', 'valor']].copy()
        df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display.sort_values(by='data', ascending=False),
                     use_container_width=True, hide_index=True)
