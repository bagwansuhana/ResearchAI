import json
import time

from google.genai import errors

from agents.gemini_client import get_gemini_client


MODEL_NAME = "gemini-3.8-flash"


def extract_claims(question, relevant_evidence):
    """
    Extract factual claims from the supplied evidence.

    Returns:
        {
            "success": bool,
            "claims": list,
            "error": str | None
        }

    Gemini is instructed to use only the supplied
    evidence and not introduce outside information.
    """

    if not relevant_evidence:
        return {
            "success": False,
            "claims": [],
            "error": "No relevant evidence was available."
        }

    evidence_text = []

    for index, item in enumerate(
        relevant_evidence[:3],
        start=1
    ):
        paper = item.get(
            "paper",
            {}
        )

        title = paper.get(
            "title",
            "Unknown source"
        )

        chunk_id = item.get(
            "chunk_id",
            "?"
        )

        text = item.get(
            "text",
            ""
        )

        # Keep the prompt reasonably sized.
        text = text[:2500]

        evidence_text.append(
            f"""
EVIDENCE {index}

Source: {title}
Chunk: {chunk_id}

Text:
{text}
"""
        )

    evidence_block = "\n".join(
        evidence_text
    )

    prompt = f"""
You are an academic evidence analysis assistant.

Research question:
{question}

Your task is to extract factual claims from
the supplied research evidence.

STRICT RULES:

1. Use ONLY the evidence provided below.
2. Do NOT use outside knowledge.
3. Do NOT invent facts.
4. Do NOT add unsupported information.
5. Each claim must be traceable to one or more
   supplied evidence passages.
6. Keep claims concise and precise.
7. Do not make a stronger claim than the evidence supports.
8. If the evidence is too weak to form a reliable
   factual claim, do not create one.

Return ONLY valid JSON in this exact structure:

{{
  "claims": [
    {{
      "claim": "A concise factual claim.",
      "evidence_ids": [1],
      "reason": "Brief explanation based only on the evidence."
    }}
  ]
}}

Research question:
{question}

Provided evidence:
{evidence_block}
"""

    client = None

    try:

        client = get_gemini_client()

        # Retry temporary server failures.
        for attempt in range(3):

            try:

                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json"
                    }
                )

                if not response.text:
                    return {
                        "success": False,
                        "claims": [],
                        "error": "Gemini returned an empty response."
                    }

                result = json.loads(
                    response.text
                )

                claims = result.get(
                    "claims",
                    []
                )

                if not isinstance(
                    claims,
                    list
                ):
                    return {
                        "success": False,
                        "claims": [],
                        "error": "Gemini returned an invalid claim format."
                    }

                cleaned_claims = []

                for claim in claims:

                    if not isinstance(
                        claim,
                        dict
                    ):
                        continue

                    claim_text = claim.get(
                        "claim",
                        ""
                    ).strip()

                    if not claim_text:
                        continue

                    evidence_ids = claim.get(
                        "evidence_ids",
                        []
                    )

                    reason = claim.get(
                        "reason",
                        ""
                    ).strip()

                    cleaned_claims.append({
                        "claim": claim_text,
                        "evidence_ids": evidence_ids,
                        "reason": reason,
                    })

                return {
                    "success": True,
                    "claims": cleaned_claims,
                    "error": None
                }

            except errors.ServerError as error:

                if attempt < 2:
                    time.sleep(
                        2 ** attempt
                    )
                    continue

                return {
                    "success": False,
                    "claims": [],
                    "error": (
                       f"Gemini server error: {error} "
                    )
                }

            except errors.APIError as error:

                return {
                    "success": False,
                    "claims": [],
                    "error": (
                        f"Gemini API error: {error}"
                    )
                }

            except json.JSONDecodeError:

                return {
                    "success": False,
                    "claims": [],
                    "error": (
                        "Gemini returned an invalid JSON response."
                    )
                }

    except Exception as error:

        return {
            "success": False,
            "claims": [],
            "error": str(error)
        }