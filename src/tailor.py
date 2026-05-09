"""
tailor.py - Takes the matched CV and job description, generates tailored CV content.
"""

import json
import os
from anthropic import Anthropic


def load_cv(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def tailor_cv(job_description: str, recommended_cv: str, match_result: dict, cv_dir: str = "cvs") -> dict:
    """
    Generate tailored CV content based on the job description and recommended CV.
    Returns structured sections ready for output.
    """

    cv_file = f"cv_{recommended_cv}.txt"
    cv_text = load_cv(os.path.join(cv_dir, cv_file))

    client = Anthropic()

    prompt = f"""You are a professional CV writer. Rewrite the CV content below to be tailored for the specific job posting.

<job_description>
{job_description}
</job_description>

<original_cv>
{cv_text}
</original_cv>

<match_analysis>
{json.dumps(match_result, indent=2)}
</match_analysis>

Rules:
- Do NOT invent experience or skills the candidate doesn't have
- Reframe existing experience to highlight relevance to this specific role
- Use keywords and language from the job posting where naturally applicable
- Keep it concise and professional
- If the job requires skills the candidate is learning or has basic knowledge of, frame honestly (e.g., "familiar with", "growing experience in")

Return ONLY valid JSON:

{{
    "professional_summary": "3-4 sentence tailored summary",
    "experience": [
        {{
            "dates": "YYYY-YYYY",
            "title": "Job Title",
            "company": "Company Name",
            "location": "Location",
            "description": "3-5 sentence tailored description"
        }}
    ],
    "skills": {{
        "primary": ["most relevant skills for this role"],
        "tools": ["relevant tools"],
        "languages": ["spoken languages with level"]
    }},
    "tailoring_notes": "Brief explanation of what was changed and why"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
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
            "professional_summary": "Failed to generate tailored content.",
            "experience": [],
            "skills": {"primary": [], "tools": [], "languages": []},
            "tailoring_notes": "Parse error",
            "raw_response": response_text,
        }

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python tailor.py <job_description_file> <match_result_file>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        job_desc = f.read()
    with open(sys.argv[2], "r") as f:
        match_result = json.load(f)

    result = tailor_cv(job_desc, match_result["recommended_cv"], match_result)
    print(json.dumps(result, indent=2))
