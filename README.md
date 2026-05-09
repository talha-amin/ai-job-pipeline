# AI Job Application Pipeline

An AI-powered pipeline that automates the job application process. Given a job posting, it selects the best-fit CV from multiple versions, generates tailored content, and evaluates output quality — turning a 2-hour manual process into under a minute.

## What It Does

```
Job Posting URL → Scrape → Match CV → Tailor Content → Evaluate Quality → Output
```

1. **Scrape** — Extracts job description from a URL (or accepts raw text)
2. **Match** — Sends the job description + both CVs to Claude API, returns which CV fits better with reasoning and a fit score
3. **Tailor** — Rewrites the selected CV's professional summary, experience descriptions, and skills section using the job posting's language and requirements
4. **Evaluate** — An independent LLM call scores the tailored output against the original job requirements (keyword coverage, experience relevance, skills alignment)
5. **Log** — Every run is logged to CSV with timestamp, company, scores, and recommendations for later analysis

## Why I Built This

I have two CVs — one focused on business development and one focused on data/engineering. When applying to working student jobs in Germany, I was manually deciding which CV to use, rewriting sections to match each job, and spending ~2 hours per application. This pipeline automates the analysis and content generation, letting me focus on quality applications instead of repetitive rewriting.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/talha-amin/ai-job-pipeline.git
cd ai-job-pipeline

# Install dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY=your_key_here

# Run the pipeline
python pipeline.py --url "https://example.com/job-posting" --company "Company" --role "Role Title"
```

## Usage

**From a URL:**
```bash
python pipeline.py --url "https://www.arbeitnow.com/jobs/..." --company "SAP" --role "Working Student Data Analyst"
```

**From a text file:**
```bash
python pipeline.py --file job_description.txt --company "Merck" --role "Label Analyst"
```

**Paste directly:**
```bash
python pipeline.py --text --company "Startup" --role "Growth Intern"
# Then paste the job description and press Ctrl+D
```

**Skip evaluation (saves one API call):**
```bash
python pipeline.py --url "..." --company "..." --role "..." --skip-eval
```

## Example Output

```
======================================================================
CV MATCH ANALYSIS
======================================================================
Recommended CV:  DATA
Fit Score:       8/10
Reasoning:       The role focuses on Python scripts, Google Sheets reporting,
                 and data validation — all core strengths in the data CV.
Key Matches:     Python scripting, Google Sheets, Data validation, SQL, Cross-functional collaboration
Gaps:            Google Apps Script, No direct financial reporting experience

======================================================================
TAILORED CV CONTENT
======================================================================

--- Professional Summary ---
Computer science graduate pursuing an MSc in Visual Computing at OvGU Magdeburg
with hands-on experience building data pipelines, SQL workflows, and Python
automation scripts...

--- Experience ---
2022-2024 | Assistant Software Engineer | Pakistan
Cubix Global Inc
Built full-stack applications using JS/TS, React, Next.js, and Node.js...

======================================================================
QUALITY EVALUATION
======================================================================
Overall Score:       7/10
Keyword Coverage:    8/10
Experience Match:    6/10
Skills Alignment:    8/10
Recommendation:      APPLY
Strongest Match:     Python scripting and data pipeline projects
Weakest Area:        No direct financial reporting experience
======================================================================
```

## Project Structure

```
ai-job-pipeline/
├── pipeline.py              # Main entry point — runs the full pipeline
├── requirements.txt
├── .env.example
├── cvs/
│   ├── cv_bizdev.txt         # Business development focused CV
│   └── cv_data.txt           # Data/engineering focused CV
├── src/
│   ├── scraper.py            # Fetches and cleans job postings from URLs
│   ├── matcher.py            # Matches job to best CV via Claude API
│   ├── tailor.py             # Generates tailored CV content
│   └── evaluate.py           # Independent quality scoring
├── outputs/                  # Generated tailored content (JSON)
│   └── example_delivery_hero_20250509.json
└── logs/                     # Run history CSV for analysis
    └── run_history.csv
```

## How It Works Under the Hood

The pipeline makes 3 Claude API calls per run (2 if you skip evaluation):

| Step | API Call | Purpose |
|------|----------|---------|
| Match | `claude-sonnet-4-20250514` | Analyze job + both CVs → recommend best fit |
| Tailor | `claude-sonnet-4-20250514` | Rewrite CV sections using job's language |
| Evaluate | `claude-sonnet-4-20250514` | Independent quality score of the output |

The evaluation step uses a separate LLM call as an independent judge — it doesn't see the original CV, only the tailored output and the job description. This prevents the system from rating its own work favorably.

## Run History & Analytics

Every run is logged to `logs/run_history.csv`:

| timestamp | company | role | recommended_cv | fit_score | eval_score | recommendation |
|-----------|---------|------|----------------|-----------|------------|----------------|
| 2025-05-09T14:30 | Delivery Hero | Tech Reporting | data | 8 | 7 | apply |
| 2025-05-09T15:10 | Synthflow AI | GTM Working Student | bizdev | 9 | 8 | apply |
| 2025-05-09T16:00 | Lovehoney | L&D Assistant | data | 3 | 2 | skip |

This data can be analyzed to understand which role types get the highest fit scores, which CV gets recommended more often, and where the biggest skill gaps are.

## Tech Stack

- **Python** — Core pipeline logic
- **Anthropic Claude API** — CV matching, content generation, and evaluation
- **BeautifulSoup** — Job posting scraping
- **CSV logging** — Lightweight run history tracking

## Customization

**Add your own CVs:** Replace the files in `cvs/` with your own CV text files. The pipeline supports any number of CVs — just update `matcher.py` to load additional files.

**Change the model:** Update the `model` parameter in `matcher.py`, `tailor.py`, and `evaluate.py`.

**Adjust prompts:** All prompts are inline in each module — modify them to change the output format or evaluation criteria.

## License

MIT
