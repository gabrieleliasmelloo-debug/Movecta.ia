from pathlib import Path
import html
import os
import re

import google.generativeai as genai
import streamlit as st


BASE_DIR = Path(__file__).parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"
ROLE_LABELS = {"manager": "Gestão e liderança", "employee": "Colaboradores"}
SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json"}
MODEL_NAME = "gemini-flash-lite-latest"


def ensure_knowledge_directories():
    for directory in (
        KNOWLEDGE_DIR / "common",
        KNOWLEDGE_DIR / "manager",
        KNOWLEDGE_DIR / "employee",
    ):
        directory.mkdir(parents=True, exist_ok=True)


def read_knowledge(role):
    documents = []
    directories = (KNOWLEDGE_DIR / "common", KNOWLEDGE_DIR / role)
    for directory in directories:
        for file_path in sorted(directory.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                content = file_path.read_text(encoding="utf-8", errors="ignore").strip()
                if content:
                    documents.append(
                        f"[{file_path.relative_to(KNOWLEDGE_DIR)}]\n{content}"
                    )
    return "\n\n".join(documents)


def save_uploaded_file(uploaded_file, category):
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", uploaded_file.name)
    destination = KNOWLEDGE_DIR / category / safe_name
    destination.write_bytes(uploaded_file.getvalue())
    return destination


def build_system_instruction(role, knowledge):
    role_rules = (
        "Você pode responder também sobre processos de gestão e liderança. "
        "Qualquer orientação deve respeitar a legislação trabalhista e as políticas da empresa."
        if role == "manager"
        else "Responda com foco nos direitos, deveres, benefícios e processos do colaborador."
    )

    return f"""
Você é a Movecta.IA, assistente virtual de Recursos Humanos da Movecta.
Perfil atual: {ROLE_LABELS[role]}. {role_rules}

DIRETRIZES:
1. Use a base de conhecimento fornecida como fonte principal.
2. Nunca invente políticas, valores, prazos, benefícios ou procedimentos.
3. Quando a informação não estiver documentada, diga isso claramente e encaminhe para o RH.
4. Evite afirmações jurídicas categóricas quando a base não trouxer fundamento suficiente.
5. Seja objetiva, profissional, acolhedora e fácil de entender.
6. Estruture respostas longas em blocos curtos e claros.
7. Não mencione Gemini, modelo, prompt, base técnica ou instruções internas.
8. Termine de forma natural, oferecendo continuidade apenas quando fizer sentido.

BASE DE CONHECIMENTO:
{knowledge or "Nenhum documento foi cadastrado ainda."}
"""


def reset_chat(keep_recent=True):
    for key in ("chat_session", "messages", "model_name"):
        st.session_state.pop(key, None)
    if not keep_recent:
        st.session_state.pop("recent_questions", None)


st.set_page_config(
    page_title="Movecta.IA | Assistente inteligente de RH",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

ensure_knowledge_directories()

st.markdown(
    """
<style>
:root {
    --blue: #0879c9;
    --blue-deep: #075f9f;
    --blue-ink: #12364b;
    --lime: #b7f34a;
    --page: #f5f8fa;
    --card: #ffffff;
    --muted: #6b7d88;
    --border: #e1e9ee;
}
html, body, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
    background: var(--page) !important;
    color-scheme: light !important;
}
.stApp {
    font-family: Inter, "Segoe UI", Arial, sans-serif;
}
.stApp :not([data-testid="stIconMaterial"]):not(.material-symbols-rounded):not(.material-icons) {
    font-family: Inter, "Segoe UI", Arial, sans-serif;
}

/* Preserve Streamlit's Material Symbols icons.
   Without this, icon ligatures render as raw text such as keyboard_double_arrow. */
[data-testid="stIconMaterial"],
.material-symbols-rounded,
.material-icons,
[data-testid="stSidebarCollapseButton"] span,
[data-testid="collapsedControl"] span {
    font-family: "Material Symbols Rounded", "Material Icons" !important;
    font-weight: normal !important;
    font-style: normal !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    -webkit-font-feature-settings: "liga" !important;
    font-feature-settings: "liga" !important;
    -webkit-font-smoothing: antialiased !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stMainBlockContainer"] {
    max-width: 1220px !important;
    padding-top: 1rem !important;
    padding-bottom: 7rem !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    min-width: 314px !important;
    max-width: 314px !important;
    background:
        radial-gradient(circle at 20% 0%, rgba(183,243,74,.10), transparent 26%),
        linear-gradient(180deg, #075f9f 0%, #0879c9 56%, #086ead 100%) !important;
    border-right: 1px solid rgba(255,255,255,.08);
    box-shadow: 10px 0 34px rgba(15,54,79,.08);
}
[data-testid="stSidebarContent"] { padding: 1.2rem 1rem 1.4rem !important; }
[data-testid="stSidebar"] * { color: #fff !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * { color: #d7edf8 !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-testid="stFileUploader"] section {
    background: rgba(255,255,255,.96) !important;
    color: #15384d !important;
    border-color: rgba(255,255,255,.42) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-testid="stFileUploader"] section * {
    color: #15384d !important;
}
.side-brand {
    display:flex; align-items:center; gap:12px;
    padding: 2px 3px 18px;
    border-bottom: 1px solid rgba(255,255,255,.18);
}
.side-logo {
    width:46px; height:46px; flex:0 0 46px;
    border-radius:14px; display:grid; place-items:center;
    background:rgba(255,255,255,.10);
    border:1px solid rgba(255,255,255,.22);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.16);
}
.side-logo svg { width:31px; height:22px; display:block; }
.side-brand-name { font-size:22px; line-height:1; font-weight:800; letter-spacing:-.6px; }
.side-brand-name b { color:var(--lime) !important; font-weight:800; }
.side-brand-tag { margin-top:5px; font-size:9px; color:#d9edf8 !important; letter-spacing:.7px; text-transform:uppercase; }
.side-status {
    display:flex; align-items:center; gap:8px; margin:14px 2px 8px;
    color:#e8f5fb !important; font-size:11px; font-weight:600;
}
.status-dot {
    width:7px; height:7px; border-radius:50%;
    background:var(--lime); box-shadow:0 0 0 4px rgba(183,243,74,.15);
}
.side-label {
    margin:20px 2px 8px;
    color:#cbe7f5 !important; font-size:9px; font-weight:800;
    letter-spacing:1.2px; text-transform:uppercase;
}
.recent-item {
    padding:10px 11px; margin:6px 0; border-radius:11px;
    background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.09);
    color:#f2f8fb !important; font-size:11px; line-height:1.35;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
}
.side-empty {
    padding:11px; border-radius:11px; color:#d5eaf6 !important;
    font-size:10px; line-height:1.45;
    border:1px dashed rgba(255,255,255,.18);
}
.admin-note {
    color:#cbe4f2 !important; font-size:9px; line-height:1.45; margin-top:8px;
}

/* Main chrome */
.topbar {
    display:flex; align-items:center; justify-content:space-between;
    padding: 2px 1px 15px; margin-bottom: 14px;
}
.top-brand { display:flex; align-items:center; gap:10px; }
.top-brand-mark {
    width:34px; height:34px; border-radius:10px; display:grid; place-items:center;
    background:linear-gradient(135deg,var(--blue),var(--blue-deep));
    color:#fff !important; font-weight:900; font-size:15px;
    box-shadow:0 7px 18px rgba(8,121,201,.18);
}
.top-brand-name { color:#173c52 !important; font-size:16px; font-weight:800; letter-spacing:-.2px; }
.top-brand-name b { color:var(--lime) !important; }
.top-env {
    padding:7px 10px; border-radius:999px; background:#fff;
    border:1px solid var(--border); color:#667b88 !important;
    font-size:9px; font-weight:800; letter-spacing:.8px; text-transform:uppercase;
}

/* Welcome */
.welcome-shell {
    position:relative; overflow:hidden;
    min-height:330px;
    padding:42px 44px;
    border-radius:26px;
    background:
        radial-gradient(circle at 92% 18%, rgba(183,243,74,.26), transparent 28%),
        radial-gradient(circle at 76% 72%, rgba(8,121,201,.12), transparent 30%),
        linear-gradient(135deg,#ffffff 0%,#f9fcfe 58%,#edf8fe 100%);
    border:1px solid #dce8ef;
    box-shadow:0 22px 55px rgba(22,57,78,.08);
    margin-bottom:24px;
}
.welcome-grid {
    display:grid; grid-template-columns:minmax(0,1.25fr) minmax(260px,.75fr);
    gap:30px; align-items:center;
}
.eyebrow {
    display:inline-flex; align-items:center; gap:7px;
    color:var(--blue) !important; font-size:10px; font-weight:900;
    letter-spacing:1.25px; text-transform:uppercase;
}
.eyebrow-dot {
    width:7px; height:7px; border-radius:50%; background:var(--lime);
    box-shadow:0 0 0 4px rgba(183,243,74,.16);
}
.welcome-shell h1 {
    color:#153b52 !important;
    font-size:42px !important; line-height:1.07 !important;
    letter-spacing:-1.5px !important; max-width:690px;
    margin:14px 0 14px !important;
}
.welcome-shell p {
    max-width:670px; margin:0 !important; color:#617783 !important;
    font-size:14px; line-height:1.7;
}
.trust-row { display:flex; flex-wrap:wrap; gap:8px; margin-top:22px; }
.trust-pill {
    padding:8px 11px; border-radius:999px; background:rgba(255,255,255,.78);
    border:1px solid #dce8ee; color:#486676 !important;
    font-size:10px; font-weight:650;
}
.ai-orb-wrap { display:grid; place-items:center; min-height:210px; }
.ai-orb {
    position:relative; width:180px; height:180px; border-radius:50%;
    display:grid; place-items:center;
    background:
        radial-gradient(circle at 35% 30%, rgba(255,255,255,.98), rgba(255,255,255,.62) 28%, transparent 29%),
        linear-gradient(145deg, rgba(183,243,74,.88), rgba(8,121,201,.88));
    box-shadow:
        0 25px 55px rgba(8,121,201,.18),
        inset 0 0 0 1px rgba(255,255,255,.7),
        inset -18px -18px 34px rgba(6,93,155,.18);
}
.ai-orb:before, .ai-orb:after {
    content:""; position:absolute; border-radius:50%; border:1px solid rgba(8,121,201,.16);
}
.ai-orb:before { width:214px; height:214px; }
.ai-orb:after { width:246px; height:246px; border-style:dashed; opacity:.62; }
.ai-core {
    width:62px; height:62px; border-radius:18px;
    display:grid; place-items:center;
    background:rgba(255,255,255,.90); color:var(--blue-deep) !important;
    font-size:25px; font-weight:900;
    box-shadow:0 10px 25px rgba(10,70,108,.13);
}

/* Role cards */
.section-kicker {
    margin:2px 0 11px; color:#738691 !important;
    font-size:10px; font-weight:850; letter-spacing:1px; text-transform:uppercase;
}
.role-card {
    min-height:188px; padding:26px 27px; border-radius:20px;
    background:#fff; border:1px solid var(--border);
    box-shadow:0 12px 32px rgba(22,57,78,.055);
    transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.role-card:hover {
    transform:translateY(-2px); border-color:#c5dce8;
    box-shadow:0 18px 38px rgba(22,57,78,.09);
}
.role-icon {
    width:48px; height:48px; border-radius:14px; display:grid; place-items:center;
    background:#eaf5fb; color:var(--blue) !important; font-size:20px; font-weight:800;
    margin-bottom:19px;
}
.role-card.manager .role-icon { background:#eff9dc; color:#628213 !important; }
.role-card strong { display:block; color:#173d54 !important; font-size:18px; margin-bottom:8px; }
.role-card span { color:#6d808b !important; font-size:12px; line-height:1.55; }
.role-meta { margin-top:14px; color:#90a0a9 !important; font-size:9px; text-transform:uppercase; letter-spacing:.7px; }

/* Buttons */
.stButton > button {
    border-radius:12px !important;
    min-height:43px;
    font-weight:750 !important;
    border:1px solid #d5e3eb !important;
    background:#fff !important; color:#1d536f !important;
    box-shadow:none !important;
}
.stButton > button:hover {
    border-color:#a9cadc !important; background:#f7fbfd !important; color:#0b6ca9 !important;
}
[data-testid="stSidebar"] .stButton > button {
    width:100%; background:rgba(255,255,255,.11) !important;
    color:#fff !important; border:1px solid rgba(255,255,255,.20) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background:rgba(255,255,255,.17) !important;
}

/* Chat */
.chat-head {
    display:flex; align-items:center; justify-content:space-between; gap:16px;
    padding:16px 18px; border-radius:18px;
    background:#fff; border:1px solid var(--border);
    box-shadow:0 9px 26px rgba(22,57,78,.045);
    margin-bottom:16px;
}
.chat-profile { display:flex; align-items:center; gap:12px; }
.chat-profile-icon {
    width:42px; height:42px; border-radius:13px; display:grid; place-items:center;
    background:linear-gradient(145deg,#edf9da,#e7f5fb); color:#2d7195 !important; font-size:18px;
}
.chat-profile strong { display:block; color:#173d54 !important; font-size:14px; }
.chat-profile span { display:block; color:#7a8d98 !important; font-size:10px; margin-top:3px; }
.chat-state {
    display:flex; align-items:center; gap:6px; color:#7b8d96 !important;
    font-size:9px; font-weight:800; text-transform:uppercase; letter-spacing:.7px;
}
.chat-state i { width:7px; height:7px; border-radius:50%; display:block; background:var(--lime); }

.assistant-intro {
    margin:4px 0 14px; padding:18px 20px; border-radius:18px;
    background:linear-gradient(135deg,#ffffff,#f8fcfe);
    border:1px solid var(--border);
}
.assistant-intro strong { color:#173d54 !important; font-size:15px; }
.assistant-intro p { color:#71848f !important; font-size:11px; margin:5px 0 0 !important; }

[data-testid="stChatMessage"] {
    border:1px solid #e0e8ed !important; border-radius:19px !important;
    padding:11px 14px !important; margin-bottom:10px !important;
    width:fit-content; max-width:min(78%,720px);
    background:#fff !important;
    box-shadow:0 7px 20px rgba(22,57,78,.045);
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * { color:#28495b !important; }
[data-testid="stChatMessage"]:has(.user-message-marker) {
    margin-left:auto !important;
    background:linear-gradient(135deg,#0879c9,#0665aa) !important;
    border-color:#0879c9 !important;
    box-shadow:0 10px 24px rgba(8,121,201,.16);
}
[data-testid="stChatMessage"]:has(.user-message-marker) * { color:#fff !important; }
[data-testid="stChatInput"] {
    background:#fff !important; border:1px solid #d7e3ea !important;
    border-radius:18px !important; padding:7px 9px !important;
    box-shadow:0 14px 34px rgba(22,57,78,.11) !important;
}
[data-testid="stChatInput"] textarea {
    background:#fff !important; color:#183b4f !important;
}
[data-testid="stChatInput"] textarea::placeholder { color:#8697a0 !important; opacity:1; }
[data-testid="stChatInput"] button {
    border-radius:12px !important; background:var(--blue) !important; color:#fff !important;
}
[data-testid="stBottom"], [data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] { background:var(--page) !important; box-shadow:none !important; }

.quick-title {
    margin:4px 0 9px; color:#80919a !important; font-size:9px;
    font-weight:850; text-transform:uppercase; letter-spacing:1px;
}

/* Upload */
[data-testid="stFileUploader"] section {
    border-radius:12px !important;
    overflow:hidden !important;
    min-width:0 !important;
}
[data-testid="stFileUploader"] section > div,
[data-testid="stFileUploader"] section label,
[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section small {
    max-width:100% !important;
}
[data-testid="stFileUploader"] section small {
    display:block !important;
    overflow:hidden !important;
    text-overflow:ellipsis !important;
    white-space:nowrap !important;
}
[data-baseweb="select"] > div { border-radius:11px !important; }

/* Sidebar visual safety */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    border:1px solid rgba(255,255,255,.13) !important;
    border-radius:12px !important;
    overflow:hidden !important;
    background:rgba(255,255,255,.045) !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    min-height:44px !important;
    padding:0 10px !important;
    overflow:hidden !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary p {
    font-size:11px !important;
    font-weight:700 !important;
    line-height:1.25 !important;
    margin:0 !important;
    white-space:normal !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary [data-testid="stIconMaterial"] {
    flex:0 0 auto !important;
    font-size:20px !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
    overflow:hidden !important;
}
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
[data-testid="collapsedControl"] [data-testid="stIconMaterial"] {
    font-size:24px !important;
    width:24px !important;
    height:24px !important;
    overflow:hidden !important;
}
[data-testid="stSidebar"] button {
    overflow:hidden !important;
}
[data-testid="stSidebar"] button [data-testid="stIconMaterial"] {
    flex:0 0 auto !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    overflow-wrap:anywhere;
}

@media (max-width: 920px) {
    [data-testid="stMainBlockContainer"] { padding-left:1rem !important; padding-right:1rem !important; }
    .welcome-grid { grid-template-columns:1fr; }
    .ai-orb-wrap { display:none; }
    .welcome-shell { padding:28px 24px; min-height:auto; }
    .welcome-shell h1 { font-size:32px !important; }
    .top-env { display:none; }
}
</style>
""",
    unsafe_allow_html=True,
)


# API
api_key = os.getenv("GEMINI_API_KEY")
secrets_file = BASE_DIR / ".streamlit" / "secrets.toml"

if not api_key and secrets_file.exists():
    for line in secrets_file.read_text(encoding="utf-8").splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() == "GEMINI_API_KEY":
            api_key = value.strip().strip('"').strip("'")
            break

if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except (FileNotFoundError, KeyError):
        api_key = None

if not api_key:
    st.error("A chave de teste da IA não está configurada.")
    st.stop()

genai.configure(api_key=api_key)

if "recent_questions" not in st.session_state:
    st.session_state.recent_questions = []


# Sidebar
with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
            <div class="side-logo">
                <svg viewBox="0 0 64 42" aria-hidden="true">
                    <path d="M4 31 L19 17 L28 25 L43 10" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M34 31 L50 16 L60 22" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div>
                <div class="side-brand-name">Movecta <b>IA</b></div>
                <div class="side-brand-tag">Movimento que conecta</div>
            </div>
        </div>
        <div class="side-status"><span class="status-dot"></span> Assistente disponível</div>
        """,
        unsafe_allow_html=True,
    )

    if "role" in st.session_state:
        if st.button("＋  Nova conversa", use_container_width=True):
            reset_chat(keep_recent=True)
            st.rerun()

        st.markdown('<div class="side-label">Últimas perguntas</div>', unsafe_allow_html=True)
        recent = st.session_state.recent_questions[-6:][::-1]
        if recent:
            for question in recent:
                safe_question = html.escape(question)
                st.markdown(
                    f'<div class="recent-item" title="{safe_question}">{safe_question}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="side-empty">Suas perguntas recentes aparecerão aqui durante esta sessão.</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="side-label">Administração</div>', unsafe_allow_html=True)
    with st.expander("Base de conhecimento", expanded=False):
        st.caption("Adicione documentos que serão considerados nas respostas.")
        upload_category = st.selectbox(
            "Disponível para",
            ["common", "manager", "employee"],
            format_func=lambda value: {
                "common": "Todos",
                "manager": "Gestão",
                "employee": "Colaboradores",
            }[value],
        )
        uploaded_file = st.file_uploader(
            "Novo documento",
            type=[extension[1:] for extension in SUPPORTED_EXTENSIONS],
        )
        if uploaded_file and st.button("Adicionar documento", use_container_width=True):
            saved_path = save_uploaded_file(uploaded_file, upload_category)
            st.success(f"Adicionado: {saved_path.name}")

        st.markdown(
            '<div class="admin-note">Ambiente de protótipo. Evite documentos com dados pessoais sensíveis nesta etapa de testes.</div>',
            unsafe_allow_html=True,
        )


# Header
top_left, top_right = st.columns([5, 1], vertical_alignment="center")
with top_left:
    st.markdown(
        """
        <div class="topbar">
            <div class="top-brand">
                <div class="top-brand-mark">M</div>
                <div class="top-brand-name">Movecta <b>IA</b></div>
            </div>
            <div class="top-env">Protótipo interno</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Welcome / role selection
if "role" not in st.session_state:
    st.markdown(
        """
        <div class="welcome-shell">
            <div class="welcome-grid">
                <div>
                    <div class="eyebrow"><span class="eyebrow-dot"></span> Inteligência aplicada à experiência de pessoas</div>
                    <h1>Informação de RH, quando você precisa.</h1>
                    <p>
                        A Movecta.IA transforma políticas, benefícios e processos internos em respostas claras,
                        rápidas e contextualizadas. Escolha seu perfil para iniciar um atendimento direcionado.
                    </p>
                    <div class="trust-row">
                        <span class="trust-pill">Contexto da Movecta</span>
                        <span class="trust-pill">Atendimento inteligente</span>
                        <span class="trust-pill">Respostas objetivas</span>
                    </div>
                </div>
                <div class="ai-orb-wrap">
                    <div class="ai-orb"><div class="ai-core">✦</div></div>
                </div>
            </div>
        </div>
        <div class="section-kicker">Selecione seu perfil de acesso</div>
        """,
        unsafe_allow_html=True,
    )

    manager_column, employee_column = st.columns(2, gap="medium")

    manager_column.markdown(
        """
        <div class="role-card manager">
            <div class="role-icon">◆</div>
            <strong>Gestão e liderança</strong>
            <span>Políticas internas, apoio à liderança, processos de gestão e orientação para situações do dia a dia.</span>
            <div class="role-meta">Gerentes e lideranças</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    employee_column.markdown(
        """
        <div class="role-card">
            <div class="role-icon">●</div>
            <strong>Colaboradores</strong>
            <span>Benefícios, férias, folha, direitos, rotinas e dúvidas frequentes da jornada na Movecta.</span>
            <div class="role-meta">Funcionários</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if manager_column.button("Entrar como liderança", use_container_width=True):
        st.session_state.role = "manager"
        reset_chat(keep_recent=True)
        st.rerun()

    if employee_column.button("Entrar como colaborador", use_container_width=True):
        st.session_state.role = "employee"
        reset_chat(keep_recent=True)
        st.rerun()

    st.stop()


# Chat
role = st.session_state.role
area_description = (
    "Políticas, liderança e processos de gestão"
    if role == "manager"
    else "Benefícios, direitos e rotinas do colaborador"
)

with top_right:
    if st.button("Trocar perfil", use_container_width=True):
        st.session_state.pop("role", None)
        reset_chat(keep_recent=True)
        st.rerun()

st.markdown(
    f"""
    <div class="chat-head">
        <div class="chat-profile">
            <div class="chat-profile-icon">✦</div>
            <div>
                <strong>Movecta.IA • {ROLE_LABELS[role]}</strong>
                <span>{area_description}</span>
            </div>
        </div>
        <div class="chat-state"><i></i> sessão ativa</div>
    </div>
    """,
    unsafe_allow_html=True,
)

knowledge = read_knowledge(role)
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=build_system_instruction(role, knowledge),
    generation_config={"temperature": 0.2, "max_output_tokens": 420},
)

if st.session_state.get("model_name") != MODEL_NAME:
    reset_chat(keep_recent=True)
    st.session_state.model_name = MODEL_NAME

if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown(
        """
        <div class="assistant-intro">
            <strong>Olá. Eu sou a Movecta.IA.</strong>
            <p>Posso ajudar a localizar informações de RH e transformar políticas internas em respostas mais simples. Escolha uma sugestão ou escreva sua dúvida abaixo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="quick-title">Sugestões para começar</div>', unsafe_allow_html=True)
    quick_prompt = None
    q1, q2, q3, q4 = st.columns(4)
    if q1.button("🏖️  Férias", use_container_width=True):
        quick_prompt = "Como funciona o processo de férias?"
    if q2.button("💳  Benefícios", use_container_width=True):
        quick_prompt = "Quais benefícios estão disponíveis para os colaboradores?"
    if q3.button("📄  Folha de pagamento", use_container_width=True):
        quick_prompt = "Tenho uma dúvida sobre folha de pagamento. O que está documentado?"
    if q4.button("👥  Falar com RH", use_container_width=True):
        quick_prompt = "Quando devo procurar o RH diretamente?"
else:
    quick_prompt = None

for message in st.session_state.messages:
    avatar = "💠" if message["role"] == "model" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        if message["role"] == "user":
            st.markdown('<span class="user-message-marker"></span>', unsafe_allow_html=True)
        st.markdown(message["content"])

typed_prompt = st.chat_input(
    "Pergunte sobre férias, benefícios, folha, políticas ou processos internos..."
)
prompt = typed_prompt or quick_prompt

if prompt:
    clean_prompt = prompt.strip()
    if clean_prompt:
        st.session_state.recent_questions.append(clean_prompt)
        st.session_state.recent_questions = st.session_state.recent_questions[-12:]
        st.session_state.messages.append({"role": "user", "content": clean_prompt})

        with st.chat_message("user", avatar="👤"):
            st.markdown('<span class="user-message-marker"></span>', unsafe_allow_html=True)
            st.markdown(clean_prompt)

        with st.chat_message("model", avatar="💠"):
            try:
                response_stream = st.session_state.chat_session.send_message(
                    clean_prompt, stream=True
                )

                def response_chunks():
                    for response_chunk in response_stream:
                        if response_chunk.text:
                            yield response_chunk.text

                answer = st.write_stream(response_chunks())
            except Exception as error:
                error_message = str(error).split("\n", 1)[0]
                answer = (
                    "Não consegui concluir a consulta agora. "
                    f"Detalhe técnico: {error_message}"
                )
                st.markdown(answer)

        st.session_state.messages.append({"role": "model", "content": answer})
