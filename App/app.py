import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR if (APP_DIR / "Data").exists() else APP_DIR.parent
HTML_DIR = APP_DIR if (APP_DIR / "RAG_STUDY.html").exists() else APP_DIR / "App"
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from App.auth_service import sign_out, verify_session
from App.auth_ui import render_auth_view
from App.chat_service import (
	check_database_schema,
	create_conversation,
	delete_conversation,
	generate_chat_title,
	get_conversation_messages,
	get_user_conversations,
	group_conversations_by_date,
	rename_conversation,
	save_message,
)
from App.supabase_client import get_authenticated_client
from rag.pipeline import RAGPipeline, create_pipeline

st.set_page_config(
	page_title="UniAssist — Academic Study Assistant",
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
		[data-testid='stSidebar'] {
			background: #103f38;
		}
		[data-testid='stSidebar'] * {
			color: #effaf4;
		}
		[data-testid='stHeader'], [data-testid='stToolbar'] { background: #f5faf7 !important; }
		[data-testid='stBottom'], [data-testid='stBottom'] > div, [data-testid='stBottomBlockContainer'], [data-testid='stBottomBlockContainer'] > div { background: #f5faf7 !important; }
		[data-testid='stAppViewContainer'] { background: transparent; }
		[data-testid='stDecoration'] { display: none; }
		[data-testid='stSidebar'] section { padding: 1.25rem 0.85rem 1.5rem; }

		/* HIDE STREAMLIT HEADING HOVER ANCHOR LINKS */
		a.anchor-link,
		.anchor-link,
		[data-testid="stMarkdownContainer"] h1 a,
		[data-testid="stMarkdownContainer"] h2 a,
		[data-testid="stMarkdownContainer"] h3 a,
		[data-testid="stMarkdownContainer"] h4 a,
		[data-testid="stMarkdownContainer"] h5 a,
		[data-testid="stMarkdownContainer"] h6 a,
		h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
			display: none !important;
			visibility: hidden !important;
			opacity: 0 !important;
			pointer-events: none !important;
			width: 0 !important;
			height: 0 !important;
		}
		
		/* UNIVERSAL BUTTON STYLING (NO EMOJIS, CLEAN EMERALD) */
		.stButton button, .stFormSubmitButton button {
			background: #176b59;
			border: 1px solid #278a70;
			border-radius: 8px;
			color: #ffffff !important;
			font-family: 'Space Grotesk', sans-serif;
			font-size: 13px;
			font-weight: 600;
			height: 38px;
			padding: 0 14px;
			cursor: pointer;
			transition: all 0.2s ease;
			display: inline-flex;
			align-items: center;
			justify-content: center;
			text-decoration: none;
		}
		.stButton button:hover, .stFormSubmitButton button:hover {
			background: #21816a;
			border-color: #8de0c1;
			color: #ffffff !important;
			transform: translateY(-1px);
			box-shadow: 0 4px 12px rgba(23, 107, 89, 0.2);
		}
		.stButton button:active, .stFormSubmitButton button:active {
			background: #135b4d;
			transform: translateY(0);
		}

		/* LEFT SIDEBAR STYLES (CHATGPT-STYLE) */
		.brand { padding: 4px 0 2px; color: #ffffff; font-size: 22px; font-weight: 700; letter-spacing: 0; }
		.marker { color: #a9d7c6 !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 11px; line-height: 1.4; word-break: break-word; margin-bottom: 14px; }
		.sidebar-label { color: #8de0c1 !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 10px; letter-spacing: 1px; text-transform: uppercase; margin-top: 14px; margin-bottom: 6px; }
		
		/* User Profile Pill at Bottom */
		.user-profile-box {
			background: rgba(23, 107, 89, 0.35);
			border: 1px solid #278a70;
			border-radius: 8px;
			padding: 10px 12px;
			margin-top: 16px;
			margin-bottom: 8px;
		}
		.user-name { color: #effaf4; font-size: 13px; font-weight: 600; }
		.user-email { color: #a9d7c6; font-size: 11px; word-break: break-all; }

		/* Sidebar Subjects */
		.subject-cover { border: 1px solid #3d806d; border-radius: 7px; margin: 6px 0 14px; padding: 10px; }
		.subject-item { color: #d7f0e5; font-family: 'Space Grotesk', sans-serif; font-size: 12px; line-height: 1.4; padding: 4px 0; }
		.subject-code { color: #8de0c1; font-family: 'IBM Plex Mono', monospace; font-size: 10px; margin-right: 5px; }
		.nav-link { border-bottom: 1px solid #2d6658; color: #effaf4 !important; display: block; font-family: 'Space Grotesk', sans-serif; font-size: 13px; padding: 8px 0; text-decoration: none !important; }
		.nav-link:hover { color: #8de0c1 !important; }
		.about-text { color: #d7f0e5 !important; font-family: 'Space Grotesk', sans-serif; font-size: 12px; line-height: 1.6; }
		
		/* CHATGPT-STYLE CHAT HISTORY SECTION IN SIDEBAR */
		.sidebar-history-container {
			border-top: 1px solid #2d6658;
			margin-top: 16px;
			padding-top: 12px;
		}
		.sidebar-history-group-label {
			color: #8de0c1;
			font-size: 10px;
			font-family: 'IBM Plex Mono', monospace;
			text-transform: uppercase;
			letter-spacing: 0.8px;
			font-weight: 700;
			margin: 10px 0 4px 2px;
		}
		.sidebar-chat-btn .stButton,
		.sidebar-active-btn .stButton {
			margin-bottom: 4px !important;
		}
		.sidebar-chat-btn .stButton button,
		.sidebar-active-btn .stButton button {
			height: auto !important;
			min-height: 38px !important;
			padding: 8px 12px !important;
			border-radius: 6px !important;
			text-align: left !important;
			justify-content: flex-start !important;
			align-items: center !important;
			width: 100% !important;
			transition: all 0.15s ease !important;
		}
		.sidebar-chat-btn .stButton button {
			background: rgba(23, 107, 89, 0.22) !important;
			border: 1px solid #2d6658 !important;
			border-left: 3px solid transparent !important;
			color: #d7f0e5 !important;
		}
		.sidebar-chat-btn .stButton button:hover {
			background: #176b59 !important;
			border-color: #5aa790 !important;
			border-left: 3px solid #5aa790 !important;
			color: #ffffff !important;
			transform: none !important;
		}
		.sidebar-active-btn .stButton button {
			background: #1d6b59 !important;
			border: 1px solid #8de0c1 !important;
			border-left: 4px solid #8de0c1 !important;
			color: #ffffff !important;
			font-weight: 600 !important;
			box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
			transform: none !important;
		}
		.sidebar-chat-btn .stButton button div,
		.sidebar-active-btn .stButton button div,
		.sidebar-chat-btn .stButton button p,
		.sidebar-active-btn .stButton button p,
		.sidebar-chat-btn .stButton button span,
		.sidebar-active-btn .stButton button span {
			text-align: left !important;
			justify-content: flex-start !important;
			white-space: nowrap !important;
			overflow: hidden !important;
			text-overflow: ellipsis !important;
			width: 100% !important;
			font-size: 12.5px !important;
			line-height: 1.4 !important;
			margin: 0 !important;
			padding: 0 !important;
		}

		/* MAIN CHAT WORKSPACE (CENTERED PC VIEW) */
		.workspace {
			max-width: 860px;
			margin: 0 auto;
			padding: clamp(24px, 5vh, 48px) 20px 140px;
		}
		.chat-header-bar {
			display: flex;
			align-items: center;
			justify-content: space-between;
			border-bottom: 1px solid #d4e7df;
			padding-bottom: 12px;
			margin-bottom: 20px;
		}
		.chat-header-title {
			font-size: 18px;
			font-weight: 700;
			color: #16352e;
		}
		.chat-header-badge {
			color: #176b59;
			background: rgba(23, 107, 89, 0.08);
			border: 1px solid rgba(23, 107, 89, 0.2);
			border-radius: 999px;
			padding: 2px 10px;
			font-size: 11px;
			font-family: 'IBM Plex Mono', monospace;
			text-transform: uppercase;
			letter-spacing: 0.5px;
		}
		.welcome-title { font-size: clamp(28px, 4vw, 42px); line-height: 1.15; margin: 8px 0 12px; max-width: 760px; }
		.welcome-copy { color: #52736a; font-size: 14px; line-height: 1.6; max-width: 680px; }
		
		/* Suggestion buttons row */
		.suggestion-button .stButton button {
			background: #ffffff !important;
			border: 1px solid #c3ded4 !important;
			color: #176b59 !important;
			font-size: 12px !important;
			font-weight: 600 !important;
			height: auto !important;
			min-height: 48px !important;
			padding: 10px 12px !important;
			text-align: left !important;
			justify-content: flex-start !important;
			line-height: 1.4 !important;
			white-space: normal !important;
			border-radius: 8px !important;
			box-shadow: 0 2px 8px rgba(19, 91, 77, 0.04) !important;
		}
		.suggestion-button .stButton button:hover {
			background: #eef7f3 !important;
			border-color: #176b59 !important;
			color: #103f38 !important;
			transform: translateY(-1px) !important;
			box-shadow: 0 4px 12px rgba(19, 91, 77, 0.08) !important;
		}

		/* Messages and Fixed Chat Input (PC Aligned) */
		[data-testid='stChatMessage'] { padding: 14px 0; border-bottom: 1px solid #d4e7df; }
		[data-testid='stChatMessageContent'] { line-height: 1.65; max-width: 760px; overflow-wrap: anywhere; }
		[data-testid='stChatInput'] { max-width: 860px; margin: 0 auto; padding: 0 20px 18px; }
		[data-testid='stBottomBlockContainer'] { padding-bottom: 12px; }
		[data-testid='stChatInput'] form { background: #ffffff !important; border: 1px solid #8fc9b5 !important; border-radius: 9px; box-shadow: 0 8px 24px rgba(19, 91, 77, .12); }
		[data-testid='stChatInput'] form:focus-within { border-color: #176b59 !important; box-shadow: 0 0 0 1px #176b59, 0 8px 24px rgba(19, 91, 77, .12); }
		[data-testid='stChatInput'] textarea,
		[data-testid='stChatInput'] textarea:focus,
		[data-testid='stChatInput'] textarea:hover { background: #ffffff !important; border: 0 !important; box-shadow: none !important; color: #16352e !important; -webkit-text-fill-color: #16352e !important; caret-color: #176b59; font-family: 'Space Grotesk', sans-serif; font-size: 14px; outline: 0; }
		[data-testid='stChatInput'] textarea::placeholder { color: #718e84 !important; opacity: 1 !important; -webkit-text-fill-color: #718e84 !important; }
		[data-testid='stChatInput'] button { color: #176b59; }

		/* CRISP HIGH-CONTRAST INLINE CODE AND CODE BLOCKS */
		code, [data-testid="stMarkdownContainer"] code, p code, li code, span code {
			background: #e4f2ec !important;
			color: #0e4b3e !important;
			border: 1px solid #b2dacb !important;
			border-radius: 5px !important;
			padding: 2px 7px !important;
			font-family: 'IBM Plex Mono', monospace !important;
			font-size: 0.88em !important;
			font-weight: 600 !important;
			display: inline-block !important;
			line-height: 1.35 !important;
		}

		pre, pre code, [data-testid="stMarkdownContainer"] pre, [data-testid="stCodeBlock"], .stCode {
			background: #0e2923 !important;
			color: #e6faf2 !important;
			border: 1px solid #236756 !important;
			border-radius: 8px !important;
			padding: 14px 18px !important;
			font-family: 'IBM Plex Mono', monospace !important;
			font-size: 13px !important;
			line-height: 1.6 !important;
			overflow-x: auto !important;
			display: block !important;
		}
		pre code {
			background: transparent !important;
			border: none !important;
			padding: 0 !important;
			color: #e6faf2 !important;
			display: block !important;
		}

		/* Markdown lists and bold text */
		[data-testid="stMarkdownContainer"] strong, [data-testid="stChatMessageContent"] strong {
			color: #103f38 !important;
			font-weight: 700 !important;
		}

		/* Input and Tab Highlights */
		div[data-baseweb="tab-list"] { gap: 4px; border-bottom: 2px solid #d4e7df !important; margin-bottom: 16px; }
		button[data-baseweb="tab"] { color: #52736a !important; font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important; font-size: 13px !important; padding: 8px 14px !important; border-radius: 6px 6px 0 0 !important; border: none !important; outline: none !important; background: transparent !important; transition: all 0.2s ease !important; }
		button[data-baseweb="tab"]:hover { color: #176b59 !important; background: rgba(23, 107, 89, 0.06) !important; }
		button[data-baseweb="tab"][aria-selected="true"], [data-testid="stTabs"] button[aria-selected="true"], [data-testid="stTabs"] button[aria-selected="true"] p, [data-testid="stTabs"] button[aria-selected="true"] span { color: #103f38 !important; font-weight: 700 !important; }
		div[data-baseweb="tab-highlight"], [data-testid="stTabs"] [data-baseweb="tab-highlight"], div[role="tablist"] + div { background-color: #176b59 !important; background: #176b59 !important; height: 3px !important; }
		[data-testid="stTabs"] [data-baseweb="tab-border"] { background-color: #d4e7df !important; }
		[data-testid="stTextInput"] > div, [data-testid="stTextInput"] > div > div, div[data-baseweb="input"], div[data-baseweb="base-input"] { border-radius: 8px !important; border: 1px solid #c3ded4 !important; background: #ffffff !important; transition: all 0.2s ease !important; }
		[data-testid="stTextInput"] > div:focus-within, [data-testid="stTextInput"] > div > div:focus-within, div[data-baseweb="input"]:focus-within, div[data-baseweb="base-input"]:focus-within, div[data-baseweb="input"]:focus-within > div, div[data-baseweb="base-input"]:focus-within > div { border-color: #176b59 !important; box-shadow: 0 0 0 2px rgba(23, 107, 89, 0.2) !important; outline: none !important; }
		[data-testid="stTextInput"] input, input[type="text"], input[type="password"] { color: #16352e !important; -webkit-text-fill-color: #16352e !important; caret-color: #176b59 !important; font-family: 'Space Grotesk', sans-serif !important; font-size: 14px !important; outline: none !important; }

		@media (max-width: 650px) {
			.workspace { padding: 16px 12px 110px; }
			h1.welcome-title { font-size: 26px !important; }
			.welcome-copy { font-size: 13px; }
		}
		</style>
		""",
		unsafe_allow_html=True,
	)


def show_html_page(page_name: str) -> None:
	page_files = {
		"study": HTML_DIR / "RAG_STUDY.html",
		"about": HTML_DIR / "My_Self.html",
	}
	page_file = page_files.get(page_name)
	if page_file is None or not page_file.exists():
		st.error("This page is not available yet.")
		return

	col_btn, _ = st.columns([1, 4])
	with col_btn:
		if st.button("← Back to chat", key="back_to_chat_btn"):
			st.query_params.clear()
			st.rerun()

	components.html(page_file.read_text(encoding="utf-8"), height=3000, scrolling=True)


@st.cache_resource(show_spinner=False)
def get_rag_pipeline() -> RAGPipeline:
	return create_pipeline()


# Initialize state stably
if "user" not in st.session_state:
	st.session_state.user = None
if "access_token" not in st.session_state:
	st.session_state.access_token = None
if "current_conversation_id" not in st.session_state:
	st.session_state.current_conversation_id = None
if "messages" not in st.session_state:
	st.session_state.messages = []
if "local_conversations" not in st.session_state:
	st.session_state.local_conversations = []
if "local_messages" not in st.session_state:
	st.session_state.local_messages = {}

# Restore session from query params on browser refresh
if not st.session_state.user or not st.session_state.access_token:
	saved_token = st.query_params.get("session_token")
	if saved_token:
		verified = verify_session(saved_token)
		if verified:
			st.session_state.user = verified
			st.session_state.access_token = saved_token

inject_styles()

# Authentication Boundary
if not st.session_state.user or not st.session_state.access_token:
	render_auth_view()
	st.stop()

# User is authenticated
current_user = st.session_state.user
user_id = current_user["id"]
client = get_authenticated_client(st.session_state.access_token)

# Navigation
current_page = st.query_params.get("page", "chat")

# Load conversations for authenticated user
conversations = get_user_conversations(client, user_id)
grouped_conversations = group_conversations_by_date(conversations)

# ==============================================================================
# LEFT SIDEBAR: ChatGPT-Style Layout with CHAT HISTORY AT THE LAST
# ==============================================================================
with st.sidebar:
	st.markdown("<div class='brand'>UniAssist</div>", unsafe_allow_html=True)
	st.markdown("<p class='marker'>@ProjectByShomay</p>", unsafe_allow_html=True)

	# + New Chat Quick Button at Top
	if st.button("+ New Chat", key="btn_side_new_chat", use_container_width=True):
		st.session_state.current_conversation_id = None
		st.session_state.messages = []
		st.rerun()

	# Subjects covered
	st.markdown("<p class='sidebar-label'>Subjects covered</p>", unsafe_allow_html=True)
	st.markdown(
		"""
		<div class='subject-cover'>
			<div class='subject-item'><span class='subject-code'>01</span>FDSA</div>
			<div class='subject-item'><span class='subject-code'>02</span>Cloud Computing</div>
			<div class='subject-item'><span class='subject-code'>03</span>Networking and Data Communication</div>
			<div class='subject-item'><span class='subject-code'>04</span>DSA</div>
		</div>
		""",
		unsafe_allow_html=True,
	)

	# Pages navigation
	st.markdown("<p class='sidebar-label'>Pages</p>", unsafe_allow_html=True)
	st.markdown("<a class='nav-link' href='?page=study' target='_self'>Study page →</a>", unsafe_allow_html=True)
	st.markdown("<a class='nav-link' href='?page=about' target='_self'>About Me →</a>", unsafe_allow_html=True)

	with st.expander("I am"):
		st.markdown(
			"<p class='about-text'><strong>Shomay Singh Parihar</strong><br>Building a focused academic study companion for learning, revision, and exploration.<br><a href='https://shomay12.github.io/Personal_web/' target='_blank' style='color:#8de0c1; text-decoration: underline; margin-top: 6px; display: inline-block;'>Personal Website ↗</a></p>",
			unsafe_allow_html=True,
		)
	with st.expander("About UniAssist"):
		st.markdown(
			"<p class='about-text'>A focused study workspace for organizing questions and learning across your academic subjects.</p>",
			unsafe_allow_html=True,
		)

	# CHAT HISTORY SECTION AT THE LAST OF THE LEFT SIDEBAR
	st.markdown("<div class='sidebar-history-container'>", unsafe_allow_html=True)
	st.markdown("<p class='sidebar-label'>Private Chat History</p>", unsafe_allow_html=True)

	if not conversations:
		st.caption("No conversations yet. Type a question to start your first chat.")
	else:
		for group_name, conv_list in grouped_conversations.items():
			st.markdown(f"<p class='sidebar-history-group-label'>{group_name}</p>", unsafe_allow_html=True)
			for conv in conv_list:
				cid = conv["id"]
				title = conv.get("title", "Conversation")
				is_active = cid == st.session_state.current_conversation_id
				btn_label = title
				btn_class = "sidebar-active-btn" if is_active else "sidebar-chat-btn"

				st.markdown(f"<div class='{btn_class}'>", unsafe_allow_html=True)
				if st.button(
					btn_label,
					key=f"side_conv_{cid}",
					use_container_width=True,
					help=f"Open: {title}",
				):
					st.session_state.current_conversation_id = cid
					st.session_state.messages = get_conversation_messages(client, cid, user_id)
					st.rerun()
				st.markdown("</div>", unsafe_allow_html=True)

		# Active Chat Options
		if st.session_state.current_conversation_id:
			active_conv = next(
				(c for c in conversations if c["id"] == st.session_state.current_conversation_id),
				None,
			)
			if active_conv:
				with st.expander("Manage Active Chat", expanded=False):
					new_title = st.text_input("Rename Chat", value=active_conv.get("title", ""), key="side_rename_input")
					col_ren, col_del = st.columns(2)
					with col_ren:
						if st.button("Save", key="side_save_title_btn", use_container_width=True):
							if new_title.strip():
								rename_conversation(client, active_conv["id"], new_title.strip(), user_id)
								st.rerun()
					with col_del:
						if st.button("Delete", key="side_delete_chat_btn", use_container_width=True):
							delete_conversation(client, active_conv["id"], user_id)
							st.session_state.current_conversation_id = None
							st.session_state.messages = []
							st.rerun()

	st.markdown("</div>", unsafe_allow_html=True)

	# User Profile Card & Sign Out at Very Bottom
	st.markdown(
		f"""
		<div class='user-profile-box'>
			<div class='user-name'>{current_user.get('full_name', 'Student')}</div>
			<div class='user-email'>{current_user.get('email', '')}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)

	if st.button("Sign Out", key="btn_side_sign_out", use_container_width=True):
		sign_out(st.session_state.access_token)
		st.session_state.user = None
		st.session_state.access_token = None
		st.session_state.current_conversation_id = None
		st.session_state.messages = []
		st.query_params.clear()
		st.rerun()

subject = "FDSA, Cloud Computing, Networking and Data Communication, DSA"

# Subpages View
if current_page in {"study", "about"}:
	show_html_page(current_page)
	st.stop()

# Sync active conversation messages if not loaded yet
if st.session_state.current_conversation_id and not st.session_state.messages:
	st.session_state.messages = get_conversation_messages(client, st.session_state.current_conversation_id, user_id)

# ==============================================================================
# MAIN WORKSPACE: Centered PC View
# ==============================================================================
st.markdown("<main class='workspace'>", unsafe_allow_html=True)

active_conv_title = None
if st.session_state.current_conversation_id:
	active_conv = next(
		(c for c in conversations if c["id"] == st.session_state.current_conversation_id),
		None,
	)
	if active_conv:
		active_conv_title = active_conv.get("title", "Active Conversation")

submitted_prompt = None

if active_conv_title:
	st.markdown(
		f"""
		<div class='chat-header-bar'>
			<div class='chat-header-title'>{active_conv_title}</div>
			<div class='chat-header-badge'>Private Chat</div>
		</div>
		""",
		unsafe_allow_html=True,
	)
elif not st.session_state.messages:
	st.markdown(
		f"<h1 class='welcome-title'>Welcome back, {current_user.get('full_name', 'Student')}!</h1>",
		unsafe_allow_html=True,
	)
	st.markdown(
		"<p class='welcome-copy'>Ask a question across your academic subjects (DSA, FDSA, Cloud Computing, Networking). Your conversation history is private and securely encrypted with PostgreSQL Row Level Security.</p>",
		unsafe_allow_html=True,
	)

	st.markdown("<p style='font-size: 11px; color: #52736a; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 24px; margin-bottom: 8px;'>Sample Study Questions (Click to Ask):</p>", unsafe_allow_html=True)
	col_s1, col_s2, col_s3 = st.columns(3)
	with col_s1:
		st.markdown("<div class='suggestion-button'>", unsafe_allow_html=True)
		if st.button("DSA: Dijkstra's Algorithm & Time Complexity", key="btn_sug_1", use_container_width=True):
			submitted_prompt = "Explain time complexity and how Dijkstra's algorithm works in Data Structures & Algorithms."
		st.markdown("</div>", unsafe_allow_html=True)
	with col_s2:
		st.markdown("<div class='suggestion-button'>", unsafe_allow_html=True)
		if st.button("Cloud: IaaS vs PaaS vs SaaS Differences", key="btn_sug_2", use_container_width=True):
			submitted_prompt = "What are the key differences between IaaS, PaaS, and SaaS in Cloud Computing?"
		st.markdown("</div>", unsafe_allow_html=True)
	with col_s3:
		st.markdown("<div class='suggestion-button'>", unsafe_allow_html=True)
		if st.button("ML: Gradient Descent Intuition & Steps", key="btn_sug_3", use_container_width=True):
			submitted_prompt = "Explain gradient descent in simple terms with an intuitive example."
		st.markdown("</div>", unsafe_allow_html=True)

# Display existing messages
for message in st.session_state.messages:
	with st.chat_message(message["role"]):
		st.markdown(message["content"])
		sources = message.get("sources")
		if message["role"] == "assistant" and sources:
			with st.expander("Sources"):
				for source in sources:
					page = source.get("page")
					page_label = f" · Page {page + 1}" if isinstance(page, int) else ""
					st.caption(f"{source['document']}{page_label}")

# User Input
chat_input_val = st.chat_input("Type a question about your subjects...")
prompt = chat_input_val or submitted_prompt

if prompt:
	now_iso = datetime.now(timezone.utc).isoformat()

	# 1. Ensure conversation exists
	if not st.session_state.current_conversation_id:
		title = generate_chat_title(prompt)
		new_conv = create_conversation(client, user_id, title)
		st.session_state.current_conversation_id = new_conv["id"]

	conv_id = st.session_state.current_conversation_id

	# 2. Add and persist user message
	user_msg_entry = {"role": "user", "content": prompt}
	st.session_state.messages.append(user_msg_entry)
	save_message(client, conv_id, user_id, "user", prompt)

	with st.chat_message("user"):
		st.markdown(prompt)

	# 3. Process with RAG Pipeline
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
		sources = result.get("sources", [])
		if sources:
			with st.expander("Sources"):
				for source in sources:
					page = source.get("page")
					page_label = f" · Page {page + 1}" if isinstance(page, int) else ""
					st.caption(f"{source['document']}{page_label}")

		# 4. Add and persist assistant message
		assistant_msg_entry = {"role": "assistant", "content": result["answer"], "sources": sources}
		st.session_state.messages.append(assistant_msg_entry)
		save_message(client, conv_id, user_id, "assistant", result["answer"], sources)

	st.rerun()

st.markdown("</main>", unsafe_allow_html=True)