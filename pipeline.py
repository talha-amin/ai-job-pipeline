"""
pipeline.py - Main entry point. Runs the full job application pipeline.

Usage:
    python pipeline.py --url <job_posting_url>
    python pipeline.py --file <job_description.txt>
    python pipeline.py --text  (then paste job description, Ctrl+D to finish)
"""

import argparse
import json
import os
import csv
from datetime import datetime

from src.scraper import scrape_job_posting, load_from_file
from src.matcher import match_cv_to_job
from src.tailor import tailor_cv
from src.evaluate import evaluate_output


def log_run(company: str, role: str, match_result: dict, eval_result: dict):
    """Append run data to CSV log."""
    log_file = "logs/run_history.csv"
    file_exists = os.path.exists(log_file)

    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp", "company", "role", "recommended_cv",
                "fit_score", "eval_score", "recommendation",
                "key_matches", "gaps"
            ])
        writer.writerow([
            datetime.now().isoformat(),
            company,
            role,
            match_result.get("recommended_cv", ""),
            match_result.get("fit_score", ""),
            eval_result.get("overall_score", ""),
            eval_result.get("recommendation", ""),
            "; ".join(match_result.get("key_matches", [])),
            "; ".join(match_result.get("gaps", [])),
        ])


def save_output(company: str, role: str, match_result: dict, tailored: dict, evaluation: dict):
    """Save all outputs to a JSON file in outputs/."""
    safe_name = f"{company}_{role}".lower().replace(" ", "_").replace("/", "-")[:60]
    filename = f"outputs/{safe_name}_{datetime.now().strftime('%Y%m%d')}.json"

    output = {
        "metadata": {
            "company": company,
            "role": role,
            "timestamp": datetime.now().isoformat(),
            "recommended_cv": match_result.get("recommended_cv"),
        },
        "match_analysis": match_result,
        "tailored_content": tailored,
        "evaluation": evaluation,
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filename


def print_results(match_result: dict, tailored: dict, evaluation: dict):
    """Pretty print the pipeline results."""
    print("\n" + "=" * 70)
    print("CV MATCH ANALYSIS")
    print("=" * 70)
    print(f"Recommended CV:  {match_result.get('recommended_cv', 'N/A').upper()}")
    print(f"Fit Score:       {match_result.get('fit_score', 'N/A')}/10")
    print(f"Reasoning:       {match_result.get('reasoning', 'N/A')}")
    print(f"Key Matches:     {', '.join(match_result.get('key_matches', []))}")
    print(f"Gaps:            {', '.join(match_result.get('gaps', []))}")

    print("\n" + "=" * 70)
    print("TAILORED CV CONTENT")
    print("=" * 70)

    print(f"\n--- Professional Summary ---")
    print(tailored.get("professional_summary", "N/A"))

    print(f"\n--- Experience ---")
    for exp in tailored.get("experience", []):
        print(f"\n{exp.get('dates', '')} | {exp.get('title', '')} | {exp.get('location', '')}")
        print(f"{exp.get('company', '')}")
        print(exp.get("description", ""))

    print(f"\n--- Skills ---")
    skills = tailored.get("skills", {})
    if skills.get("primary"):
        print(f"Primary:   {', '.join(skills['primary'])}")
    if skills.get("tools"):
        print(f"Tools:     {', '.join(skills['tools'])}")
    if skills.get("languages"):
        print(f"Languages: {', '.join(skills['languages'])}")

    print(f"\n--- Tailoring Notes ---")
    print(tailored.get("tailoring_notes", "N/A"))

    print("\n" + "=" * 70)
    print("QUALITY EVALUATION")
    print("=" * 70)
    print(f"Overall Score:       {evaluation.get('overall_score', 'N/A')}/10")
    print(f"Keyword Coverage:    {evaluation.get('keyword_coverage', 'N/A')}/10")
    print(f"Experience Match:    {evaluation.get('experience_relevance', 'N/A')}/10")
    print(f"Skills Alignment:    {evaluation.get('skills_alignment', 'N/A')}/10")
    print(f"Recommendation:      {evaluation.get('recommendation', 'N/A').upper()}")
    if evaluation.get("caveat"):
        print(f"Caveat:              {evaluation['caveat']}")
    print(f"Strongest Match:     {evaluation.get('strongest_match', 'N/A')}")
    print(f"Weakest Area:        {evaluation.get('weakest_area', 'N/A')}")
    missing = evaluation.get("missing_keywords", [])
    if missing:
        print(f"Missing Keywords:    {', '.join(missing)}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="AI Job Application Pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="URL of the job posting to scrape")
    group.add_argument("--file", help="Path to a text file with the job description")
    group.add_argument("--text", action="store_true", help="Paste job description via stdin")

    parser.add_argument("--company", default="Unknown", help="Company name (for logging)")
    parser.add_argument("--role", default="Unknown", help="Role title (for logging)")
    parser.add_argument("--skip-eval", action="store_true", help="Skip evaluation step (saves one API call)")

    args = parser.parse_args()

    # Step 1: Get job description
    print("\n[1/4] Fetching job description...")
    if args.url:
        job_desc = scrape_job_posting(args.url)
        if not job_desc:
            print("Failed to scrape URL. Try --file or --text instead.")
            return
    elif args.file:
        job_desc = load_from_file(args.file)
    else:
        print("Paste job description below (Ctrl+D when done):")
        import sys
        job_desc = sys.stdin.read()

    print(f"   Got {len(job_desc)} characters")

    # Step 2: Match CV
    print("\n[2/4] Analyzing job and matching CV...")
    match_result = match_cv_to_job(job_desc)
    print(f"   Recommended: {match_result.get('recommended_cv', 'N/A').upper()} CV (score: {match_result.get('fit_score', '?')}/10)")

    # Step 3: Tailor CV
    print("\n[3/4] Generating tailored CV content...")
    tailored = tailor_cv(job_desc, match_result["recommended_cv"], match_result)
    print("   Tailored content generated")

    # Step 4: Evaluate
    if not args.skip_eval:
        print("\n[4/4] Evaluating output quality...")
        evaluation = evaluate_output(job_desc, tailored)
        print(f"   Quality score: {evaluation.get('overall_score', '?')}/10 — {evaluation.get('recommendation', '?').upper()}")
    else:
        evaluation = {"overall_score": "skipped", "recommendation": "skipped"}
        print("\n[4/4] Evaluation skipped")

    # Print results
    print_results(match_result, tailored, evaluation)

    # Save outputs
    filename = save_output(args.company, args.role, match_result, tailored, evaluation)
    print(f"\nOutput saved: {filename}")

    # Log run
    log_run(args.company, args.role, match_result, evaluation)
    print(f"Run logged:   logs/run_history.csv")


if __name__ == "__main__":
    main()
