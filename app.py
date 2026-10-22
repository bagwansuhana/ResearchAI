import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client

from tools.semantic_scholar import search_papers
from research_session import (
    create_research_session,
    update_session_status,
    add_papers,
)
from tools.paper_text import get_paper_text
from rag.text_processor import process_paper_text
from rag.evidence_retriever import retrieve_relevant_chunks
from rag.claim_extractor import extract_claims
from rag.fact_checker import fact_check_claims


# ============================================================
# SUPABASE CONNECTION
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )
    except Exception:
        supabase = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ResearchAI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# SUPABASE CONNECTION
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )
    except Exception as error:
        st.warning(
            "Supabase connection setup failed. "
            "Cloud features are currently unavailable."
        )
# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ResearchAI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)
if supabase is not None:
    st.sidebar.success("Supabase client initialized")
else:
    st.sidebar.info(
        "Guest mode: cloud storage is not connected."
    )

# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "Research",
    "papers": [],
    "current_query": "",
    "history": [],
    "saved_papers": [],
    "research_session": None,
    "selected_papers": [],
    "analysis_started": False,
    "auth_user": None,
    "auth_session": None,
    "auth_mode": "Login",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL
       ======================================================== */

    #MainMenu {
        visibility: hidden;
    }

    header {
        visibility: visible;
    }

    footer {
        visibility: hidden;
    }

    .stApp {
        background: #f7f8fa !important;
        color: #17191c !important;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* Force readable text regardless of Streamlit theme */

    .stApp p,
    .stApp span,
    .stApp label,
    .stApp div,
    .stApp li {
        color: #30343a;
    }

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
        color: #17191c !important;
    }

    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e3e6e9;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.35rem;
        padding-left: 1.15rem;
        padding-right: 1.15rem;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: #30343a;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #17191c !important;
    }

    section[data-testid="stSidebar"] .stButton button {
        background: transparent !important;
        border: none !important;
        color: #4b5563 !important;
        text-align: left !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        padding: 0.48rem 0.65rem !important;
        min-height: 0 !important;
        border-radius: 5px !important;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background: #f2f3f5 !important;
        color: #17191c !important;
    }

        /* Keep the sidebar collapse / reopen control visible */
    [data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }

    /* ========================================================
       INPUT
       ======================================================== */

    div[data-testid="stTextInput"] input {
        background: #ffffff !important;
        color: #17191c !important;
        border: 1px solid #cfd4da !important;
        border-radius: 6px !important;
        min-height: 45px !important;
        font-size: 0.92rem !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #858b93 !important;
        opacity: 1 !important;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #6b7280 !important;
        box-shadow: 0 0 0 1px #6b7280 !important;
    }

    /* ========================================================
       SEARCH BUTTON
       ======================================================== */

    div[data-testid="stFormSubmitButton"] button {
    background: #ffffff !important;
    color: #17191c !important;
    border: 1px solid #17191c !important;
    border-radius: 6px !important;
    min-height: 45px !important;
    font-weight: 600 !important;
    }

    div[data-testid="stFormSubmitButton"] button span {
     color: #17191c !important;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
    background: #f2f3f5 !important;
    color: #17191c !important;
    border-color: #17191c !important;
    }
    /* ========================================================
       NORMAL BUTTONS
       ======================================================== */

    .stButton button {
        color: #30343a !important;
        background: #ffffff !important;
        border: 1px solid #d8dce1 !important;
        border-radius: 5px !important;
    }

    .stButton button span {
        color: #30343a !important;
    }

    .stButton button:hover {
        border-color: #9ca3af !important;
        background: #f7f8fa !important;
    }

    /* ========================================================
       LINK BUTTONS
       ======================================================== */

    .stLinkButton a {
        color: #30343a !important;
        background: #ffffff !important;
        border: 1px solid #d8dce1 !important;
        border-radius: 5px !important;
        font-size: 0.78rem !important;
    }

    .stLinkButton a:hover {
        background: #f7f8fa !important;
        border-color: #9ca3af !important;
    }

    /* ========================================================
       EXPANDERS
       ======================================================== */

    div[data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid #e3e6e9 !important;
        border-radius: 6px !important;
    }

    div[data-testid="stExpander"] summary span {
        color: #4b5563 !important;
        font-size: 0.8rem !important;
    }

    /* ========================================================
       CHECKBOX
       ======================================================== */

    div[data-testid="stCheckbox"] label span {
        color: #30343a !important;
    }

    /* ========================================================
       ALERTS
       ======================================================== */

    div[data-testid="stAlert"] p {
        color: #30343a !important;
    }

    /* ========================================================
       CAPTIONS
       ======================================================== */

    [data-testid="stCaptionContainer"] p {
        color: #737982 !important;
        font-size: 0.78rem !important;
    }

    /* ========================================================
       CUSTOM UI
       ======================================================== */

    .eyebrow {
        color: #737982;
        font-size: 0.69rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }

    .page-subtitle {
        color: #626871;
        font-size: 0.91rem;
        line-height: 1.6;
        max-width: 720px;
        margin-top: -0.3rem;
    }

    .section-label {
        color: #737982;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .paper-number {
        color: #9aa0a8;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.08em;
    }

    .paper-title {
        color: #17191c;
        font-size: 0.98rem;
        font-weight: 650;
        line-height: 1.45;
        margin-top: 0.2rem;
    }

    .paper-authors {
        color: #626871;
        font-size: 0.8rem;
        line-height: 1.5;
        margin-top: 0.28rem;
    }

    .paper-meta {
        color: #858b93;
        font-size: 0.72rem;
        margin-top: 0.55rem;
    }

    .research-question {
        color: #17191c;
        font-size: 1.05rem;
        line-height: 1.55;
        font-weight: 550;
    }

    .answer-placeholder {
        color: #777e87;
        font-size: 0.88rem;
        line-height: 1.65;
    }

    .status-label {
        font-size: 0.7rem;
        font-weight: 750;
        letter-spacing: 0.07em;
    }

    .status-supported {
        color: #26734d;
    }

    .status-partial {
        color: #8a6418;
    }

    .status-unsupported {
        color: #9a3f3f;
    }

    .status-insufficient {
        color: #686f78;
    }

    .confidence-value {
        color: #17191c;
        font-size: 0.95rem;
        font-weight: 700;
    }

    .muted-line {
        color: #777e87;
        font-size: 0.8rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def paper_id(paper):
    return (
        paper.get("id")
        or paper.get("url")
        or paper.get("title")
        or ""
    )


def format_authors(authors):
    if not authors:
        return "Authors unavailable"

    names = []

    for author in authors:
        if isinstance(author, str):
            names.append(author)

        elif isinstance(author, dict):
            name = (
                author.get("display_name")
                or author.get("name")
            )

            if name:
                names.append(name)

    if not names:
        return "Authors unavailable"

    if len(names) > 4:
        return ", ".join(names[:4]) + " et al."

    return ", ".join(names)


def is_saved(paper):
    pid = paper_id(paper)

    return any(
        paper_id(saved) == pid
        for saved in st.session_state.saved_papers
    )


def toggle_saved(paper):
    pid = paper_id(paper)

    if is_saved(paper):
        st.session_state.saved_papers = [
            saved
            for saved in st.session_state.saved_papers
            if paper_id(saved) != pid
        ]
    else:
        st.session_state.saved_papers.append(paper)


def is_selected(paper):
    pid = paper_id(paper)

    return any(
        paper_id(selected) == pid
        for selected in st.session_state.selected_papers
    )


def toggle_selected(paper):
    pid = paper_id(paper)

    if is_selected(paper):
        st.session_state.selected_papers = [
            selected
            for selected in st.session_state.selected_papers
            if paper_id(selected) != pid
        ]
    else:
        st.session_state.selected_papers.append(paper)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## ResearchAI"
    )

    st.caption(
        "Evidence-grounded academic research"
    )

    st.divider()

    # Authentication
    st.markdown("### Account")

    if st.session_state.auth_user is None:

        st.session_state.auth_mode = st.radio(
            "Choose an option",
            ["Login", "Sign up"],
            horizontal=True,
            key="auth_mode_selector",
        )

        with st.form("auth_form"):
            email = st.text_input("Email")
            password = st.text_input(
                "Password",
                type="password",
            )

            submitted = st.form_submit_button(
                st.session_state.auth_mode,
                use_container_width=True,
            )

            if submitted:
                if supabase is None:
                    st.error(
                        "Supabase is not configured. "
                        "You can continue as a guest."
                    )

                elif not email.strip() or not password:
                    st.warning(
                        "Enter your email and password."
                    )

                else:
                    try:
                        if st.session_state.auth_mode == "Sign up":
                            response = supabase.auth.sign_up({
                                "email": email.strip(),
                                "password": password,
                            })
                        else:
                            response = supabase.auth.sign_in_with_password({
                                "email": email.strip(),
                                "password": password,
                            })

                        if response.user:
                            st.session_state.auth_user = response.user
                            st.session_state.auth_session = response.session

                            if response.session:
                                st.success("Account authenticated.")
                            else:
                                st.success(
                                    "Sign-up submitted. Check your email "
                                    "if confirmation is required."
                                )

                            st.rerun()

                    except Exception as e:
                        st.error(f"Authentication failed: {e}")

    else:
        st.success(
            f"Signed in: {st.session_state.auth_user.email}"
        )

        if st.button(
            "Log out",
            use_container_width=True,
        ):
            try:
                if supabase is not None:
                    supabase.auth.sign_out()
            finally:
                st.session_state.auth_user = None
                st.session_state.auth_session = None
                st.rerun()

    st.divider()

    if st.button(
        "Research",
        use_container_width=True,
    ):
        st.session_state.page = "Research"
        st.rerun()

    if st.button(
        f"Saved Papers  ({len(st.session_state.saved_papers)})",
        use_container_width=True,
    ):
        st.session_state.page = "Saved Papers"
        st.rerun()

    if st.button(
        f"Research History  ({len(st.session_state.history)})",
        use_container_width=True,
    ):
        st.session_state.page = "Research History"
        st.rerun()

    st.divider()

    if st.button(
        "How it works",
        use_container_width=True,
    ):
        st.session_state.page = "How it works"
        st.rerun()

    if st.button(
        "About",
        use_container_width=True,
    ):
        st.session_state.page = "About"
        st.rerun()


