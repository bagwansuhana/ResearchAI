import json
import time

from google.genai import errors

from agents.gemini_client import get_gemini_client


MODEL_NAME = "gemini-3.8-flash"


VALID_STATUSES = [
    "supported",
    "partially_supported",
    "unsupported",
    "insufficient_evidence",
]


def fact_check_claims(
    question,
    claims,
    relevant_evidence,
):
    """
    Evaluate extracted claims against the retrieved evidence.

    Returns:
        {
            "success": bool,
            "fact_checks": list,
            "error": str | None
        }

    The model is instructed to use only the supplied
    evidence and to make conservative assessments.
    """

    if not claims:

        return {
            "success": False,
            "fact_checks": [],
            "error": "No claims were available for fact-checking."
        }

    if not relevant_evidence:

        return {
            "success": False,
            "fact_checks": [],
            "error": "No relevant evidence was available."
        }


    # ---------------------------------------------------------
    # Prepare evidence
    # ---------------------------------------------------------

    evidence_sections = []

    for index, item in enumerate(
        relevant_evidence[:3],  
        start=1,
    ):

        paper = item.get(
            "paper",
            {},
        )

        title = paper.get(
            "title",
            "Unknown source",
        )

        chunk_id = item.get(
            "chunk_id",
            "?",
        )

        text = item.get(
            "text",
            "",
        )

        text = text[:2500]

        evidence_sections.append(
            f"""
EVIDENCE {index}

Source: {title}
Chunk: {chunk_id}

Text:
{text}
"""
        )


    evidence_block = "\n".join(
        evidence_sections
    )


    # ---------------------------------------------------------
    # Prepare claims
    # ---------------------------------------------------------

    claims_block = []

    for index, claim in enumerate(
        claims,
        start=1,
    ):

        claims_block.append(
            f"""
CLAIM {index}

Claim:
{claim.get("claim", "")}

Claim evidence references:
{claim.get("evidence_ids", [])}

Extraction reason:
{claim.get("reason", "")}
"""
        )


    claims_text = "\n".join(
        claims_block
    )


    # ---------------------------------------------------------
    # Fact-checking prompt
    # ---------------------------------------------------------

    prompt = f"""
You are an academic evidence verification assistant.

Research question:
{question}

Your task is to evaluate each extracted claim
against the supplied research evidence.

IMPORTANT RULES:

1. Use ONLY the supplied evidence.
2. Do NOT use outside knowledge.
3. Do NOT invent facts.
4. Do NOT assume that a claim is true because
   it sounds scientifically reasonable.
5. Be conservative.
6. Every assessment must be traceable to
   the supplied evidence.
7. If evidence is weak or incomplete, prefer
   insufficient_evidence or partially_supported.

For every claim, assign exactly ONE status:

supported
partially_supported
unsupported
insufficient_evidence

Definitions:

SUPPORTED:
The supplied evidence directly supports the
claim as stated.

PARTIALLY_SUPPORTED:
The evidence supports an important part of
the claim but does not fully establish it.

UNSUPPORTED:
The supplied evidence does not support the
claim, or the evidence contradicts it.

INSUFFICIENT_EVIDENCE:
There is not enough reliable evidence to
determine whether the claim is supported.

Return ONLY valid JSON in this exact structure:

{{
  "fact_checks": [
    {{
      "claim": "The exact claim being evaluated.",
      "status": "supported",
      "evidence_ids": [1],
      "explanation": "Brief explanation based only on the supplied evidence."
    }}
  ]
}}

Claims:

{claims_text}

Evidence:

{evidence_block}
"""


    # ---------------------------------------------------------
    # Gemini request with retry
    # ---------------------------------------------------------

    try:

        client = get_gemini_client()

        for attempt in range(3):

            try:

                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json"
                    },
                )

                if not response.text:

                    return {
                        "success": False,
                        "fact_checks": [],
                        "error": (
                            "Gemini returned an empty response."
                            f"{error}"
                        )
                    }


                result = json.loads(
                    response.text
                )

                fact_checks = result.get(
                    "fact_checks",
                    [],
                )

                if not isinstance(
                    fact_checks,
                    list,
                ):

                    return {
                        "success": False,
                        "fact_checks": [],
                        "error": (
                            "Gemini returned an invalid "
                            "fact-check format."
                        )
                    }


                # -------------------------------------------------
                # Validate and clean model output
                # -------------------------------------------------

                cleaned_results = []

                for item in fact_checks:

                    if not isinstance(
                        item,
                        dict,
                    ):
                        continue


                    claim_text = item.get(
                        "claim",
                        "",
                    )

                    if not isinstance(
                        claim_text,
                        str,
                    ):

                        claim_text = str(
                            claim_text
                        )


                    status = item.get(
                        "status",
                        "insufficient_evidence",
                    )

                    if status not in VALID_STATUSES:

                        status = (
                            "insufficient_evidence"
                        )


                    evidence_ids = item.get(
                        "evidence_ids",
                        [],
                    )

                    if not isinstance(
                        evidence_ids,
                        list,
                    ):

                        evidence_ids = []


                    explanation = item.get(
                        "explanation",
                        "",
                    )

                    if not isinstance(
                        explanation,
                        str,
                    ):

                        explanation = str(
                            explanation
                        )


                    cleaned_results.append(
                        {
                            "claim": claim_text.strip(),
                            "status": status,
                            "evidence_ids": evidence_ids,
                            "explanation": explanation.strip(),
                        }
                    )


                return {
                    "success": True,
                    "fact_checks": cleaned_results,
                    "error": None
                }


            except errors.ServerError:

                if attempt < 2:

                    time.sleep(
                        2 ** attempt
                    )

                    continue


                return {
                    "success": False,
                    "fact_checks": [],
                    "error": (
                        f"Gemini server error :{error}"
                        
                
                    )
                }


            except errors.APIError as error:

                return {
                    "success": False,
                    "fact_checks": [],
                    "error": (
                        f"Gemini API error: {error}"
                    )
                }


            except json.JSONDecodeError:

                return {
                    "success": False,
                    "fact_checks": [],
                    "error": (
                        "Gemini returned an invalid "
                        "JSON response."
                    )
                }


    except Exception as error:

        return {
            "success": False,
            "fact_checks": [],
            "error": str(error)
        }