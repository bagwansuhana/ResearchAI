import io
import re

import requests
from bs4 import BeautifulSoup # type: ignore
from pypdf import PdfReader


HEADERS = {
    "User-Agent": "ResearchAI/1.0"
}


def download_content(url):
    if not url:
        return None

    try:
        response = requests.get(
            url,
            timeout=30,
            headers=HEADERS,
            allow_redirects=True,
        )

        response.raise_for_status()

        return response

    except requests.RequestException:
        return None


def extract_pdf_text(pdf_bytes):
    if not pdf_bytes:
        return None

    try:
        reader = PdfReader(
            io.BytesIO(pdf_bytes)
        )

        pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

        full_text = "\n\n".join(pages).strip()

        if len(full_text) < 1000:
            return None

        return full_text

    except Exception:
        return None


def try_pdf_url(url):
    response = download_content(url)

    if not response:
        return None

    content_type = response.headers.get(
        "content-type",
        ""
    ).lower()

    clean_url = url.lower().split("?")[0]

    looks_like_pdf = (
        "application/pdf" in content_type
        or clean_url.endswith(".pdf")
    )

    if not looks_like_pdf:
        return None

    return extract_pdf_text(
        response.content
    )


def clean_text(text):
    if not text:
        return None

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n\s*\n\s*\n+",
        "\n\n",
        text
    )

    text = text.strip()

    return text


def looks_like_full_text(text):
    """
    Determine whether extracted HTML text
    looks like actual research content rather
    than a repository metadata page.
    """

    if not text:
        return False

    if len(text) < 3000:
        return False

    lower_text = text.lower()

    research_indicators = [
        "introduction",
        "methodology",
        "methods",
        "results",
        "discussion",
        "conclusion",
        "references",
    ]

    indicator_count = sum(
        1
        for indicator in research_indicators
        if indicator in lower_text
    )

    # A genuine article should contain
    # several research-section indicators.

    if indicator_count < 3:
        return False

    metadata_terms = [
        "research output",
        "fingerprint",
        "cite this",
        "bibtex",
        "projects per year",
    ]

    metadata_count = sum(
        1
        for term in metadata_terms
        if term in lower_text
    )

    # If the page is dominated by repository
    # metadata, do not treat it as evidence.

    if metadata_count >= 3 and indicator_count < 5:
        return False

    return True


def extract_html_text(html):
    if not html:
        return None

    try:
        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        for element in soup(
            [
                "script",
                "style",
                "noscript",
                "nav",
                "header",
                "footer",
                "aside",
                "form",
            ]
        ):
            element.decompose()

        # Prefer article content.

        article = soup.find("article")

        if article:

            text = article.get_text(
                separator="\n"
            )

        else:

            main = soup.find("main")

            if main:

                text = main.get_text(
                    separator="\n"
                )

            else:

                text = soup.get_text(
                    separator="\n"
                )

        text = clean_text(text)

        if not text:
            return None

        return text

    except Exception:
        return None


def try_html_url(url):
    response = download_content(url)

    if not response:
        return None

    content_type = response.headers.get(
        "content-type",
        ""
    ).lower()

    if (
        "text/html" not in content_type
        and "application/xhtml" not in content_type
    ):
        return None

    return extract_html_text(
        response.text
    )


def collect_pdf_urls(paper):
    urls = []

    if paper.get("pdf_url"):
        urls.append(
            paper.get("pdf_url")
        )

    for location in paper.get(
        "locations",
        []
    ):

        if not location:
            continue

        pdf_url = location.get(
            "pdf_url"
        )

        if (
            pdf_url
            and pdf_url not in urls
        ):
            urls.append(pdf_url)

    return urls


def collect_html_urls(paper):
    urls = []

    if paper.get("landing_page_url"):
        urls.append(
            paper.get("landing_page_url")
        )

    for location in paper.get(
        "locations",
        []
    ):

        if not location:
            continue

        landing_url = location.get(
            "landing_page_url"
        )

        if (
            landing_url
            and landing_url not in urls
        ):
            urls.append(landing_url)

    return urls


def get_paper_text(paper):

    # --------------------------------------------------
    # 1. TRY OPEN-ACCESS PDFs
    # --------------------------------------------------

    pdf_urls = collect_pdf_urls(
        paper
    )

    for pdf_url in pdf_urls:

        text = try_pdf_url(
            pdf_url
        )

        if text:

            return {
                "success": True,
                "text": text,
                "source_url": pdf_url,
                "source_type": "pdf",
                "error": None
            }

    # --------------------------------------------------
    # 2. TRY OPEN-ACCESS HTML
    # --------------------------------------------------

    html_urls = collect_html_urls(
        paper
    )

    for html_url in html_urls:

        text = try_html_url(
            html_url
        )

        if text:

            return {
                "success": True,
                "text": text,
                "source_url": html_url,
                "source_type": "html",
                "error": None
            }

    # --------------------------------------------------
    # 3. NOTHING USABLE
    # --------------------------------------------------

    if not pdf_urls and not html_urls:

        return {
            "success": False,
            "text": None,
            "source_url": None,
            "source_type": None,
            "error": (
                "No publicly accessible "
                "full-text source was found."
            )
        }

    return {
        "success": False,
        "text": None,
        "source_url": None,
        "source_type": None,
        "error": (
            "Publicly accessible sources were "
            "found, but readable research full "
            "text could not be retrieved."
        )
    }