from datetime import datetime


def create_research_session(question):
    return {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "question": question,
        "created_at": datetime.now().isoformat(),

        "papers": [],
        "selected_papers": [],

        "evidence": [],
        "claims": [],
        "fact_checks": [],

        "final_answer": "",

        "sources": [],
        "limitations": [],

        "evidence_confidence": None,

        "status": "question"
    }


def update_session_status(session, status):

    valid_statuses = [
        "question",
        "searching",
        "sources_found",
        "retrieving_evidence",
        "analyzing",
        "fact_checking",
        "completed"
    ]

    if status not in valid_statuses:
        raise ValueError(
            f"Invalid research status: {status}"
        )

    session["status"] = status

    return session


def add_papers(session, papers):

    session["papers"] = papers

    update_session_status(
        session,
        "sources_found"
    )

    return session


def select_paper(session, paper):

    paper_id = (
        paper.get("id")
        or paper.get("url")
        or paper.get("title")
    )

    existing_ids = [
        selected.get("id")
        or selected.get("url")
        or selected.get("title")
        for selected in session["selected_papers"]
    ]

    if paper_id not in existing_ids:
        session["selected_papers"].append(paper)

    return session


def remove_selected_paper(session, paper):

    paper_id = (
        paper.get("id")
        or paper.get("url")
        or paper.get("title")
    )

    session["selected_papers"] = [
        selected
        for selected in session["selected_papers"]
        if (
            selected.get("id")
            or selected.get("url")
            or selected.get("title")
        ) != paper_id
    ]

    return session


def add_evidence(
    session,
    evidence_text,
    source,
    relevance=None
):

    evidence = {
        "text": evidence_text,
        "source": source,
        "relevance": relevance
    }

    session["evidence"].append(evidence)

    return session


def add_claim(
    session,
    claim_text,
    status="unverified",
    evidence=None
):

    valid_statuses = [
        "unverified",
        "supported",
        "partially_supported",
        "unsupported",
        "insufficient_evidence"
    ]

    if status not in valid_statuses:
        raise ValueError(
            f"Invalid claim status: {status}"
        )

    claim = {
        "claim": claim_text,
        "status": status,
        "evidence": evidence or []
    }

    session["claims"].append(claim)

    return session


def add_fact_check(
    session,
    claim,
    status,
    supporting_evidence=None,
    explanation=""
):

    valid_statuses = [
        "supported",
        "partially_supported",
        "unsupported",
        "insufficient_evidence"
    ]

    if status not in valid_statuses:
        raise ValueError(
            f"Invalid fact-check status: {status}"
        )

    result = {
        "claim": claim,
        "status": status,
        "supporting_evidence": (
            supporting_evidence or []
        ),
        "explanation": explanation
    }

    session["fact_checks"].append(result)

    return session


def set_final_answer(
    session,
    answer,
    sources=None,
    limitations=None,
    evidence_confidence=None
):

    session["final_answer"] = answer

    session["sources"] = (
        sources or []
    )

    session["limitations"] = (
        limitations or []
    )

    session["evidence_confidence"] = (
        evidence_confidence
    )

    update_session_status(
        session,
        "completed"
    )

    return session