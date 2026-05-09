"""
matcher.py - Sends job description + both CVs to Claude API, returns structured recommendation.
"""

import json
import os
from anthropic import Anthropic


def load_cv(filepath: str) -> str:
    """Load CV text from file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def match_cv_to_job(job_description: str, cv_dir: str = "cvs") -> dict:
    """
    Send job description and both CVs to Claude API.
    Returns structured JSON with:
    - recommended_cv: which CV to use
    - reasoning: why this CV was chosen
    - fit_score: 1-10 how well the candidate fits
    - key_matches: skills/experience that match
    - gaps: what's missing
    """

    cv_bizdev = load_cv(os.path.join(cv_dir, "cv_bizdev.txt"))
    cv_data = load_cv(os.path.join(cv_dir, "cv_data.txt"))

    client = Anthropic()

    prompt = f"""You are a career advisor analyzing a job posting against two CVs for the same person.

<job_description>
{job_description}
</job_description>

<cv_bizdev>
{cv_bizdev}
</cv_bizdev>

<cv_data>
{cv_data}
</cv_data>

Analyze the job posting and determine which CV is the better fit. Return ONLY valid JSON with no other text:

{{
    "recommended_cv": "bizdev" or "data",
    "reasoning": "2-3 sentences explaining why this CV is the better fit",
    "fit_score": 1-10,
    "key_matches": ["list of 3-5 matching skills or experiences"],
    "gaps": ["list of any missing requirements"],
    "role_type": "one of: data_analytics, business_development, operations, engineering, product, marketing, other"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text

    # Clean potential markdown fencing
    response_text = response_text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
    if response_text.endswith("```"):
        response_text = response_text.rsplit("```", 1)[0]
    response_text = response_text.strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        result = {
            "recommended_cv": "data",
            "reasoning": "Failed to parse API response. Defaulting to data CV.",
            "fit_score": 0,
            "key_matches": [],
            "gaps": ["Parse error"],
            "role_type": "other",
            "raw_response": response_text,
        }

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python matcher.py <job_description_file>")
        print("  or pipe text: echo 'job desc' | python matcher.py -")
        sys.exit(1)

    source = sys.argv[1]
    if source == "-":
        job_desc = sys.stdin.read()
    else:
        with open(source, "r") as f:
            job_desc = f.read()

    result = match_cv_to_job(job_desc)
    print(json.dumps(result, indent=2))
