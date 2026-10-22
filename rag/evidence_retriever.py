from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def retrieve_relevant_chunks(
    question,
    retrieved_papers,
    top_k=5,
):
    """
    Retrieve the most relevant evidence chunks
    for a research question using TF-IDF
    and cosine similarity.
    """

    candidates = []

    for paper_index, item in enumerate(
        retrieved_papers,
        start=1,
    ):

        if not item.get("success"):
            continue

        paper = item.get(
            "paper",
            {}
        )

        chunks = item.get(
            "chunks",
            []
        )

        for chunk in chunks:

            chunk_text = chunk.get(
                "text",
                ""
            )

            if not chunk_text.strip():
                continue

            candidates.append({
                "paper_index": paper_index,
                "paper": paper,
                "chunk_id": chunk.get(
                    "chunk_id"
                ),
                "text": chunk_text,
            })

    if not candidates:
        return []

    documents = [
        question
    ]

    documents.extend(
        candidate["text"]
        for candidate in candidates
    )

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_df=0.95,
    )

    matrix = vectorizer.fit_transform(
        documents
    )

    question_vector = matrix[0]

    chunk_vectors = matrix[1:]

    scores = cosine_similarity(
        question_vector,
        chunk_vectors
    )[0]

    results = []

    for candidate, score in zip(
        candidates,
        scores
    ):

        result = candidate.copy()

        result["score"] = float(
            score
        )

        results.append(
            result
        )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:top_k]