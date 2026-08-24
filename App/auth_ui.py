"""Polished UniAssist Authentication Interface.

Provides Login, Sign Up, and Password Reset UI matching the UniAssist visual design system.
"""

from typing import Optional

import streamlit as st

from App.auth_service import reset_password, sign_in, sign_up


def inject_auth_styles() -> None:
    """Inject custom styles tailored for the authentication view."""
    st.markdown(
        """
        <style>
        .auth-container {
            max-width: 460px;
            margin: clamp(24px, 5vh, 60px) auto;
            padding: 32px 36px;
            background: #ffffff;
            border: 1px solid #c3ded4;
            border-radius: 14px;
            box-shadow: 0 16px 40px rgba(19, 91, 77, 0.08);
        }
        .auth-brand {
            font-family: 'Silkscreen', monospace !important;
            font-size: 26px;
            font-weight: 700;
            color: #103f38;
            letter-spacing: -0.5px;
            text-align: center;
            margin-bottom: 4px;
        }
        .auth-tagline {
            text-align: center;
            font-size: 13px;
            color: #52736a;
            margin-bottom: 24px;
        }
        .auth-badge {
            display: inline-block;
            background: rgba(23, 107, 89, 0.08);
            border: 1px solid rgba(23, 107, 89, 0.2);
            color: #176b59;
            border-radius: 999px;
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        .auth-footer {
            text-align: center;
            margin-top: 24px;
            font-size: 12px;
            color: #718e84;
        }
        .stButton button, .stFormSubmitButton button {
            background: #176b59 !important;
            border: 1px solid #278a70 !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            height: 42px !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        .stButton button:hover, .stFormSubmitButton button:hover {
            background: #21816a !important;
            border-color: #8de0c1 !important;
            color: #ffffff !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(23, 107, 89, 0.2) !important;
        }

        /* STRICT TAB STYLING OVERRIDES */
        div[data-baseweb="tab-list"] {
            gap: 4px;
            border-bottom: 2px solid #d4e7df !important;
            margin-bottom: 16px;
        }
        button[data-baseweb="tab"] {
            color: #52736a !important;
            font-family: 'Space Grotesk', sans-serif !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            padding: 8px 14px !important;
            border-radius: 6px 6px 0 0 !important;
            border: none !important;
            outline: none !important;
            background: transparent !important;
            transition: all 0.2s ease !important;
        }
        button[data-baseweb="tab"]:hover {
            color: #176b59 !important;
            background: rgba(23, 107, 89, 0.06) !important;
        }
        button[data-baseweb="tab"][aria-selected="true"],
        [data-testid="stTabs"] button[aria-selected="true"],
        [data-testid="stTabs"] button[aria-selected="true"] p,
        [data-testid="stTabs"] button[aria-selected="true"] span {
            color: #103f38 !important;
            font-weight: 700 !important;
        }
        div[data-baseweb="tab-highlight"],
        [data-testid="stTabs"] [data-baseweb="tab-highlight"],
        div[role="tablist"] + div {
            background-color: #176b59 !important;
            background: #176b59 !important;
            height: 3px !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab-border"] {
            background-color: #d4e7df !important;
        }

        /* STRICT INPUT STYLING AND FOCUS OVERRIDES */
        [data-testid="stTextInput"] > div,
        [data-testid="stTextInput"] > div > div,
        div[data-baseweb="input"],
        div[data-baseweb="base-input"] {
            border-radius: 8px !important;
            border: 1px solid #c3ded4 !important;
            background: #ffffff !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stTextInput"] > div:focus-within,
        [data-testid="stTextInput"] > div > div:focus-within,
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="base-input"]:focus-within,
        div[data-baseweb="input"]:focus-within > div,
        div[data-baseweb="base-input"]:focus-within > div {
            border-color: #176b59 !important;
            box-shadow: 0 0 0 2px rgba(23, 107, 89, 0.2) !important;
            outline: none !important;
        }
        [data-testid="stTextInput"] input,
        input[type="text"], input[type="password"] {
            color: #16352e !important;
            -webkit-text-fill-color: #16352e !important;
            caret-color: #176b59 !important;
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 14px !important;
            outline: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


from App.supabase_client import get_supabase_config, save_supabase_config


def render_auth_view() -> Optional[dict]:
    """Render the authentication screen and return the authenticated user dict on success."""
    inject_auth_styles()

    url, key = get_supabase_config()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 24px;">
                <div class="auth-brand">UniAssist</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not key:
            st.info(
                "**Supabase Setup Required**: Enter your Supabase `anon` API key below or add `SUPABASE_ANON_KEY` to your `.env` file."
            )
            with st.expander("Connect Supabase Credentials", expanded=True):
                with st.form("supabase_config_form"):
                    input_url = st.text_input("Supabase Project URL", value=url or "https://pbqiywxjcskxfrciamnl.supabase.co")
                    input_key = st.text_input("Supabase Anon Key", type="password", placeholder="eyJhbGciOiJIUzI1NiIsIn...")
                    save_config_btn = st.form_submit_button("Save & Connect →", use_container_width=True)
                    if save_config_btn:
                        if input_key.strip():
                            save_supabase_config(input_url, input_key)
                            st.success("Supabase credentials saved! Refreshing...")
                            st.rerun()
                        else:
                            st.error("Please enter a valid Anon Key.")

        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["Sign In", "Sign Up", "Forgot Password"])

        with auth_tab1:
            with st.form("signin_form", clear_on_submit=False):
                email = st.text_input("Email Address", key="signin_email", placeholder="student@university.edu")
                password = st.text_input(
                    "Password",
                    key="signin_password",
                    type="password",
                    placeholder="••••••••",
                )
                submit_btn = st.form_submit_button("Sign In to UniAssist →", use_container_width=True)

                if submit_btn:
                    with st.spinner("Authenticating..."):
                        result = sign_in(email, password)
                        if result.get("success"):
                            st.session_state.user = result["user"]
                            st.session_state.access_token = result["access_token"]
                            st.session_state.refresh_token = result.get("refresh_token")
                            st.session_state.current_conversation_id = None
                            st.session_state.messages = []
                            st.query_params["session_token"] = result["access_token"]
                            st.success(f"Welcome back, {result['user'].get('full_name', 'Student')}!")
                            st.rerun()
                        else:
                            st.error(result.get("error", "Failed to sign in."))

        with auth_tab2:
            with st.form("signup_form", clear_on_submit=False):
                full_name = st.text_input("Full Name", key="signup_name", placeholder="e.g. Alex Morgan")
                email = st.text_input("Email Address", key="signup_email", placeholder="student@university.edu")
                password = st.text_input(
                    "Password",
                    key="signup_password",
                    type="password",
                    placeholder="At least 6 characters",
                )
                confirm_password = st.text_input(
                    "Confirm Password",
                    key="signup_confirm_password",
                    type="password",
                    placeholder="Re-enter your password",
                )
                signup_btn = st.form_submit_button("Create UniAssist Account →", use_container_width=True)

                if signup_btn:
                    with st.spinner("Creating your secure account..."):
                        result = sign_up(email, password, confirm_password, full_name)
                        if result.get("success"):
                            if result.get("access_token"):
                                st.session_state.user = result["user"]
                                st.session_state.access_token = result["access_token"]
                                st.session_state.refresh_token = result.get("refresh_token")
                                st.session_state.current_conversation_id = None
                                st.session_state.messages = []
                                st.query_params["session_token"] = result["access_token"]
                                st.success("Account created successfully! Redirecting...")
                                st.rerun()
                            else:
                                st.success(result.get("message"))
                        else:
                            st.error(result.get("error", "Failed to create account."))

        with auth_tab3:
            with st.form("forgot_password_form", clear_on_submit=False):
                st.caption("Enter your registered email address to receive password recovery instructions.")
                email = st.text_input("Registered Email", key="forgot_email", placeholder="student@university.edu")
                reset_btn = st.form_submit_button("Send Reset Link →", use_container_width=True)

                if reset_btn:
                    with st.spinner("Sending recovery email..."):
                        result = reset_password(email)
                        if result.get("success"):
                            st.success(result.get("message"))
                        else:
                            st.error(result.get("error", "Failed to send reset email."))

    return None
