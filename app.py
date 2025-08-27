
import os
import re
import json
import pandas as pd
import streamlit as st

# ---- CONFIG ----
st.set_page_config(page_title="Ideator – Gerador de Ideias por Tendências", page_icon="💡", layout="wide")

# ---- LOAD TRENDS ----
@st.cache_data
def load_trends(csv_path):
    df = pd.read_csv(csv_path)
    # Normalizar colunas esperadas
    expected = ["trend_nome","descricao","porque_agora","oportunidades","exemplos"]
    for col in expected:
        if col not in df.columns:
            df[col] = ""
    # Drop linhas vazias de nome
    df = df[df["trend_nome"].notna() & (df["trend_nome"].astype(str).str.strip() != "")]
    return df[expected]

default_csv = "/mnt/data/tendencias_estruturadas.csv"
csv_file = st.file_uploader("📄 Suba sua base de tendências (CSV) ou use a padrão:", type=["csv"])
if csv_file:
    trends_df = load_trends(csv_file)
else:
    trends_df = load_trends(default_csv)

st.sidebar.header("⚙️ Configurações")
model_name = st.sidebar.text_input("Modelo LLM", value=os.environ.get("OPENAI_MODEL","gpt-4o-mini"))
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.4, 0.1)
max_tokens = st.sidebar.slider("Max tokens", 256, 4096, 1400, 64)

st.title("💡 Ideator – Gerador de Ideias por Tendências")
st.caption("Insira o briefing do cliente, selecione tendências (ou deixe o sistema sugerir) e gere ideias acionáveis com plano 30/60/90.")

# ---- BRIEF ----
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        segmento = st.text_input("Segmento", value="Saúde e bem-estar")
        metas = st.text_area("Metas (lista)", value="aumentar captação; diferenciação; retenção")
        restricoes = st.text_input("Restrições", value="baixo CAPEX; execução < 90 dias")
    with col2:
        publicos = st.text_input("Públicos", value="adultos 25–55")
        canais = st.text_input("Canais", value="clínica física; Instagram; WhatsApp")
        tom = st.text_input("Tom de marca", value="humano, prático")

    briefing = st.text_area("Briefing livre (opcional)", placeholder="Descreva o desafio do cliente em 2-5 linhas...")

# ---- TENDÊNCIAS ----
st.subheader("📚 Tendências disponíveis")
st.dataframe(trends_df, use_container_width=True)

st.markdown("---")
st.subheader("🎯 Seleção de Tendências")

all_trends = trends_df["trend_nome"].dropna().astype(str).tolist()
auto_select = st.checkbox("Selecionar tendências automaticamente com base no briefing", value=True)

def score_trend(row, text):
    text = text.lower()
    bag = " ".join([str(row.get(c,"")) for c in ["trend_nome","descricao","porque_agora","oportunidades","exemplos"]]).lower()
    # Pontue por interseção de palavras (heurística simples)
    words = set(re.findall(r"[\wÀ-ÿ']+", text))
    score = sum(1 for w in words if w in bag)
    # Bônus se o nome da tendência aparecer no texto
    score += 2 if str(row.get("trend_nome","")).lower() in text else 0
    return score

pre_selected = []
if auto_select:
    text = " ".join([segmento, metas, restricoes, publicos, canais, tom, briefing])
    scores = [(row["trend_nome"], score_trend(row, text)) for _, row in trends_df.iterrows()]
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    pre_selected = [name for name, s in scores[:6] if s > 0] or all_trends[:6]

chosen = st.multiselect("Escolha até 8 tendências (ou use a seleção automática)", options=all_trends, default=pre_selected, max_selections=8)

# ---- PROMPTING ----
system_prompt = """Você é um estrategista de inovação que gera ideias acionáveis a partir de tendências.
Use a biblioteca de tendências carregada (nome, descrição, por que agora, oportunidades, exemplos).
Para cada ideia, inclua:
- Nome curto e criativo
- Qual tendência(s) usa e por quê ("Por que agora?")
- Como funciona (passo a passo)
- Canal/custos aproximados/recursos
- Métrica de sucesso inicial
- Versão "light" (MVP 30 dias) e "pro" (90 dias)
Gere 10 ideias: 6 seguras, 3 ousadas, 1 moonshot. Ordene por impacto.
Finalize com um roadmap 30/60/90.
"""

def build_user_prompt():
    context_trends = trends_df[trends_df["trend_nome"].isin(chosen)].to_dict(orient="records")
    brief_json = {
        "segmento": segmento,
        "metas": metas,
        "restricoes": restricoes,
        "publicos": publicos,
        "canais": canais,
        "tom": tom,
        "briefing_livre": briefing
    }
    return f"Cliente: {json.dumps(brief_json, ensure_ascii=False)}\nTendências selecionadas: {json.dumps(context_trends, ensure_ascii=False)}"

st.markdown("---")
st.subheader("🤖 Geração de Ideias")

# Escolher provedor (OpenAI oficial via REST com requests para simplificar dependências)
provider = st.selectbox("Provedor LLM", ["OpenAI API (oficial)"], index=0)

def call_openai_chat(messages, model, temperature=0.4, max_tokens=1400):
    import requests
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        st.error("Defina a variável de ambiente OPENAI_API_KEY para gerar ideias.")
        return None
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code != 200:
        st.error(f"Erro da API OpenAI: {r.status_code} — {r.text}")
        return None
    data = r.json()
    return data["choices"][0]["message"]["content"]

colA, colB = st.columns([1,1])
with colA:
    generate = st.button("🚀 Gerar Ideias")
with colB:
    export_md = st.button("💾 Exportar último resultado (Markdown)")

if "last_output" not in st.session_state:
    st.session_state["last_output"] = ""

if generate:
    if not chosen:
        st.warning("Selecione pelo menos 1 tendência.")
    else:
        user_prompt = build_user_prompt()
        messages = [
            {"role":"system","content": system_prompt},
            {"role":"user","content": user_prompt},
        ]
        with st.spinner("Gerando ideias..."):
            out = call_openai_chat(messages, model=model_name, temperature=temperature, max_tokens=max_tokens)
        if out:
            st.session_state["last_output"] = out
            st.success("Ideias geradas!")
            st.markdown(out)

if export_md:
    if st.session_state["last_output"]:
        st.download_button("Baixar ideias (Markdown)", data=st.session_state["last_output"], file_name="ideias.md", mime="text/markdown")
    else:
        st.info("Gere ideias primeiro para exportar.")
