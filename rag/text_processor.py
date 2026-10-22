import re


def clean_text(text):
    """
    Clean retrieved academic text before chunking.
    """

    if not text:
        return ""

    # Normalize line breaks
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Remove excessive blank lines
    text = re.sub(
        r"\n\s*\n\s*\n+",
        "\n\n",
        text
    )

    # Remove common repository metadata
    metadata_patterns = [
        r"Downloaded from\s+https?://\S+",
        r"Kent Academic Repository",
        r"University of Kent's Academic Repository",
    ]

    for pattern in metadata_patterns:

        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE
        )

    return text.strip()


def split_into_sentences(text):
    """
    Split academic text into approximate sentences.
    """

    if not text:
        return []

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def create_chunks(
    text,
    chunk_size=1200,
    overlap=200
):
    """
    Split cleaned text into overlapping chunks.

    chunk_size:
        Approximate number of words per chunk.

    overlap:
        Number of words shared between
        consecutive chunks.
    """

    if not text:
        return []

    words = text.split()

    if not words:
        return []

    chunks = []

    start = 0
    chunk_number = 1

    while start < len(words):

        end = min(
            start + chunk_size,
            len(words)
        )

        chunk_words = words[
            start:end
        ]

        chunk_text = " ".join(
            chunk_words
        ).strip()

        if chunk_text:

            chunks.append({
                "chunk_id": chunk_number,
                "text": chunk_text,
                "start_word": start,
                "end_word": end,
            })

            chunk_number += 1

        if end >= len(words):
            break

        start = end - overlap

    return chunks


def process_paper_text(text):
    """
    Complete text-processing pipeline.

    Returns cleaned text and chunks.
    """

    cleaned = clean_text(
        text
    )

    chunks = create_chunks(
        cleaned
    )

    return {
        "cleaned_text": cleaned,
        "chunks": chunks,
        "character_count": len(cleaned),
        "chunk_count": len(chunks),
    }