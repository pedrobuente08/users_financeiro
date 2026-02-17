import streamlit as st
from supabase import create_client, Client
import pandas as pd

st.set_page_config(page_title="Gestão Financeira", layout="centered")

# SUPABASE_URL = "https://rdzgzvyxlaszygxchzlp.supabase.co"
# SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJkemd6dnl4bGFzenlneGNoemxwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3ODg0MzEsImV4cCI6MjA4NTM2NDQzMX0.NBQvzCzMYvUkxFQNR06gOK9otavlDKh3b9U4se5mEBA"
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv(
    "SUPABASE_ANON_KEY") or st.secrets.get("SUPABASE_ANON_KEY")


supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


# -------------------------------
# Util
# -------------------------------

def get_user_from_token(token: str):
    try:
        res = supabase.auth.get_user(token)
        return res.user
    except Exception:
        return None


# -------------------------------
# Sessão
# -------------------------------

if "user" not in st.session_state:
    st.session_state.user = None

if "profile" not in st.session_state:
    st.session_state.profile = None

if "token" not in st.session_state:
    st.session_state.token = None


# -------------------------------
# Lê token da URL
# -------------------------------

query_params = st.query_params
token = query_params.get("token", None)


# -------------------------------
# Autenticação
# -------------------------------

if st.session_state.user is None:

    if not token:
        st.markdown(
            '<meta http-equiv="refresh" content="0; url=http://localhost:3000">', unsafe_allow_html=True)
        st.stop()

    user = get_user_from_token(token)

    if not user:
        st.markdown(
            '<meta http-equiv="refresh" content="0; url=http://localhost:3000">', unsafe_allow_html=True)
        st.stop()

    # autentica o cliente com o JWT do usuário para respeitar o RLS
    supabase.postgrest.auth(token)

    # carrega perfil
    profile = (
        supabase
        .table("users_plataform")
        .select("*")
        .eq("auth_user_id", user.id)
        .maybe_single()
        .execute()
    )

    if not profile or not profile.data:
        st.title("Complete seu cadastro")
        st.write("Precisamos de mais alguns dados para liberar o dashboard.")

        with st.form("form_perfil"):
            nome = st.text_input("Nome completo")
            telefone = st.text_input("Telefone (ex: 5511999999999)")
            submitted = st.form_submit_button("Salvar e continuar")

        if submitted:
            digits = ''.join(filter(str.isdigit, telefone))
            if not nome.strip() or not telefone.strip():
                st.error("Preencha todos os campos.")
            elif len(digits) != 13:
                st.error(
                    "Telefone inválido. Use 13 dígitos: código do país (55) + DDD + número. Ex: 5511999999999")
            else:
                supabase.table("users_plataform").insert({
                    "auth_user_id": user.id,
                    "name": nome.strip(),
                    "phone": digits,
                }).execute()
                st.success("Perfil criado! Recarregando...")
                st.rerun()

        st.stop()

    # só salva na sessão se tudo deu certo
    st.session_state.user = user
    st.session_state.profile = profile.data
    st.session_state.token = token


# -------------------------------
# DASHBOARD
# -------------------------------

user = st.session_state.user
profile = st.session_state.profile
token = st.session_state.token

if user is None or profile is None or token is None:
    st.markdown('<meta http-equiv="refresh" content="0; url=http://localhost:3000">',
                unsafe_allow_html=True)
    st.stop()

# garante JWT nas queries do dashboard
supabase.postgrest.auth(token)

st.sidebar.write(f"Bem-vindo, **{profile['name']}**")

if st.sidebar.button("Sair"):
    st.session_state.user = None
    st.session_state.profile = None
    st.query_params.clear()
    st.rerun()


st.title(f"📊 Dashboard de {profile['name']}")

phone = profile["phone"]

# normaliza: gera os dois formatos possíveis (com e sem o 9 extra após o DDD)
# Exemplo: 5573991775430 (13 dígitos) ↔ 557391775430 (12 dígitos)


def phone_variants(p: str) -> list:
    p = p.strip()
    variants = [p]
    if len(p) == 13 and p[4] == '9':    # tem o 9 extra → gera sem ele
        variants.append(p[:4] + p[5:])
    elif len(p) == 12:                   # sem o 9 extra → gera com ele
        variants.append(p[:4] + '9' + p[4:])
    return variants


# -------------------------------
# BUSCA FINANCEIRO
# -------------------------------

res = (
    supabase
    .table("balanco")
    .select("*")
    .in_("user_id", phone_variants(phone))
    .execute()
)

df = pd.DataFrame(res.data)

if df.empty:
    st.warning("Nenhum dado financeiro encontrado.")
    st.stop()


# -------------------------------
# Tratamento
# -------------------------------

df["data"] = pd.to_datetime(df["data"], errors="coerce")
df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)

df = df.dropna(subset=["data"])
df["mes_ano"] = df["data"].dt.strftime("%m/%Y")


# -------------------------------
# Filtros
# -------------------------------

st.sidebar.divider()

meses = sorted(df["mes_ano"].unique(), reverse=True)

mes_filtro = st.sidebar.multiselect(
    "Filtrar meses",
    meses,
    default=meses
)

df = df[df["mes_ano"].isin(mes_filtro)]


# -------------------------------
# Métricas
# -------------------------------

col1, col2, col3 = st.columns(3)

entradas = df[df["tipo"].str.contains(
    "entrada", case=False, na=False)]["valor"].sum()
saidas = df[df["tipo"].str.contains(
    "saída|saida", case=False, na=False)]["valor"].sum()

saldo = entradas - saidas

col1.metric("Ganhos", f"R$ {entradas:,.2f}")
col2.metric("Gastos", f"R$ {saidas:,.2f}", delta_color="inverse")
col3.metric("Saldo", f"R$ {saldo:,.2f}")


# -------------------------------
# Gráficos
# -------------------------------

st.divider()

c1, c2 = st.columns(2)

with c1:
    st.write("💰 Gastos por categoria")
    gastos_cat = (
        df[df["tipo"].str.contains("saída|saida", case=False, na=False)]
        .groupby("categoria")["valor"]
        .sum()
    )

    if not gastos_cat.empty:
        st.bar_chart(gastos_cat)

with c2:
    st.write("📈 Evolução diária")
    evolucao = df.groupby(df["data"].dt.date)["valor"].sum()
    st.line_chart(evolucao)


# -------------------------------
# Tabela
# -------------------------------

st.divider()
st.subheader("Histórico")

df_view = df[["data", "item", "categoria", "tipo", "valor"]].copy()
df_view["data"] = df_view["data"].dt.strftime("%d/%m/%Y")

st.dataframe(
    df_view.sort_values(by="data", ascending=False),
    use_container_width=True,
    hide_index=True
)