# ============================================================
# RESEARCH PAGE
# ============================================================

if st.session_state.page == "Research":

    # --------------------------------------------------------
    # RESEARCH HEADER
    # --------------------------------------------------------

    st.markdown(
        '<div class="eyebrow">ACADEMIC RESEARCH</div>',
        unsafe_allow_html=True,
    )

    st.title(
        "Find academic research"
    )

    st.markdown(
        """
        <div class="page-subtitle">
        Search scholarly literature using a natural-language
        research question and build an evidence-grounded
        research session.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")


    # --------------------------------------------------------
    # SEARCH BAR
    # --------------------------------------------------------

    with st.form("research_search"):

        search_col, button_col = st.columns(
            [6, 1],
            gap="small",
        )

        with search_col:

            query = st.text_input(
                "Research question",
                value=st.session_state.current_query,
                placeholder="What do you want to research?",
                label_visibility="collapsed",
            )

        with button_col:

            search_clicked = st.form_submit_button(
                "Search",
                use_container_width=True,
            )


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search_clicked:

        query = query.strip()

        if not query:

            st.error(
                "Enter a research question first."
            )

        else:

            try:

                session = create_research_session(
                    query
                )

                update_session_status(
                    session,
                    "searching"
                )

                st.session_state.research_session = session
                st.session_state.current_query = query
                st.session_state.selected_papers = []
                st.session_state.analysis_started = False

                with st.spinner(
                    "Searching academic literature..."
                ):

                    papers = search_papers(
                        query,
                        limit=5,
                    )

                add_papers(
                    session,
                    papers,
                )

                st.session_state.papers = papers

                if query not in st.session_state.history:
                    st.session_state.history.insert(
                        0,
                        query,
                    )

                st.rerun()

            except Exception as error:

                st.error(
                    f"Search failed: {error}"
                )


    # --------------------------------------------------------
    # INITIAL EMPTY STATE
    # --------------------------------------------------------

    if not st.session_state.papers:

        st.divider()

        st.markdown(
            '<div class="section-label">Research workspace</div>',
            unsafe_allow_html=True,
        )

        st.write("")

        st.markdown(
            """
            <div class="answer-placeholder">
            Enter a research question above to begin.
            </div>
            """,
            unsafe_allow_html=True,
        )


    # --------------------------------------------------------
    # SEARCH RESULTS
    # --------------------------------------------------------

    else:

        st.divider()

        st.markdown(
            '<div class="section-label">Research sources</div>',
            unsafe_allow_html=True,
        )

        st.write("")

        result_left, result_right = st.columns(
            [5, 2],
            gap="large",
        )

        with result_left:

            st.subheader(
                f"{len(st.session_state.papers)} sources found"
            )

            st.markdown(
                f"""
                <div class="research-question">
                {st.session_state.current_query}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with result_right:

            st.caption(
                "Select sources to use in the research session."
            )


        st.write("")


        # ----------------------------------------------------
        # PAPERS

        # ----------------------------------------------------

        for index, paper in enumerate(
            st.session_state.papers,
            start=1,
        ):

            with st.container(border=True):

                top_left, top_right = st.columns(
                    [6, 1],
                    gap="medium",
                )

                with top_left:

                    st.markdown(
                        f'<div class="paper-number">{index:02d}</div>',
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        f"""
                        <div class="paper-title">
                        {paper.get("title", "Untitled paper")}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        f"""
                        <div class="paper-authors">
                        {format_authors(paper.get("authors", []))}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    year = paper.get(
                        "year",
                        "Year unavailable",
                    )

                    citations = paper.get(
                        "citationCount",
                        0,
                    )

                    access = (
                        "Open access"
                        if paper.get("open_access")
                        else "Access varies"
                    )

                    st.markdown(
                        f"""
                        <div class="paper-meta">
                        {year}
                        &nbsp;&nbsp;·&nbsp;&nbsp;
                        {citations} citations
                        &nbsp;&nbsp;·&nbsp;&nbsp;
                        {access}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with top_right:

                    if is_selected(paper):

                        if st.button(
                            "✓ Selected",
                            key=f"selected_{paper_id(paper)}",
                            use_container_width=True,
                        ):
                            toggle_selected(paper)
                            st.rerun()

                    else:

                        if st.button(
                            "Select for analysis",
                            key=f"select_{paper_id(paper)}",
                            use_container_width=True,
                        ):
                            toggle_selected(paper)
                            st.rerun()


                action_left, action_mid, action_right = st.columns(
                    [1, 1.2, 4],
                    gap="small",
                )

                with action_left:

                    save_text = (
                        "★ Saved"
                        if is_saved(paper)
                        else "☆ Save"
                    )

                    if st.button(
                        save_text,
                        key=f"save_{paper_id(paper)}",
                    ):

                        toggle_saved(paper)
                        st.rerun()


                with action_mid:

                    url = paper.get("url")

                    if url:

                        st.link_button(
                            "View source",
                            url,
                        )


                with action_right:

                    abstract = paper.get("abstract")

                    if abstract:

                        with st.expander(
                            "Abstract"
                        ):

                            st.write(
                                abstract
                            )

                    else:

                        st.caption(
                            "Abstract unavailable."
                        )


        # ----------------------------------------------------
        # START RESEARCH SESSION
        # ----------------------------------------------------

        st.write("")

        selected_count = len(
            st.session_state.selected_papers
        )

        st.divider()

        session_left, session_mid, session_right = st.columns(
            [4.5, 1.5, 1.5],
            gap="medium",
        )

        with session_left:

            st.markdown(
                '<div class="section-label">Research session</div>',
                unsafe_allow_html=True,
            )

            st.caption(
                f"{selected_count} source(s) selected. "
                "These papers will be used for evidence analysis."
            )

        with session_mid:

            all_papers_selected = (
                len(st.session_state.papers) > 0
                and selected_count == len(st.session_state.papers)
            )

            if all_papers_selected:

                select_all = st.button(
                    "Deselect all",
                    use_container_width=True,
                )

            else:

                select_all = st.button(
                    "Select all",
                    use_container_width=True,
                )

        with session_right:

            start_analysis = st.button(
                "Continue to analysis",
                disabled=selected_count == 0,
                use_container_width=True,
            )

        if select_all:

            if all_papers_selected:

                st.session_state.selected_papers = []

            else:

                st.session_state.selected_papers = (
                    st.session_state.papers.copy()
                )

            st.rerun()

        if start_analysis:

            st.session_state.analysis_started = True

            with st.spinner("Retrieving paper text..."):

                retrieved_papers = []

                for paper in st.session_state.selected_papers:

                    result = get_paper_text(
                        paper
                    )

                    processed = None

                    if result["success"]:

                        processed = process_paper_text(
                            result["text"]
                        )

                    retrieved_papers.append({
                        "paper": paper,
                        "success": result["success"],
                        "text": result["text"],
                        "error": result["error"],
                        "source_url": result.get(
                            "source_url"
                        ),
                        "source_type": result.get(
                            "source_type"
                        ),
                        "cleaned_text": (
                            processed["cleaned_text"]
                            if processed
                            else None
                        ),
                        "chunks": (
                            processed["chunks"]
                            if processed
                            else []
                        ),
                        "chunk_count": (
                            processed["chunk_count"]
                            if processed
                            else 0
                        ),
                    })

                st.session_state.retrieved_papers = (
                    retrieved_papers
                )

                retrieval_success = sum(
                    1
                    for item in retrieved_papers
                    if item.get("success")
                )

                retrieval_total = len(retrieved_papers)

                if retrieval_success == 0:

                    st.warning(
                        "Readable full text could not be retrieved "
                        "from the selected sources."
                    )

                elif retrieval_success < retrieval_total:

                    st.caption(
                        f"Evidence retrieved from "
                        f"{retrieval_success} of "
                        f"{retrieval_total} selected sources."
                    )



                relevant_evidence = retrieve_relevant_chunks(
                    st.session_state.current_query,
                    retrieved_papers,
                    top_k=5,
                )

                st.session_state.relevant_evidence = (
                    relevant_evidence
                )

                # Extract factual claims from the retrieved evidence
               
                with st.spinner("Analyzing evidence..."):

                    claim_result = extract_claims(
                        st.session_state.current_query,
                        relevant_evidence,
                    )

                claims = claim_result.get(
                    "claims",
                    []
                )

                claim_extraction_success = claim_result.get(
                    "success",
                    False
                )

                claim_extraction_error = claim_result.get(
                    "error"
                )

                st.session_state.claims = claims
                st.session_state.claim_extraction_success = (
                    claim_extraction_success
                )
                st.session_state.claim_extraction_error = (
                    claim_extraction_error
                )

                # Fact-check extracted claims against the retrieved evidence
                if claims:
                    with st.spinner("Fact-checking claims..."):

                        fact_check_result = fact_check_claims(
                            st.session_state.current_query,
                            claims,
                            relevant_evidence,
                        )
                else:
                    fact_check_result = {
                        "success": False,
                        "fact_checks": [],
                        "error": "No claims were available for fact-checking."
                    }

                fact_checks = fact_check_result.get(
                    "fact_checks",
                    []
                )
                st.session_state.fact_checks = fact_checks
                st.session_state.fact_check_success = (
                    fact_check_result.get(
                        "success",
                        False
                    )
                )
                st.session_state.fact_check_error = (
                    fact_check_result.get(
                        "error"
                    )
                )

                # Show a user-friendly message only if analysis failed
                if (
                    not claim_extraction_success
                    and claim_extraction_error
                ):
                    st.caption(
                        "Evidence analysis could not be completed. "
                        "The retrieved evidence is still available below."
                    )

                if claims:
                    st.markdown("### Extracted claims")
                    for index, claim in enumerate(
                        claims,
                        start=1
                    ):
                        st.markdown(
                            f"**[{index}] {claim.get('claim', '')}**"
                        )

                        reason = claim.get(
                            "reason",
                            ""
                        )

                        if reason:
                            st.caption(reason)

                        evidence_ids = claim.get(
                            "evidence_ids",
                            []
                        )

                        if evidence_ids:
                            st.caption(
                                "Evidence: "
                                + ", ".join(
                                    str(item)
                                    for item in evidence_ids
                                )
                            )

                else:
                    st.caption(
                        "No claims were extracted from the available evidence."
                    )










                st.write("DEBUG SOURCE LOCATIONS")

                for item in retrieved_papers:

                    paper = item["paper"]

                    st.write({
                        "title": paper.get("title"),
                        "pdf_url": paper.get("pdf_url"),
                        "landing_page_url": paper.get(
                            "landing_page_url"
                        ),
                        "locations": paper.get(
                            "locations",
                            []
                        ),
                    })

                st.session_state.analysis_text_ready = True

            st.rerun()

        # ----------------------------------------------------
        # ANALYSIS WORKSPACE
        # ----------------------------------------------------

        if st.session_state.analysis_started:

            st.divider()

            st.markdown(
                '<div class="section-label">Research session</div>',
                unsafe_allow_html=True,
            )

            st.write("")

            st.subheader(
                "Research question"
            )

            st.markdown(
                f"""
                <div class="research-question">
                {st.session_state.current_query}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")


            # =================================================
            # SOLUTION / ANSWER
            # =================================================

            st.divider()

            st.markdown(
                '<div class="section-label">Evidence retrieval</div>',
                unsafe_allow_html=True,
            )

            retrieved_papers = st.session_state.get(
                "retrieved_papers",
                [],
            )

            successful_papers = [
                item
                for item in retrieved_papers
                if item.get("success")
            ]

            failed_papers = [
                item
                for item in retrieved_papers
                if not item.get("success")
            ]

            st.caption(
                f"{len(successful_papers)} of "
                f"{len(retrieved_papers)} selected source(s) "
                "have readable full text."
            )

            if successful_papers:

                for index, item in enumerate(
                    successful_papers,
                    start=1,
                ):

                    paper = item["paper"]
                    text = item["text"]

                    with st.container(border=True):

                        st.markdown(
                            f"**[{index}] {paper.get('title', 'Untitled paper')}**"
                        )

                        source_type = item.get(
                            "source_type",
                            "unknown"
                        )

                        source_label = {
                            "pdf": "Open-access PDF",
                            "html": "Open-access HTML",
                        }.get(
                            source_type,
                            "Full text"
                        )

                        chunk_count = item.get(
                            "chunk_count",
                            0
                        )

                        st.caption(
                            f"{len(text):,} characters retrieved · "
                            f"{source_label} · "
                            f"{chunk_count} evidence chunks"
                        )

                        with st.expander("View retrieved text"):

                            st.text(
                                text[:5000]
                            )

                            if len(text) > 5000:
                                st.caption(
                                    "Showing the first 5,000 characters."
                                )

            st.markdown(
                '<div class="section-label">Relevant evidence</div>',
                unsafe_allow_html=True,
            )

            relevant_evidence = st.session_state.get(
                "relevant_evidence",
                []
            )

            if relevant_evidence:

                with st.expander(
                    f"Retrieved evidence · {len(relevant_evidence)} passage(s)",
                    expanded=False,
                ):

                    for index, evidence in enumerate(
                        relevant_evidence,
                        start=1,
                    ):

                        paper = evidence.get(
                            "paper",
                            {}
                        )

                        st.markdown(
                            f"**[{index}] "
                            f"{paper.get('title', 'Untitled paper')}**"
                        )

                        st.caption(
                            f"Evidence passage "
                            f"{evidence.get('chunk_id')}"
                        )

                        st.write(
                            evidence.get(
                                "text",
                                ""
                            )
                        )

                        if index < len(relevant_evidence):
                            st.divider()

            else:

                st.caption(
                    "No relevant evidence could be retrieved "
                    "from the readable sources."
                )


            # =================================================
            # EVIDENCE ASSESSMENT
            # =================================================

            st.write("")
            st.divider()

            st.markdown(
                '<div class="section-label">Evidence assessment</div>',
                unsafe_allow_html=True,
            )

            st.write("")

            fact_checks = st.session_state.get(
                "fact_checks",
                []
            )

            fact_check_success = st.session_state.get(
                "fact_check_success",
                False
            )

            fact_check_error = st.session_state.get(
                "fact_check_error"
            )


            if fact_checks:

                status_labels = {
                    "supported": "SUPPORTED",
                    "partially_supported": "PARTIALLY SUPPORTED",
                    "unsupported": "UNSUPPORTED",
                    "insufficient_evidence": "INSUFFICIENT EVIDENCE",
                }

                status_classes = {
                    "supported": "status-supported",
                    "partially_supported": "status-partial",
                    "unsupported": "status-unsupported",
                    "insufficient_evidence": "status-insufficient",
                }

                for index, result in enumerate(
                    fact_checks,
                    start=1,
                ):

                    status = result.get(
                        "status",
                        "insufficient_evidence",
                    )

                    label = status_labels.get(
                        status,
                        "INSUFFICIENT EVIDENCE",
                    )

                    css_class = status_classes.get(
                        status,
                        "status-insufficient",
                    )

                    claim = result.get(
                        "claim",
                        "",
                    )

                    explanation = result.get(
                        "explanation",
                        "",
                    )

                    evidence_ids = result.get(
                        "evidence_ids",
                        [],
                    )

                    st.markdown(
                        f'''
                        <div class="claim-result">
                            <div class="status-label {css_class}">
                                {index}. {label}
                            </div>
                        </div>
                        ''',
                        unsafe_allow_html=True,
                    )

                    if claim:
                        st.markdown(
                            f"**{claim}**"
                        )

                    if explanation:
                        st.caption(
                            explanation
                        )

                    if evidence_ids:
                        st.caption(
                            "Evidence: "
                            + ", ".join(
                                str(item)
                                for item in evidence_ids
                            )
                        )

                    if index < len(fact_checks):
                        st.write("")

            elif fact_check_error:
                st.caption(
                    "Evidence assessment could not be completed "
                    "because the analysis service was temporarily unavailable."
                )

            else:
                st.caption(
                    "No claim-level assessment could be generated "
                    "from the available evidence."
                )


            # =================================================
            # CONCLUSION
            # =================================================

            st.write("")
            st.divider()

            st.markdown(
                '<div class="section-label">Conclusion</div>',
                unsafe_allow_html=True,
            )

            st.write("")

            fact_checks = st.session_state.get(
                "fact_checks",
                [],
            )

            if fact_checks:
                supported_count = sum(
                    1
                    for item in fact_checks
                    if item.get("status") == "supported"
                )
                partial_count = sum(
                    1
                    for item in fact_checks
                    if item.get("status") == "partially_supported"
                )
                unsupported_count = sum(
                    1
                    for item in fact_checks
                    if item.get("status") == "unsupported"
                )
                insufficient_count = sum(
                    1
                    for item in fact_checks
                    if item.get("status") == "insufficient_evidence"
                )
                total_claims = len(fact_checks)

                if supported_count == total_claims and total_claims > 0:
                    conclusion = (
                        "The available evidence consistently supports the claims "
                        "evaluated for this research question."
                    )
                elif supported_count > 0 and (
                    partial_count > 0 or insufficient_count > 0
                ):
                    conclusion = (
                        "The available evidence provides support for the research "
                        "question, but some claims are only partially supported or "
                        "require additional evidence."
                    )
                elif partial_count > 0 and unsupported_count == 0:
                    conclusion = (
                        "The available evidence provides partial support for the "
                        "research question, but it is not sufficient to establish "
                        "all claims with confidence."
                    )
                elif unsupported_count > 0 and supported_count == 0:
                    conclusion = (
                        "The available evidence does not provide sufficient support "
                        "for the claims evaluated. Additional or more relevant "
                        "sources are needed."
                    )
                else:
                    conclusion = (
                        "The available evidence is insufficient to reach a reliable "
                        "conclusion."
                    )

                st.markdown(
                    f'<div class="answer-placeholder">{conclusion}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption(
                    "A conclusion will be generated once the available evidence "
                    "has been assessed."
                )

            # =================================================
            # EVIDENCE CONFIDENCE
            # =================================================

            st.write("")
            st.divider()

            confidence_left, confidence_right = st.columns(
                [3, 7],
                gap="large",
            )

            with confidence_left:

                st.markdown(
                    '<div class="section-label">Evidence Confidence</div>',
                    unsafe_allow_html=True,
                )

                st.write("")

                if fact_checks:
                    total_claims = len(fact_checks)
                    supported_count = sum(
                        1
                        for item in fact_checks
                        if item.get("status") == "supported"
                    )
                    partial_count = sum(
                        1
                        for item in fact_checks
                        if item.get("status") == "partially_supported"
                    )
                    unsupported_count = sum(
                        1
                        for item in fact_checks
                        if item.get("status") == "unsupported"
                    )
                    insufficient_count = sum(
                        1
                        for item in fact_checks
                        if item.get("status") == "insufficient_evidence"
                    )

                    score = (
                        supported_count * 1.0 + partial_count * 0.5
                    ) / total_claims

                    if unsupported_count > 0:
                        confidence = "Low"
                    elif insufficient_count > 0:
                        confidence = "Moderate"
                    elif score >= 0.75:
                        confidence = "High"
                    elif score >= 0.50:
                        confidence = "Moderate"
                    else:
                        confidence = "Low"

                    st.markdown(
                        f'<div class="confidence-value">{confidence}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="confidence-value">Not assessed</div>',
                        unsafe_allow_html=True,
                    )

            with confidence_right:

                st.caption(
                    "Evidence Confidence describes the strength "
                    "and consistency of the available evidence."
                )


            # =================================================
            # SOURCES
            # =================================================

            st.divider()

            st.markdown(
                '<div class="section-label">Sources</div>',
                unsafe_allow_html=True,
            )

            st.write("")

            for index, paper in enumerate(
                st.session_state.selected_papers,
                start=1,
            ):

                source_title = paper.get(
                    "title",
                    "Untitled paper",
                )

                source_year = paper.get(
                    "year",
                    "Year unavailable",
                )

                source_url = paper.get("url")

                st.markdown(
                    f"**[{index}] {source_title}**"
                )

                st.caption(
                    f"{format_authors(paper.get('authors', []))} · "
                    f"{source_year}"
                )

                if source_url:
                    st.link_button(
                        "Open source",
                        source_url,
                        key=f"analysis_source_{index}",
                    )


            # =================================================
            # LIMITATIONS
            # =================================================

            st.divider()

            st.markdown(
                '<div class="section-label">Limitations</div>',
                unsafe_allow_html=True,
            )

            st.write("")

            limitations = []

            retrieved_papers = st.session_state.get(
                "retrieved_papers",
                []
            )

            selected_papers = st.session_state.get(
                "selected_papers",
                []
            )

            retrieval_success = sum(
                1
                for item in retrieved_papers
                if item.get("success")
            )

            retrieval_total = len(retrieved_papers)

            if retrieval_total == 0:

                limitations.append(
                    "No readable full-text evidence was retrieved "
                    "from the selected sources."
                )

            elif retrieval_success < retrieval_total:

                limitations.append(
                    f"Readable full text was retrieved from "
                    f"{retrieval_success} of {retrieval_total} "
                    "selected sources."
                )

            if selected_papers:

                limitations.append(
                    "The analysis is limited to the academic "
                    "sources selected for this research session."
                )

            limitations.append(
                "Evidence quality and relevance may vary "
                "between sources."
            )

            fact_checks = st.session_state.get(
                "fact_checks",
                []
            )

            if any(
                item.get("status") in [
                    "partially_supported",
                    "insufficient_evidence",
                ]
                for item in fact_checks
            ):

                limitations.append(
                    "Some claims could not be fully established "
                    "from the available evidence."
                )

            if any(
                item.get("status") == "unsupported"
                for item in fact_checks
            ):

                limitations.append(
                    "Some extracted claims were not supported "
                    "by the retrieved evidence."
                )

            for limitation in limitations:

                st.markdown(
                    f"- {limitation}"
                )


# ============================================================
# SAVED PAPERS
# ============================================================

elif st.session_state.page == "Saved Papers":

    st.markdown(
        '<div class="eyebrow">RESEARCH COLLECTION</div>',
        unsafe_allow_html=True,
    )

    st.title(
        "Saved Papers"
    )

    st.markdown(
        """
        <div class="page-subtitle">
        Papers saved for later review and analysis.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if not st.session_state.saved_papers:

        st.markdown(
            '<div class="answer-placeholder">No saved papers yet.</div>',
            unsafe_allow_html=True,
        )

    else:

        for index, paper in enumerate(
            st.session_state.saved_papers,
            start=1,
        ):

            with st.container(border=True):

                st.markdown(
                    f'<div class="paper-number">{index:02d}</div>',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f"""
                    <div class="paper-title">
                    {paper.get("title", "Untitled paper")}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f"""
                    <div class="paper-authors">
                    {format_authors(paper.get("authors", []))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                url = paper.get("url")

                if url:
                    st.link_button(
                        "View source",
                        url,
                        key=f"saved_source_{index}",
                    )

                if st.button(
                    "Remove",
                    key=f"remove_saved_{index}",
                ):

                    st.session_state.saved_papers.pop(index - 1)
                    st.rerun()


# ============================================================
# RESEARCH HISTORY
# ============================================================

elif st.session_state.page == "Research History":

    st.markdown(
        '<div class="eyebrow">RESEARCH HISTORY</div>',
        unsafe_allow_html=True,
    )

    st.title(
        "Research History"
    )

    st.markdown(
        """
        <div class="page-subtitle">
        Research questions searched during this session.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if not st.session_state.history:

        st.markdown(
            '<div class="answer-placeholder">No research history yet.</div>',
            unsafe_allow_html=True,
        )

    else:

        for index, query in enumerate(
            st.session_state.history,
            start=1,
        ):

            with st.container(border=True):

                st.markdown(
                    f'<div class="paper-number">{index:02d}</div>',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f"""
                    <div class="paper-title">
                    {query}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ============================================================
# HOW IT WORKS
# ============================================================

elif st.session_state.page == "How it works":

    st.markdown(
        '<div class="eyebrow">RESEARCH WORKFLOW</div>',
        unsafe_allow_html=True,
    )

    st.title(
        "How ResearchAI works"
    )

    st.markdown(
        """
        <div class="page-subtitle">
        ResearchAI connects a research question with academic
        evidence and a traceable conclusion.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    steps = [
        (
            "01",
            "Research question",
            "The user asks a natural-language research question.",
        ),
        (
            "02",
            "Academic sources",
            "Relevant scholarly literature is retrieved.",
        ),
        (
            "03",
            "Evidence retrieval",
            "Accessible full-text sources are processed to find relevant evidence.",
        ),
        (
            "04",
            "Evidence analysis",
            "Retrieved evidence is compared against individual claims.",
        ),
        (
            "05",
            "Fact checking",
            "Claims are classified according to the available evidence.",
        ),
        (
            "06",
            "Final research report",
            "The system produces an answer with sources, limitations, and Evidence Confidence.",
        ),
    ]

    for number, title, description in steps:

        st.markdown(
            f"### {number}  {title}"
        )

        st.write(
            description
        )

        if number != "06":
            st.write("")


    st.divider()

    st.markdown(
        '<div class="section-label">Evidence Confidence</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    st.write(
        "**High** — strong and consistent evidence."
    )

    st.write(
        "**Moderate** — evidence supports the conclusion but has limitations."
    )

    st.write(
        "**Low** — evidence is limited, conflicting, or only partially relevant."
    )

    st.write(
        "**Insufficient** — there is not enough reliable evidence to conclude."
    )


# ============================================================
# ABOUT
# ============================================================

elif st.session_state.page == "About":

    st.markdown(
        '<div class="eyebrow">ABOUT</div>',
        unsafe_allow_html=True,
    )

    st.title(
        "ResearchAI"
    )

    st.markdown(
        """
        <div class="page-subtitle">
        An evidence-grounded academic research assistant for
        discovering literature, retrieving evidence, evaluating
        claims, and producing traceable research conclusions.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        '<div class="section-label">Purpose</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    st.write(
        "ResearchAI is designed to go beyond simply generating "
        "an answer. The system connects important claims with "
        "retrieved academic evidence."
    )

    st.divider()

    st.markdown(
        '<div class="section-label">Final research output</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    st.write(
        "A completed research session will contain:"
    )

    st.write(
        "- Solution / Answer"
    )

    st.write(
        "- Evidence Assessment"
    )

    st.write(
        "- Supported claims"
    )

    st.write(
        "- Partially supported claims"
    )

    st.write(
        "- Unsupported claims"
    )

    st.write(
        "- Insufficient evidence"
    )

    st.write(
        "- Conclusion"
    )

    st.write(
        "- Sources"
    )

    st.write(
        "- Limitations"
    )

    st.write(
        "- Evidence Confidence"
    )

    st.divider()

    st.markdown(
        '<div class="section-label">Current implementation</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    st.write(
        "The current version uses OpenAlex for academic "
        "literature discovery and retrieves available metadata, "
        "abstracts, citation counts, and open-access information."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "ResearchAI · Evidence-grounded academic research"
)