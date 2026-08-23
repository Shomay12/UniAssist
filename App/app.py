import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR if (APP_DIR / "Data").exists() else APP_DIR.parent
HTML_DIR = APP_DIR if (APP_DIR / "RAG_STUDY.html").exists() else APP_DIR / "App"
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from rag.pipeline import RAGPipeline, create_pipeline


st.set_page_config(
	page_title="Academic Study Assistant",
	page_icon="U",
	layout="wide",
	initial_sidebar_state="auto",
)


def inject_styles() -> None:
	st.markdown(
		"""
		<style>
		@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Pixelify+Sans:wght@400;500;600&family=Silkscreen:wght@400;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
		* { box-sizing: border-box; font-family: 'Space Grotesk', sans-serif; }
		h1.welcome-title { font-family: 'Pixelify Sans', sans-serif !important; letter-spacing: 0; font-weight: 500; }
		h2, h3 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: 0; font-weight: 600; }
		.brand { font-family: 'Silkscreen', monospace !important; letter-spacing: 0; font-weight: 400; }
		.stApp {
			background-color: #f5faf7;
			background-image: linear-gradient(rgba(19, 91, 77, .045) 1px, transparent 1px), linear-gradient(90deg, rgba(19, 91, 77, .045) 1px, transparent 1px);
			background-size: 32px 32px;
			color: #16352e;
		}
		[data-testid='stSidebar'] { background: #103f38; }
		[data-testid='stSidebar'] * { color: #effaf4; }
		[data-testid='stHeader'], [data-testid='stToolbar'] { background: #f5faf7 !important; }
		[data-testid='stBottom'], [data-testid='stBottom'] > div, [data-testid='stBottomBlockContainer'], [data-testid='stBottomBlockContainer'] > div { background: #f5faf7 !important; }
		[data-testid='stAppViewContainer'] { background: transparent; }
		[data-testid='stDecoration'] { display: none; }
		[data-testid='stSidebar'] section { padding: 1.5rem 1rem 1rem; }
		[data-testid='stSidebar'] .stButton button {
			background: #176b59; border: 1px solid #278a70; border-radius: 7px; color: #ffffff;
			font-family: 'Space Grotesk', sans-serif; font-size: 14px; font-weight: 600; height: 42px;
			padding: 0 12px;
		}
		[data-testid='stSidebar'] .stButton button:hover { background: #21816a; border-color: #8de0c1; }
		.brand { padding: 12px 0 8px; color: #ffffff; font-size: 22px; font-weight: 700; letter-spacing: 0; }
		.marker, .sidebar-label { font-family: 'IBM Plex Mono', monospace !important; }
		.marker { color: #a9d7c6 !important; font-size: 11px; line-height: 1.5; word-break: break-word; margin-bottom: 26px; }
		.sidebar-label { color: #8de0c1 !important; font-size: 10px; letter-spacing: 1px; text-transform: uppercase; }
		.subject-cover { border: 1px solid #3d806d; border-radius: 7px; margin: 8px 0 22px; padding: 12px; }
		.subject-item { color: #d7f0e5; font-family: 'Space Grotesk', sans-serif; font-size: 12px; line-height: 1.45; padding: 5px 0; }
		.subject-code { color: #8de0c1; font-family: 'IBM Plex Mono', monospace; font-size: 10px; margin-right: 5px; }
		.nav-link { border-bottom: 1px solid #2d6658; color: #effaf4 !important; display: block; font-family: 'Space Grotesk', sans-serif; font-size: 13px; padding: 10px 0; text-decoration: none !important; }
		.nav-link:hover { color: #8de0c1 !important; }
		.about-text { color: #d7f0e5 !important; font-family: 'Space Grotesk', sans-serif; font-size: 12px; line-height: 1.6; }
		.workspace { max-width: 820px; margin: 0 auto; padding: clamp(44px, 10vh, 104px) 24px 140px; }
		.welcome-title { font-size: clamp(30px, 4.2vw, 46px); line-height: 1.12; margin: 16px 0 12px; max-width: 760px; }
		.welcome-copy { color: #52736a; font-size: clamp(14px, 1.4vw, 16px); line-height: 1.6; max-width: 650px; }
		.suggestion { background: #ffffff; border: 1px solid #c3ded4; border-radius: 7px; color: #52736a; display: inline-block; font-family: 'Space Grotesk', sans-serif; font-size: 13px; margin-top: 30px; padding: 10px 12px; }
		[data-testid='stChatMessage'] { padding: 18px 0; border-bottom: 1px solid #d4e7df; }
		[data-testid='stChatMessageContent'] { line-height: 1.65; max-width: 700px; overflow-wrap: anywhere; }
		[data-testid='stChatInput'] { max-width: 820px; margin: 0 auto; padding: 0 24px 18px; }
		[data-testid='stBottomBlockContainer'] { padding-bottom: 12px; }
		[data-testid='stChatInput'] form { background: #ffffff !important; border: 1px solid #8fc9b5 !important; border-radius: 9px; box-shadow: 0 8px 24px rgba(19, 91, 77, .12); }
		[data-testid='stChatInput'] form:focus-within { border-color: #176b59 !important; box-shadow: 0 0 0 1px #176b59, 0 8px 24px rgba(19, 91, 77, .12); }
		[data-testid='stChatInput'] textarea,
		[data-testid='stChatInput'] textarea:focus,
		[data-testid='stChatInput'] textarea:hover { background: #ffffff !important; border: 0 !important; box-shadow: none !important; color: #16352e !important; -webkit-text-fill-color: #16352e !important; caret-color: #176b59; font-family: 'Space Grotesk', sans-serif; font-size: 14px; outline: 0; }
		[data-testid='stChatInput'] textarea::placeholder { color: #718e84 !important; opacity: 1 !important; -webkit-text-fill-color: #718e84 !important; }
		[data-testid='stChatInput'] button { color: #176b59; }
		@media (min-width: 651px) and (max-width: 1100px) {
			.workspace { max-width: 720px; padding-top: 64px; }
		}
		@media (max-width: 650px) {
			[data-testid='stSidebar'] section { padding: 1rem .75rem; }
			[data-testid='stSidebar'] { min-width: 280px; max-width: 88vw; }
			.brand { font-size: 20px; }
			.marker { font-size: 10px; margin-bottom: 18px; }
			.subject-item { font-size: 11px; }
			.nav-link { font-size: 12px; padding: 9px 0; }
			.workspace { padding: 24px 16px 112px; }
			h1.welcome-title { font-size: 30px !important; line-height: 1.16; max-width: 100%; }
			.welcome-copy { font-size: 14px; }
			.subject-cover { margin-bottom: 18px; }
			[data-testid='stChatInput'] { padding: 0 16px 12px; }
			[data-testid='stChatMessage'] { padding: 14px 0; }
		}
		</style>
		""",
		unsafe_allow_html=True,
	)


