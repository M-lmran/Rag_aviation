"""
AeroAssist – Streamlit Frontend (app.py)
Run: streamlit run frontend/app.py
"""
import streamlit as st
from frontend import api_client as api

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AeroAssist – Aircraft Maintenance Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, body, .stApp { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0a0f1e 0%, #0d1b2a 50%, #0a1628 100%);
    color: #e2e8f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b2a 0%, #0a1628 100%) !important;
    border-right: 1px solid rgba(99,179,237,0.15);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

/* Cards */
.aero-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(99,179,237,0.2);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    transition: border-color 0.2s;
}
.aero-card:hover { border-color: rgba(99,179,237,0.5); }

/* Message bubbles */
.msg-user {
    background: linear-gradient(135deg, #1a4080 0%, #2563eb 100%);
    border-radius: 18px 18px 4px 18px;
    padding: 0.85rem 1.2rem;
    margin: 0.5rem 0 0.5rem 3rem;
    color: #fff;
    box-shadow: 0 2px 12px rgba(37,99,235,0.4);
}
.msg-ai {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(99,179,237,0.25);
    border-radius: 18px 18px 18px 4px;
    padding: 0.85rem 1.2rem;
    margin: 0.5rem 3rem 0.5rem 0;
    color: #e2e8f0;
}

/* Source chip */
.src-chip {
    display: inline-block;
    background: rgba(37,99,235,0.2);
    border: 1px solid rgba(99,179,237,0.3);
    border-radius: 8px;
    padding: 0.2rem 0.6rem;
    font-size: 0.75rem;
    margin: 0.2rem;
    color: #93c5fd;
}

/* Logo text */
.logo-text {
    font-size: 1.5rem;
    font-weight: 700;
    background: linear-gradient(90deg, #60a5fa, #93c5fd);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.logo-sub {
    font-size: 0.75rem;
    color: #64748b;
    margin-top: -4px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #2563eb);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 500;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb, #3b82f6);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(37,99,235,0.4);
}

/* Input */
.stTextInput input, .stTextArea textarea {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(99,179,237,0.3) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
}

/* Progress bar */
.stProgress > div > div { border-radius: 8px; }

/* Metric */
.stMetric { background: rgba(255,255,255,0.04); border-radius: 12px; padding: 0.5rem; }

.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #93c5fd;
    margin-bottom: 0.75rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(99,179,237,0.2);
}
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "token": None, "role": None, "username": None,
        "chat_history": [], "page": "chat",
        "last_query_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ═══════════════════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def show_login():
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding: 2rem 0 1rem;'>
            <div style='font-size:4rem;'>✈️</div>
            <div class='logo-text' style='font-size:2rem;'>AeroAssist</div>
            <div class='logo-sub' style='font-size:0.9rem; margin-bottom:1.5rem;'>
                Aircraft Maintenance Assistant
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown('<div class="aero-card">', unsafe_allow_html=True)
            st.markdown("### 🔐 Sign In")
            username = st.text_input("Username", placeholder="admin or engineer")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In →", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if submitted:
                with st.spinner("Authenticating…"):
                    result = api.login(username, password)
                if "error" in result:
                    st.error(result["error"])
                else:
                    token = result["access_token"]
                    user_info = api.me(token)
                    st.session_state.token    = token
                    st.session_state.role     = user_info.get("role", "engineer")
                    st.session_state.username = user_info.get("username", username)
                    st.rerun()

        st.markdown(
            "<p style='text-align:center;color:#475569;font-size:0.8rem;margin-top:1rem;'>"
            "Default: <b>admin/admin123</b> &nbsp;|&nbsp; <b>engineer/eng123</b></p>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
def show_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='padding:1rem 0 0.5rem;'>
            <div class='logo-text'>✈️ AeroAssist</div>
            <div class='logo-sub'>Aircraft Maintenance Assistant</div>
        </div>
        """, unsafe_allow_html=True)

        backend_ok = api.health()
        status_color = "#22c55e" if backend_ok else "#ef4444"
        status_label = "Backend Online" if backend_ok else "Backend Offline"
        st.markdown(
            f"<div style='font-size:0.75rem;color:{status_color};margin-bottom:1rem;'>"
            f"● {status_label}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("### Navigation")

        pages = [("💬 Chat Assistant", "chat"), ("📜 Query History", "history")]
        if st.session_state.role == "admin":
            pages.append(("📤 Upload Manual", "upload"))
            pages.append(("📊 Admin Dashboard", "admin"))
            pages.append(("👤 Manage Users", "users"))

        for label, key in pages:
            active = st.session_state.page == key
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.page = key
                st.rerun()

        st.markdown("---")
        info = api.list_manuals(st.session_state.token)
        manuals = info.get("manuals", [])
        st.markdown(f"**📚 Indexed Manuals:** {len(manuals)}")
        for m in manuals:
            st.markdown(f"<span class='src-chip'>{m}</span>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            f"<div style='font-size:0.8rem;color:#64748b;'>"
            f"👤 {st.session_state.username} &nbsp;|&nbsp; "
            f"<b>{st.session_state.role.capitalize()}</b></div>",
            unsafe_allow_html=True,
        )
        if st.button("🚪 Logout", use_container_width=True):
            for k in ["token", "role", "username", "chat_history", "last_query_id"]:
                st.session_state[k] = None if k != "chat_history" else []
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  CHAT PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def show_chat():
    st.markdown('<div class="section-title">💬 Chat Assistant</div>', unsafe_allow_html=True)

    # chat history display
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div class='aero-card' style='text-align:center;padding:2rem;'>
                <div style='font-size:3rem;'>🔧</div>
                <div style='font-size:1.1rem;font-weight:600;color:#93c5fd;margin:0.5rem 0;'>
                    Ask anything about aircraft maintenance
                </div>
                <div style='color:#64748b;font-size:0.9rem;'>
                    Upload a manual first, then ask questions like:<br>
                    <em>"What is the torque spec for engine mount bolts?"</em><br>
                    <em>"Describe the pre-flight inspection checklist."</em>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for entry in st.session_state.chat_history:
                # user message
                st.markdown(
                    f"<div class='msg-user'>🧑‍✈️ &nbsp;<b>You</b><br>{entry['query']}</div>",
                    unsafe_allow_html=True,
                )
                # AI message
                st.markdown(
                    f"<div class='msg-ai'>🤖 &nbsp;<b>AeroAssist</b><br><br>{entry['answer']}</div>",
                    unsafe_allow_html=True,
                )

                # confidence bar
                conf = entry.get("confidence", 0)
                conf_pct = int(conf * 100)
                conf_color = "#22c55e" if conf > 0.6 else ("#f59e0b" if conf > 0.35 else "#ef4444")
                st.markdown(
                    f"<div style='font-size:0.75rem;color:#64748b;margin:0.2rem 0.5rem;'>"
                    f"Confidence: <b style='color:{conf_color};'>{conf_pct}%</b></div>",
                    unsafe_allow_html=True,
                )
                st.progress(conf)

                # sources
                sources = entry.get("sources", [])
                if sources:
                    st.markdown(f"**📎 {len(sources)} Source Reference(s):**")
                    for i, s in enumerate(sources, 1):
                        score_pct = int(s.get("score", 0) * 100)
                        st.markdown(
                            f"<div class='aero-card'>"
                            f"<b>Source {i}</b> &nbsp;|&nbsp; "
                            f"<span class='src-chip'>{s.get('manual','?')}</span>"
                            f"<span class='src-chip'>Page {s.get('page','?')}</span>"
                            f"<span class='src-chip'>Match {score_pct}%</span>"
                            f"<hr style='border-color:rgba(99,179,237,0.15);margin:0.5rem 0;'>"
                            f"<div style='font-size:0.82rem;color:#94a3b8;font-style:italic;'>"
                            f"{s.get('snippet','')[:280]}…</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                # feedback
                qid = entry.get("query_id")
                if qid:
                    fb_col1, fb_col2, _ = st.columns([0.08, 0.08, 0.84])
                    with fb_col1:
                        if st.button("👍", key=f"up_{qid}"):
                            api.send_feedback(st.session_state.token, qid, "up")
                            st.toast("Thanks for your feedback!", icon="✅")
                    with fb_col2:
                        if st.button("👎", key=f"dn_{qid}"):
                            api.send_feedback(st.session_state.token, qid, "down")
                            st.toast("Feedback recorded", icon="📝")

                st.markdown("---")

    # input row
    col_inp, col_btn = st.columns([5, 1])
    with col_inp:
        query = st.text_input(
            "Your question",
            placeholder="e.g. What are the hydraulic pressure limits for the landing gear?",
            label_visibility="collapsed",
            key="chat_input",
        )
    with col_btn:
        send = st.button("Send ✈️", use_container_width=True)

    if send and query.strip():
        with st.spinner("Searching manuals and generating answer…"):
            result = api.ask(st.session_state.token, query)
        if "error" in result:
            st.error(result["error"])
        else:
            st.session_state.chat_history.append({
                "query":      query,
                "answer":     result.get("answer", ""),
                "confidence": result.get("confidence", 0),
                "sources":    result.get("sources", []),
                "query_id":   result.get("query_id"),
            })
            elapsed = result.get("elapsed_seconds", 0)
            cached  = result.get("cached", False)
            st.toast(
                f"{'⚡ Cached' if cached else f'⏱ {elapsed}s'} response",
                icon="✅",
            )
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  UPLOAD PAGE  (admin only)
# ═══════════════════════════════════════════════════════════════════════════════
def show_upload():
    st.markdown('<div class="section-title">📤 Upload Maintenance Manual</div>', unsafe_allow_html=True)

    st.markdown('<div class="aero-card">', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Select PDF manual(s)",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="visible",
    )
    if uploaded:
        for f in uploaded:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"📄 **{f.name}** ({f.size // 1024} KB)")
            with col_b:
                if st.button(f"Upload", key=f"up_{f.name}", use_container_width=True):
                    with st.spinner(f"Uploading {f.name}…"):
                        result = api.upload_manual(
                            st.session_state.token, f.read(), f.name
                        )
                    if "message" in result:
                        st.success(result["message"])
                    else:
                        st.error(str(result))
    st.markdown("</div>", unsafe_allow_html=True)

    # existing manuals
    st.markdown('<div class="section-title" style="margin-top:1.5rem;">📚 Indexed Manuals</div>', unsafe_allow_html=True)
    info = api.list_manuals(st.session_state.token)
    manuals = info.get("manuals", [])
    total   = info.get("total_vectors", 0)

    st.metric("Total Indexed Vectors", total)
    if not manuals:
        st.info("No manuals indexed yet.")
    else:
        for m in manuals:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"<span class='src-chip' style='font-size:0.9rem;'>📖 {m}</span>", unsafe_allow_html=True)
            with c2:
                if st.button("🗑 Remove", key=f"del_{m}"):
                    result = api.delete_manual(st.session_state.token, m)
                    st.success(result.get("message", "Removed"))
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  HISTORY PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def show_history():
    st.markdown('<div class="section-title">📜 Query History</div>', unsafe_allow_html=True)

    history = api.get_history(st.session_state.token, limit=100)
    if not history:
        st.info("No queries yet.")
        return

    search = st.text_input("🔍 Filter history", placeholder="Search by keyword…")
    if search:
        history = [h for h in history if search.lower() in h.get("query","").lower()
                   or search.lower() in h.get("answer","").lower()]

    st.markdown(f"**{len(history)} record(s)**")
    for h in history:
        conf = h.get("confidence", 0)
        conf_pct = int(conf * 100)
        fb = h.get("feedback")
        fb_icon = " 👍" if fb == "up" else (" 👎" if fb == "down" else "")

        with st.expander(f"🕒 {h.get('timestamp','')[:19]}  |  {h.get('query','')[:70]}… {fb_icon}"):
            st.markdown(f"**👤 User:** {h.get('username','')}")
            st.markdown(f"**❓ Query:** {h.get('query','')}")
            st.markdown(f"**🤖 Answer:** {h.get('answer','')}")
            st.progress(conf)
            st.caption(f"Confidence: {conf_pct}%")
            srcs = h.get("sources", [])
            if srcs:
                st.markdown("**📎 Sources:**")
                for s in srcs:
                    st.markdown(
                        f"<span class='src-chip'>{s.get('manual','?')}</span>"
                        f"<span class='src-chip'>Page {s.get('page','?')}</span>",
                        unsafe_allow_html=True,
                    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def show_admin():
    st.markdown('<div class="section-title">📊 Admin Dashboard</div>', unsafe_allow_html=True)
    stats = api.get_stats(st.session_state.token)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Queries",    stats.get("total_queries", 0))
    c2.metric("👍 Thumbs Up",     stats.get("thumbs_up", 0))
    c3.metric("👎 Thumbs Down",   stats.get("thumbs_down", 0))
    c4.metric("Avg Confidence",   f"{int(stats.get('avg_confidence',0)*100)}%")

    info = api.list_manuals(st.session_state.token)
    st.metric("Indexed Vectors", info.get("total_vectors", 0))
    st.metric("Manuals Loaded",  len(info.get("manuals", [])))

    backend_ok = api.health()
    st.markdown(
        f"**Backend Status:** {'🟢 Online' if backend_ok else '🔴 Offline'}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  USER MANAGEMENT PAGE  (admin only)
# ═══════════════════════════════════════════════════════════════════════════════
def show_users():
    st.markdown('<div class="section-title">👤 Manage Users</div>', unsafe_allow_html=True)
    st.markdown('<div class="aero-card">', unsafe_allow_html=True)
    st.markdown("### ➕ Create New User")
    with st.form("create_user_form"):
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["engineer", "admin"])
        if st.form_submit_button("Create User", use_container_width=True):
            if new_user and new_pass:
                result = api.register(st.session_state.token, new_user, new_pass, new_role)
                if "username" in result:
                    st.success(f"✅ User '{new_user}' created as {new_role}")
                else:
                    st.error(result.get("detail", str(result)))
            else:
                st.warning("Please fill in username and password")
    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    if not st.session_state.token:
        show_login()
        return

    show_sidebar()

    page = st.session_state.page
    if page == "chat":
        show_chat()
    elif page == "history":
        show_history()
    elif page == "upload" and st.session_state.role == "admin":
        show_upload()
    elif page == "admin" and st.session_state.role == "admin":
        show_admin()
    elif page == "users" and st.session_state.role == "admin":
        show_users()
    else:
        show_chat()


if __name__ == "__main__":
    main()
