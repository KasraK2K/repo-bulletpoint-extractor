# 🚀 Repo Insights CrewAI Assistant

This project creates a **CrewAI-based assistant** that scans a software repository (code, commits, pull requests, issues, and comments) to discover **what *you* actually contributed** and then generates **high-impact CV bullet points**.

The assistant combines static analysis, Git history mining, issue/PR metadata, and multi-agent reasoning to turn raw repo data into measurable achievements (STAR-format, metric-heavy, recruiter-friendly).

---

## ✨ Features

- **Git analysis**  
  - Uses GitPython to extract commits, diffs, insertions/deletions, and hotspots.  
  - Filters by your author names/emails (so it only attributes your work).  
  - Summarises your commit volume, affected files, and biggest changes.

- **GitHub issues & PRs** *(optional)*  
  - Uses PyGithub to pull issues and PRs.  
  - Detects where you were author, assignee, or reviewer.  
  - Extracts comments, labels, and review notes for context.  
  - Can be swapped with GitLab (via `python-gitlab`).

- **Code scanning**  
  - Walks the codebase to detect language breakdown and architecture components (API, services, infra, frontend, tests).  
  - Identifies hot files you touched most often.  

- **CrewAI multi-agent pipeline**  
  - **ResearchAgent** → mines signals from commits/PRs/issues.  
  - **AttributionAgent** → confirms authorship and estimates impact/metrics.  
  - **SynthesisAgent** → turns raw data into STAR-shaped claims.  
  - **BulletEditor** → polishes into CV-ready bullets (clear, metric-driven).

- **Output**  
  - `output/signals.json` → raw structured evidence (commits, PRs, issues, hotspots).  
  - `output/bullets.md` → final CV bullet points (ready to paste into LinkedIn/CV).  

---

## 🛠️ Project Structure
```markdown
repo-insights/
├─ .env.example # API keys and repo config
├─ requirements.txt # dependencies
├─ config.yaml # settings: your name, emails, filters, style
├─ main.py # entrypoint to run the crew
├─ agents.py # defines the CrewAI agents
├─ tasks.py # defines the tasks and orchestration
├─ tools/
│ ├─ git_repo.py # Git history analysis
│ ├─ github_api.py # GitHub issues & PRs (optional)
│ └─ code_scan.py # language & component detection
├─ prompts/
│ ├─ bulletpoint_system.txt # rules for bullet formatting
│ └─ styles.md # CV styles (senior IC, tech lead, etc.)
└─ output/
├─ signals.json # extracted raw evidence
└─ bullets.md # final CV bullet points
```

---

## ⚙️ Configuration

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment setup

Copy .env.example → .env and edit:

### 3. Personal details in config

Edit config.yaml:

```yml
you:
  full_name: "Kasra"
  role: "Technical Lead / Software Architect"
  aliases: ["Kasra", "K. <surname>"]
  emails:
    - "kasra@company.com"
    - "kasra.personal@example.com"

output:
  bullets_count: 6
  style: "senior_technical_lead"
```

## ▶️ Running

Run the pipeline:
```bash
python main.py
```
* Signals saved to output/signals.json 
* CV bullets saved to output/bullets.md

## 📄 Example Output (from a fictional repo)

```markdown
- Re-architected payments service (Python/Redis/Kafka), cutting p95 latency **42%** and error rate **–63%** across 18 endpoints, enabling +3.1M monthly transactions.
- Introduced idempotent outbox + saga patterns, eliminating **99.8%** of duplicate order events during peak traffic.
- Designed multi-stage CI/CD with ephemeral test envs, shrinking PR cycle time from **2.7 days → 11 hours** and raising merge throughput **+58%**.
- Drove zero-downtime Postgres partitioning/migration (~1.2B rows), improving cold-start queries **–71%** and storage cost **–28%**.
- Mentored 6 engineers; instituted review checklists and architecture ADRs, reducing post-merge defects **–45%** quarter-over-quarter.
- Built observability (OpenTelemetry + SLOs), cutting on-call pages **–54%** and MTTR **–39%**.
```

_(These bullets are examples; your actual bullets will be generated from your repo data.)_

## 🔧 Extending

* GitLab support → replace PyGithub with python-gitlab.
* Custom heuristics → edit tools/code_scan.py to detect project-specific components.
* Different bullet styles → add to prompts/styles.md and switch in config.yaml.
* Privacy → everything runs locally; GitHub API is optional.

## 📌 Why This Matters

Recruiters and hiring managers don’t read code. They read bullet points.
This tool bridges the gap:

* Extracts real evidence from your work.
* Quantifies impact with metrics.
* Produces polished CV bullets you can paste directly.

No more vague “worked on backend microservices” — instead you get clear, metric-backed impact statements.

---

Would you like me to also include in that Markdown a **“Quick Start Copy-Paste”** section that gives just the essential setup/run commands (like a minimal README for teammates), or do you prefer keeping it detailed as above?
