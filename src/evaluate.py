"""
evaluate.py - Scores how well the tailored CV matches the job requirements.
Uses a second LLM call as an independent evaluator.
"""

import json
from anthropic import Anthropic


def evaluate_output(job_description: str, tailored_content: dict) -> dict:
    """
    Independent evaluation of tailored CV against job requirements.
    Returns a structured score with breakdown.
    """

    client = Anthropic()

    prompt = f"""You are an independent recruiter evaluating how well a CV matches a job posting.

<job_description>
{job_description}
</job_description>

<tailored_cv_content>
{json.dumps(tailored_content, indent=2)}
</tailored_cv_content>

Score this CV against the job requirements. Be honest and critical.
Return ONLY valid JSON:

{{
    "overall_score": 1-10,
    "keyword_coverage": 1-10,
    "experience_relevance": 1-10,
    "skills_alignment": 1-10,
    "missing_keywords": ["keywords from job posting not reflected in CV"],
    "strongest_match": "which part of the CV is most compelling for this role",
    "weakest_area": "biggest gap between CV and job requirements",
    "recommendation": "apply" or "skip" or "apply_with_caveats",
    "caveat": "if apply_with_caveats, explain what to address"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
    if response_text.endswith("```"):
        response_text = response_text.rsplit("```", 1)[0]
    response_text = response_text.strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        result = {
            "overall_score": 0,
            "recommendation": "error",
            "raw_response": response_text,
        }

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python evaluate.py <job_description_file> <tailored_content_file>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        job_desc = f.read()
    with open(sys.argv[2], "r") as f:
        tailored = json.load(f)

    result = evaluate_output(job_desc, tailored)
    print(json.dumps(result, indent=2))
