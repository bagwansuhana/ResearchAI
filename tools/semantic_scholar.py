import requests

API_URL = "https://api.openalex.org/works"


def reconstruct_abstract(inverted_index):
    """
    Convert OpenAlex's inverted abstract index
    into a normal readable abstract.
    """

    if not inverted_index:
        return None

    words = []

    for word, positions in inverted_index.items():
        for position in positions:
            words.append((position, word))

    words.sort()

    return " ".join(word for _, word in words)


def search_papers(query, limit=5):

    params = {
        "search": query,
        "per-page": limit
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    papers = []

    for work in data.get("results", []):

        # -------------------------
        # AUTHORS
        # -------------------------

        authors = []

        for author in work.get("authorships", []):
            author_name = author.get("author", {}).get("display_name")

            if author_name:
                authors.append(author_name)

        # -------------------------
        # ABSTRACT
        # -------------------------

        abstract = reconstruct_abstract(
            work.get("abstract_inverted_index")
        )

        # -------------------------
        # OPEN ACCESS
        # -------------------------

        open_access = work.get("open_access") or {}

        is_open_access = open_access.get(
            "is_oa",
            False
        )

        # -------------------------
        # BEST OPEN ACCESS LOCATION
        # -------------------------

        oa_location = work.get("best_oa_location") or {}

        pdf_url = oa_location.get("pdf_url")

        landing_page = oa_location.get(
            "landing_page_url"
        )

        # -------------------------
        # PAPER URL
        # -------------------------

        url = (
            pdf_url
            or landing_page
            or work.get("doi")
            or work.get("id")
        )

        # -------------------------
        # STORE PAPER
        # -------------------------

        papers.append({

            "id": work.get("id"),

            "title": work.get("title"),

            "authors": authors,

            "year": work.get(
                "publication_year"
            ),

            "abstract": abstract,

            "url": url,

            "pdf_url": pdf_url,

            "landing_page_url": landing_page,

            "open_access": is_open_access,
             
            "locations": work.get(
                "locations",
                []
            ),

            "citationCount": work.get(
                "cited_by_count",
                0
            )
        })

    return papers