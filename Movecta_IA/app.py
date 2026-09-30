from pathlib import Path
import os
import re

import google.generativeai as genai
import streamlit as st


BASE_DIR = Path(__file__).parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"
ROLE_LABELS = {"manager": "Gerentes", "employee": "Funcionários"}
SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json"}
MODEL_NAME = "gemini-flash-lite-latest"
APP_LOGO_PATH = BASE_DIR / "assets" / "movecta-logo.png"


def ensure_knowledge_directories():
    for directory in (KNOWLEDGE_DIR / "common", KNOWLEDGE_DIR / "manager", KNOWLEDGE_DIR / "employee"):
        directory.mkdir(parents=True, exist_ok=True)


def read_knowledge(role):
    documents = []
    directories = (KNOWLEDGE_DIR / "common", KNOWLEDGE_DIR / role)
    for directory in directories:
        for file_path in sorted(directory.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                content = file_path.read_text(encoding="utf-8", errors="ignore").strip()
                if content:
                    documents.append(f"[{file_path.relative_to(KNOWLEDGE_DIR)}]\n{content}")
    return "\n\n".join(documents)


def save_uploaded_file(uploaded_file, category):
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", uploaded_file.name)
    destination = KNOWLEDGE_DIR / category / safe_name
    destination.write_bytes(uploaded_file.getvalue())
    return destination


def build_system_instruction(role, knowledge):
    role_rules = (
        "Você pode responder também sobre processos de gestão e liderança. IMPORTANTE: "
        "Qualquer ação gerencial deve estar alinhada com a CLT e políticas da empresa."
        if role == "manager"
        else "Responda com foco nos direitos, deveres e processos do colaborador. "
        "Você tem direito de conhecer e defender seus direitos pela CLT."
    )
    
    shared_guardrails = """
DIRETRIZES OBRIGATÓRIAS (NÃO PODEM SER VIOLADAS):
1. RESPEITO À CLT: Todas as respostas devem estar em conformidade com a Consolidação das Leis do Trabalho
2. PROTEÇÃO DE DIREITOS: Proteja direitos fundamentais como férias, descanso, repouso semanal, 13º salário
3. DEMISSÃO JUSTA: Demissões sem justa causa requerem aviso prévio de 30 dias e multa de FGTS de 40%
4. PROIBIÇÃO DE REPRESÁLIAS: Represálias contra colaboradores que reclamam ou recusam violações são crime
5. TRANSPARÊNCIA: Sempre explique direitos e deveres com base em lei, não em interpretações pessoais
6. ENCAMINHAMENTO: Em dúvidas, sempre encaminhe para o RH - não improvise diretrizes legais
"""
    
    return f"""
Você é a Movecta.IA, assistente virtual oficial de Recursos Humanos da Movecta.
Perfil atual: {ROLE_LABELS[role]}. {role_rules}

{shared_guardrails}

Use exclusivamente a base de conhecimento abaixo para responder. Quando perguntarem algo não documentado:
- Explique que não encontrou a informação
- Encaminhe para o RH (rh@movecta.com.br, ramal 1234)
- Nunca invente políticas, valores, prazos ou procedimentos
- Nunca ignore as normas CLT ou política da empresa

Mantenha tom cordial, objetivo. Finalize sempre perguntando se pode ajudar em mais alguma coisa.

BASE DE CONHECIMENTO:
{knowledge or "Nenhum documento foi cadastrado ainda."}
"""


st.set_page_config(page_title="Movecta.IA | Assistente de RH", page_icon="💬", layout="wide", initial_sidebar_state="expanded")
ensure_knowledge_directories()
st.markdown(
    """
    <style>
    :root {
        --movecta-blue: #0879c9;
        --movecta-blue-dark: #0564a8;
        --movecta-neon: #b7f34a;
        --movecta-page: #f8f9fa;
        --movecta-ink: #172b3a;
        --movecta-muted: #60717d;
    }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"] {
        color-scheme: light !important;
    }
    .stApp, .stApp * { font-family: "Montserrat", "Trebuchet MS", sans-serif; }
    [data-testid="stSidebarCollapseButton"] *,
    [data-testid="collapsedControl"] *,
    [data-testid="stIconMaterial"] {
        font-family: "Material Symbols Rounded", "Material Icons", sans-serif !important;
    }
    .stApp {
        background: var(--movecta-page);
        color: var(--movecta-ink);
    }
    [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"],
    [data-testid="stMainBlockContainer"] { background: var(--movecta-page) !important; }
    [data-testid="stAppViewBlockContainer"] h1,
    [data-testid="stAppViewBlockContainer"] h2,
    [data-testid="stAppViewBlockContainer"] h3,
    [data-testid="stAppViewBlockContainer"] p,
    [data-testid="stAppViewBlockContainer"] label,
    [data-testid="stAppViewBlockContainer"] span { color: var(--movecta-ink) !important; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: var(--movecta-blue);
        border-right: 0;
    }
    [data-testid="stSidebarContent"] { padding-top: 0.75rem !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] * { color: #e7f4ff !important; }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: white !important; }
    .sidebar-brand { padding: 0 0 10px; border-bottom: 1px solid #ffffff33; margin-bottom: 10px; }
    .sidebar-logo { padding: 0 0 5px; line-height: 0; }
    .sidebar-logo img { display: block; width: 176px !important; height: auto !important; object-fit: contain; }
    .sidebar-brand strong { color: white; font-size: 23px; letter-spacing: 0; }
    .sidebar-brand strong span { color: var(--movecta-neon); }
    .sidebar-brand small { display: block; color: #e7f4ff; margin-top: 4px; font-size: 11px; }
    .sidebar-section { color: #bde1f7; text-transform: uppercase; letter-spacing: 1px; font-size: 10px; font-weight: 800; margin: 12px 0 6px; }
    .sidebar-status { display: flex; align-items: center; gap: 8px; color: #e7f4ff; font-size: 12px; padding: 8px 0; }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--movecta-neon); box-shadow: 0 0 0 4px #b7f34a28; }
    .brand-header {
        display: flex; align-items: flex-start; justify-content: space-between;
        margin: 0 0 22px; padding: 8px 0 14px;
        background: transparent; border-bottom: 1px solid #e5e7eb;
    }
    .product-name { color: var(--movecta-blue); font: 800 28px "Trebuchet MS", sans-serif; letter-spacing: 0; }
    .product-name span { color: var(--movecta-neon); }
    .welcome-panel {
        padding: 24px 28px; border-radius: 8px; background: white;
        border: 1px solid #e5e7eb; box-shadow: 0 8px 24px #172b3a0d; margin-bottom: 22px;
    }
    .welcome-panel h1 { color: var(--movecta-blue-dark) !important; margin: 0 0 6px; font-size: 28px; }
    .welcome-panel p { color: #537080; margin: 0; }
    .welcome-kicker { color: var(--movecta-blue) !important; font-size: 11px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase; margin-bottom: 10px; }
    .welcome-panel .welcome-kicker { margin-bottom: 10px; }
    .role-card {
        padding: 24px; border-radius: 8px; background: white;
        border: 1px solid #e5e7eb; box-shadow: 0 5px 18px #172b3a0d;
    }
    .role-card strong { color: var(--movecta-blue-dark) !important; font-size: 18px; }
    .role-card span { color: #607985; display: block; margin-top: 7px; font-size: 13px; }
    .role-icon { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 8px; background: #e7f4fb; color: var(--movecta-blue); font-size: 22px; margin-bottom: 18px; }
    .role-card.manager .role-icon { background: #eef8d7; color: #5b7e0d; }
    .section-label { color: var(--movecta-muted); font-size: 12px; font-weight: 700; margin: 22px 0 10px; }
    .chat-context { display: flex; align-items: center; gap: 12px; padding: 10px 0 18px; border-bottom: 1px solid #e5e7eb; margin-bottom: 20px; }
    .chat-context-icon { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 8px; background: #eaf7d2; color: #5b7e0d; font-size: 19px; }
    .chat-context strong { color: var(--movecta-blue-dark); font-size: 15px; }
    .chat-context span { display: block; color: var(--movecta-muted); font-size: 11px; margin-top: 3px; }
    [data-testid="stChatMessage"] {
        border: 1px solid #dfe6eb; border-radius: 14px; padding: 10px 14px;
        background: #eef1f3 !important; margin-bottom: 10px; width: fit-content; max-width: min(78%, 640px);
        color: var(--movecta-ink) !important;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * { color: var(--movecta-ink) !important; }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        border-left: 0; margin-right: auto;
    }
    [data-testid="stChatMessage"]:has(.user-message-marker) {
        margin-left: auto; background: var(--movecta-blue) !important; border-color: var(--movecta-blue) !important; color: white !important;
    }
    [data-testid="stChatMessage"]:has(.user-message-marker) [data-testid="stMarkdownContainer"] {
        text-align: right;
    }
    [data-testid="stChatMessage"]:has(.user-message-marker) * { color: white !important; }
    [data-testid="stChatInput"] {
        background: white !important; border: 1px solid #d7dee3 !important;
        border-radius: 8px !important; box-shadow: 0 5px 18px #172b3a14 !important;
    }
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] {
        background: var(--movecta-page) !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] textarea:focus { outline: 2px solid #9bd9ff !important; }
    [data-testid="stChatInput"] button {
        background: var(--movecta-blue) !important; color: white !important;
        border-radius: 6px !important;
    }
    [data-testid="stChatInput"] textarea,
    [data-baseweb="textarea"] textarea,
    textarea,
    [data-testid="stTextInput"] input,
    input[type="text"],
    [data-testid="stFileUploader"] section,
    [data-baseweb="select"] > div {
        background: #ffffff !important;
        color: var(--movecta-ink) !important;
        border-color: #d7dee3 !important;
    }
    [data-testid="stChatInput"] textarea::placeholder,
    [data-baseweb="textarea"] textarea::placeholder,
    textarea::placeholder,
    input::placeholder { color: #607985 !important; opacity: 1 !important; }
    [data-baseweb="textarea"] { background: #ffffff !important; border-radius: 12px; }
    [data-testid="stChatInput"] { background: #ffffff !important; border-radius: 14px; padding: 4px; }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li { color: var(--movecta-ink) !important; }
    [data-testid="stFileUploader"] section {
        background: #ffffff !important; border: 1px solid #d7e2e8 !important;
        border-radius: 8px !important; padding: 12px !important; min-height: 92px;
    }
    [data-testid="stFileUploader"] section small,
    [data-testid="stFileUploader"] section span,
    [data-testid="stFileUploader"] section div { color: #435865 !important; }
    [data-testid="stFileUploader"] section svg { color: var(--movecta-blue) !important; fill: var(--movecta-blue) !important; }
    [data-testid="stFileUploader"] section small { font-size: 11px !important; }
    [data-testid="stFileUploader"] button {
        background: var(--movecta-blue) !important; color: white !important;
        border: 1px solid var(--movecta-blue) !important; border-radius: 7px !important;
        padding: 5px 12px !important; font-weight: 700 !important;
    }
    [data-testid="stFileUploader"] button:hover { background: var(--movecta-blue-dark) !important; color: white !important; }
    .stButton > button,
    .stButton > button[kind="secondary"] {
        background: var(--movecta-blue) !important; color: white !important;
        border: 1px solid var(--movecta-blue) !important; border-radius: 7px !important;
        box-shadow: none !important; font-weight: 700 !important;
    }
    .stButton > button:hover,
    .stButton > button:focus-visible {
        background: var(--movecta-blue-dark) !important; color: white !important;
        border-color: var(--movecta-blue-dark) !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--movecta-neon) !important; color: #173146 !important;
        border-color: var(--movecta-neon) !important;
    }
    .role-card + div { margin-top: 16px; }
    [data-testid="stHorizontalBlock"] > div:has(.role-card) .stButton > button {
        margin-top: 14px !important;
    }

    /* refinamento visual - interface profissional */
    [data-testid="stMainBlockContainer"] {
        max-width: 1180px !important;
        padding-top: 1.15rem !important;
        padding-bottom: 7rem !important;
    }
    [data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 300px !important;
        background:
            linear-gradient(180deg, #075f9f 0%, #0879c9 55%, #0b6ead 100%) !important;
        box-shadow: 8px 0 28px rgba(12, 52, 77, 0.08);
    }
    [data-testid="stSidebarContent"] { padding: 1.1rem 1rem 1.5rem !important; }
    .app-shell-header {
        display:flex; align-items:center; justify-content:space-between; gap:18px;
        padding: 14px 18px; margin-bottom: 18px; border:1px solid #e4eaf0;
        background:rgba(255,255,255,.92); border-radius:16px;
        box-shadow:0 8px 28px rgba(21,56,78,.06);
    }
    .app-shell-brand { display:flex; align-items:center; gap:12px; }
    .brand-mark {
        width:42px; height:42px; border-radius:12px; display:grid; place-items:center;
        background:linear-gradient(135deg,#0879c9,#055f9f); color:white !important;
        font-weight:900; font-size:17px; box-shadow:0 6px 14px rgba(8,121,201,.22);
    }
    .app-shell-brand strong { display:block; color:#15384d !important; font-size:16px; line-height:1.1; }
    .app-shell-brand small { color:#71828d !important; font-size:11px; }
    .test-badge {
        padding:7px 10px; border-radius:999px; background:#f0f7fb; border:1px solid #d8e9f4;
        color:#27617f !important; font-size:10px; font-weight:800; letter-spacing:.6px; text-transform:uppercase;
        white-space:nowrap;
    }
    .hero {
        position:relative; overflow:hidden; padding:34px 36px; border-radius:22px;
        background:linear-gradient(135deg,#ffffff 0%,#f5fbff 55%,#eef8ff 100%);
        border:1px solid #dfeaf1; box-shadow:0 16px 40px rgba(23,43,58,.07);
        margin-bottom:22px;
    }
    .hero:after {
        content:""; position:absolute; right:-70px; top:-95px; width:260px; height:260px;
        border-radius:50%; background:radial-gradient(circle,#b7f34a55 0%,#b7f34a00 68%);
    }
    .hero-kicker { color:#0879c9 !important; font-size:11px; font-weight:900; text-transform:uppercase; letter-spacing:1.4px; }
    .hero h1 { color:#163b52 !important; font-size:34px !important; margin:8px 0 10px !important; line-height:1.15; }
    .hero p { color:#657984 !important; max-width:720px; font-size:14px; line-height:1.65; margin:0 !important; }
    .hero-trust {
        display:flex; gap:10px; flex-wrap:wrap; margin-top:18px;
    }
    .hero-chip {
        font-size:11px; color:#466475 !important; padding:7px 10px; border-radius:999px;
        border:1px solid #dfe9ee; background:#ffffffaa;
    }
    .section-title { margin:4px 0 12px; color:#344f5f !important; font-size:12px; font-weight:800; letter-spacing:.2px; }
    .role-card {
        min-height:190px; padding:26px !important; border-radius:18px !important;
        border:1px solid #e1e8ed !important; box-shadow:0 10px 28px rgba(23,43,58,.055) !important;
        transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    }
    .role-card:hover {
        transform:translateY(-2px); box-shadow:0 16px 34px rgba(23,43,58,.09) !important; border-color:#c8dde9 !important;
    }
    .role-icon {
        width:48px !important; height:48px !important; border-radius:14px !important;
        font-size:20px !important; margin-bottom:20px !important;
    }
    .role-card strong { font-size:19px !important; }
    .role-card span { line-height:1.5; }
    .role-meta { margin-top:14px; font-size:11px; color:#7a8b95 !important; }
    .chat-context {
        border:1px solid #e2e9ed !important; border-radius:16px; padding:14px 16px !important;
        background:white; box-shadow:0 7px 22px rgba(23,43,58,.045); margin-bottom:18px !important;
    }
    .chat-context-icon { border-radius:12px !important; width:42px !important; height:42px !important; }
    .chat-context .context-meta { margin-left:auto; color:#84939c !important; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.6px; }
    .chat-wrap-label {
        font-size:10px; font-weight:800; color:#7b8c96 !important; text-transform:uppercase; letter-spacing:1.2px;
        margin:2px 0 12px;
    }
    [data-testid="stChatMessage"] {
        border-radius:18px !important; padding:12px 15px !important;
        box-shadow:0 5px 16px rgba(23,43,58,.045);
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background:#ffffff !important; border-color:#e1e8ed !important;
    }
    [data-testid="stChatMessage"]:has(.user-message-marker) {
        background:linear-gradient(135deg,#0879c9,#0669ae) !important;
        box-shadow:0 8px 18px rgba(8,121,201,.16);
    }
    [data-testid="stChatInput"] {
        border-radius:18px !important; border:1px solid #d9e3e9 !important;
        box-shadow:0 12px 30px rgba(23,43,58,.10) !important;
        padding:7px 9px !important;
    }
    [data-testid="stBottom"] { padding-bottom:14px !important; }
    .sidebar-card {
        margin:10px 0 14px; padding:12px 13px; border-radius:12px; background:#ffffff14;
        border:1px solid #ffffff25;
    }
    .sidebar-card strong { display:block; font-size:12px; color:#fff !important; margin-bottom:4px; }
    .sidebar-card span { font-size:10px; color:#d8ecf8 !important; line-height:1.45; display:block; }
    .sidebar-label {
        color:#cce8f7 !important; font-size:9px; font-weight:900; text-transform:uppercase; letter-spacing:1.3px;
        margin:18px 0 8px;
    }
    .security-note {
        margin-top:16px; padding-top:14px; border-top:1px solid #ffffff26;
        color:#d5eaf6 !important; font-size:9px; line-height:1.5;
    }
    @media (max-width: 900px) {
        [data-testid="stMainBlockContainer"] { padding-left:1rem !important; padding-right:1rem !important; }
        .hero { padding:24px 22px; }
        .hero h1 { font-size:27px !important; }
        .app-shell-header { padding:12px 14px; }
        .test-badge { display:none; }
    }

    </style>
    """,
    unsafe_allow_html=True,
)
brand_column, action_column = st.columns([5, 1], vertical_alignment="center")
with brand_column:
    st.markdown(
        '<div class="brand-header"><div class="product-name">Movecta <span>IA</span></div></div>',
        unsafe_allow_html=True,
    )

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
    except FileNotFoundError:
        api_key = None
if not api_key:
    st.error("Configure GEMINI_API_KEY nos secrets do Streamlit ou nas variáveis de ambiente.")
    st.stop()
genai.configure(api_key=api_key)

with st.sidebar:
    st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    st.image(str(APP_LOGO_PATH), width=176)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-status"><span class="status-dot"></span> Sistema operacional</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Base de conhecimento</div>', unsafe_allow_html=True)
    st.caption("Adicione arquivos em uma área. Eles serão lidos no próximo chat.")
    upload_category = st.selectbox("Disponível para", ["common", "manager", "employee"], format_func=lambda value: {
        "common": "Todos", "manager": "Gerentes", "employee": "Funcionários"
    }[value])
    uploaded_file = st.file_uploader("Novo documento", type=[extension[1:] for extension in SUPPORTED_EXTENSIONS])
    if uploaded_file and st.button("Adicionar à base", type="primary"):
        saved_path = save_uploaded_file(uploaded_file, upload_category)
        st.success(f"Documento adicionado: {saved_path.name}")

if "role" not in st.session_state:
    st.markdown(
        '<div class="hero"><div class="hero-kicker">Movecta.IA • Atendimento interno</div><h1>Seu ponto de partida para dúvidas de RH.</h1><p>Uma experiência de atendimento simples, rápida e orientada ao contexto de cada colaborador. Para começar, selecione abaixo o perfil que melhor representa seu acesso.</p><div class="hero-trust"><span class="hero-chip">Respostas com contexto</span><span class="hero-chip">Base interna Movecta</span><span class="hero-chip">Atendimento em português</span></div></div>',
        unsafe_allow_html=True,
    )
    manager_column, employee_column = st.columns(2)
    manager_column.markdown('<div class="role-card manager"><div class="role-icon">◈</div><strong>Área dos gerentes</strong><span>Políticas, liderança e processos de gestão.</span></div>', unsafe_allow_html=True)
    employee_column.markdown('<div class="role-card"><div class="role-icon">◉</div><strong>Área dos funcionários</strong><span>Direitos, benefícios e rotinas do colaborador.</span></div>', unsafe_allow_html=True)
    if manager_column.button("Acessar área de gestão", use_container_width=True):
        st.session_state.role = "manager"
        st.rerun()
    if employee_column.button("Acessar área do colaborador", use_container_width=True):
        st.session_state.role = "employee"
        st.rerun()
    st.stop()

role = st.session_state.role
area_description = "Políticas, liderança e processos de gestão" if role == "manager" else "Direitos, benefícios e rotinas do colaborador"
st.markdown(
    f'<div class="chat-context"><div class="chat-context-icon">✦</div><div><strong>Atendimento para {ROLE_LABELS[role].lower()}</strong><span>{area_description}</span></div></div>',
    unsafe_allow_html=True,
)
with action_column:
    change_role = st.button("Trocar perfil", use_container_width=True)
if change_role:
    for key in ("role", "chat_session", "messages"):
        st.session_state.pop(key, None)
    st.rerun()

knowledge = read_knowledge(role)
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=build_system_instruction(role, knowledge),
    generation_config={"temperature": 0.2, "max_output_tokens": 320},
)
if st.session_state.get("model_name") != MODEL_NAME:
    st.session_state.pop("chat_session", None)
    st.session_state.pop("messages", None)
    st.session_state.model_name = MODEL_NAME
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    st.session_state.messages = [{"role": "model", "content": "Olá! Sou a Movecta.IA. Como posso ajudar você hoje?"}]

for message in st.session_state.messages:
    avatar = "🤖" if message["role"] == "model" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        if message["role"] == "user":
            st.markdown('<span class="user-message-marker"></span>', unsafe_allow_html=True)
        st.markdown(message["content"])

if prompt := st.chat_input("Pergunte sobre benefícios, férias, políticas ou processos de RH..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown('<span class="user-message-marker"></span>', unsafe_allow_html=True)
        st.markdown(prompt)
    with st.chat_message("model", avatar="🤖"):
        try:
            response_stream = st.session_state.chat_session.send_message(prompt, stream=True)

            def response_chunks():
                for response_chunk in response_stream:
                    if response_chunk.text:
                        yield response_chunk.text

            answer = st.write_stream(response_chunks())
        except Exception as error:
            error_message = str(error).split("\n", 1)[0]
            answer = f"Não consegui consultar o Gemini agora. Detalhe: {error_message}"
            st.markdown(answer)
    st.session_state.messages.append({"role": "model", "content": answer})