def reset_chat() -> None:
	st.session_state.messages = []
	st.session_state.pop("last_error", None)


def show_html_page(page_name: str) -> None:
	page_files = {
		"study": HTML_DIR / "RAG_STUDY.html",
		"about": HTML_DIR / "My_Self.html",
	}
	page_file = page_files.get(page_name)
	if page_file is None or not page_file.exists():
		st.error("This page is not available yet.")
		return

	if st.button("← Back to chat", key="back_to_chat"):
		st.query_params.clear()
		st.rerun()
	components.html(page_file.read_text(encoding="utf-8"), height=3000, scrolling=True)


@st.cache_resource(show_spinner=False)
def get_rag_pipeline() -> RAGPipeline:
	return create_pipeline()


inject_styles()

if "messages" not in st.session_state:
	st.session_state.messages = []

current_page = st.query_params.get("page", "chat")

with st.sidebar:
	st.markdown("<div class='brand'>UniAssist</div>", unsafe_allow_html=True)
	st.markdown("<p class='marker'>@ProjectByShomay</p>", unsafe_allow_html=True)
	st.button("↺  Clear chat", key="clear_chat", use_container_width=True, on_click=reset_chat)
	st.markdown("<p class='sidebar-label'>Subjects covered</p>", unsafe_allow_html=True)
	st.markdown(
		"""
		<div class='subject-cover'>
			<div class='subject-item'><span class='subject-code'>01</span>FDSA</div>
			<div class='subject-item'><span class='subject-code'>02</span>Cloud Computing</div>
			<div class='subject-item'><span class='subject-code'>03</span>Networking and Data Communication</div>
		</div>
		""",
		unsafe_allow_html=True,
	)
	st.markdown("<p class='sidebar-label'>Pages</p>", unsafe_allow_html=True)
	st.markdown("<a class='nav-link' href='?page=study'>Study page →</a>", unsafe_allow_html=True)
	st.markdown("<a class='nav-link' href='?page=about'>About Me →</a>", unsafe_allow_html=True)
	with st.expander("I am"):
		st.markdown(
			"<p class='about-text'><strong>Shomay Singh Parihar</strong><br>Building a focused academic study companion for learning, revision, and exploration.</p>",
			unsafe_allow_html=True,
		)
	with st.expander("About UniAssist"):
		st.markdown(
			"<p class='about-text'>A focused study workspace for organizing questions and learning across your academic subjects.</p>",
			unsafe_allow_html=True,
		)

subject = "FDSA, Cloud Computing, Networking and Data Communication"

if current_page in {"study", "about"}:
	show_html_page(current_page)
	st.stop()

st.markdown("<main class='workspace'>", unsafe_allow_html=True)
if not st.session_state.messages:
	st.markdown("<h1 class='welcome-title'>Academic Study Assistant</h1>", unsafe_allow_html=True)
	st.markdown(
		"<p class='welcome-copy'>Choose a subject and start working through your study questions.</p>",
		unsafe_allow_html=True,
	)
	st.markdown("<p class='suggestion'>Try: Explain gradient descent in simple terms.</p>", unsafe_allow_html=True)

for message in st.session_state.messages:
	with st.chat_message(message["role"]):
		st.markdown(message["content"])
		if message["role"] == "assistant" and message.get("sources"):
			with st.expander("Sources"):
				for source in message["sources"]:
					page = source.get("page")
					page_label = f" · Page {page + 1}" if isinstance(page, int) else ""
					st.caption(f"{source['document']}{page_label}")

prompt = st.chat_input("Type a question about your subjects...")
if prompt:
	st.session_state.messages.append({"role": "user", "content": prompt})
	with st.chat_message("user"):
		st.markdown(prompt)
	with st.chat_message("assistant"):
		with st.spinner("Thinking through your study material..."):
			try:
				result = get_rag_pipeline().ask(prompt, subject)
			except Exception as error:
				result = {
					"answer": "The study resources could not be loaded. Check that the existing vector store and required packages are available.",
					"sources": [],
				}
				st.error(str(error))
		st.markdown(result["answer"])
		if result.get("sources"):
			with st.expander("Sources"):
				for source in result["sources"]:
					page = source.get("page")
					page_label = f" · Page {page + 1}" if isinstance(page, int) else ""
					st.caption(f"{source['document']}{page_label}")
		st.session_state.messages.append(
			{"role": "assistant", "content": result["answer"], "sources": result.get("sources", [])}
		)

st.markdown("</main>", unsafe_allow_html=True)