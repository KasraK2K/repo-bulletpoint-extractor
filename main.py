import os
import argparse
from dotenv import load_dotenv
from crewai import Crew, Process
from agents import ResearchAgent, AttributionAgent, SynthesisAgent, BulletEditor
from tasks import make_tasks
from tools.git_repo import get_github_owner_repo

def normalize_proof_links(text: str, owner: str, repo: str) -> str:
    if not text or not owner or not repo:
        return text
    base = f"https://github.com/{owner}/{repo}/"
    # Common placeholder bases used by LLMs or templates
    placeholders = [
        "https://github.com/project/repo/",
        "https://github.com/your-org-or-username/your-repo-name/",
        "https://github.com/org/repo/",
        "https://github.com/owner/repo/",
        "https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/",
        "https://github.com/${owner}/${repo}/",
        "https://github.com/<owner>/<repo>/",
        "https://github.com/<ORG>/<REPO>/",
    ]
    for ph in placeholders:
        text = text.replace(ph, base)
    return text

def sanitize_proof_links(text: str) -> str:
    import re
    if not text:
        return text
    def repl(m):
        url = m.group(1)
        # Accept commit links with hex sha and PR links with digits only
        if "/commit/" in url:
            sha = url.rsplit("/commit/", 1)[-1].split("/", 1)[0]
            if re.fullmatch(r"[0-9a-fA-F]{7,40}", sha):
                return m.group(0)
            return ""  # drop invalid placeholder commit link
        if "/pull/" in url:
            num = url.rsplit("/pull/", 1)[-1].split("/", 1)[0]
            if re.fullmatch(r"\d+", num):
                return m.group(0)
            return ""
        # Unknown pattern; keep as-is
        return m.group(0)
    text = re.sub(r"\[Proof\]\(([^)]+)\)", repl, text)
    # Collapse repeated spaces/tabs but keep newlines intact
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text

def main():
    parser = argparse.ArgumentParser(description="Run Repo Insights CrewAI Assistant")
    vg = parser.add_mutually_exclusive_group()
    vg.add_argument("--verbose", action="store_true", help="Enable progress output")
    vg.add_argument("--quiet", action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    # default to verbose unless explicitly quiet
    verbose = True
    if args.quiet:
        verbose = False
    elif args.verbose:
        verbose = True

    load_dotenv()
    # Disable telemetry in restricted environments
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")
    agents = {
        "ResearchAgent": ResearchAgent,
        "AttributionAgent": AttributionAgent,
        "SynthesisAgent": SynthesisAgent,
        "BulletEditor": BulletEditor
    }
    tasks, signals = make_tasks(agents, verbose=verbose)

    crew = Crew(
        agents=[ResearchAgent, AttributionAgent, SynthesisAgent, BulletEditor],
        tasks=tasks,
        process=Process.sequential,
        memory=False
    )

    if verbose:
        print("Initializing agents and tasks...", flush=True)
    # Attempt to run the crew; fall back to offline summary if environment blocks it
    try:
        if verbose:
            print("Starting CrewAI pipeline (sequential)...", flush=True)
        result = crew.kickoff()
        if verbose:
            print("CrewAI pipeline completed.", flush=True)
        output_text = str(result).strip()
    except Exception as e:
        # Offline/readonly/telemetry/network failures: degrade gracefully
        if verbose:
            print(f"CrewAI failed, falling back to offline summary: {e}", flush=True)
        output_text = (
            "[Offline mode] Could not run full CrewAI pipeline. "
            "Generated a minimal summary from local signals instead.\n\n"
        )
        # Use saved signals to craft simple Markdown sections (H2 + explanation)
        try:
            import json
            with open("output/signals.json","r") as sf:
                signals = json.load(sf)
            summary = signals.get("summary_you", {})
            hot = signals.get("top_files_you", [])[:5]
            langs = signals.get("languages", {})
            sections = []
            # Section: Contribution Summary
            if summary:
                title = "Impactful Contribution Summary"
                para = (
                    f"Based on git history, Kasra authored {summary.get('total_commits', 0)} commits "
                    f"touching {summary.get('files_touched_count', 0)} files with +{summary.get('total_insertions', 0)}/"
                    f"-{summary.get('total_deletions', 0)} line changes. This reflects sustained delivery and refactoring activity "
                    f"across key areas of the codebase, indicating ownership of complex features and maintainability improvements."
                )
                sections.append((title, para))
            # Section: Hot Files
            if hot:
                title = "Ownership Across Hotspots"
                hot_list = ", ".join(f"{os.path.basename(p)} ({n})" for p, n in hot)
                para = (
                    f"Frequent contributions cluster in high-churn areas: {hot_list}. These hotspots indicate focus on modules "
                    f"that shape runtime behaviour and product surface area, suggesting iterative optimization and feature work grounded in real usage."
                )
                sections.append((title, para))
            # Section: Language Footprint
            if langs:
                title = "Multi-Language Footprint"
                ld = ", ".join(f"{k}:{v}" for k, v in sorted(langs.items()))
                para = (
                    f"Changes span multiple languages ({ld}), highlighting cross-layer work from APIs/services to data/infrastructure. "
                    f"This breadth typically corresponds to end-to-end ownership of features and platform improvements."
                )
                sections.append((title, para))
            if not sections:
                sections = [("No Signals Available", "Could not derive sections from local signals.")]
            output_text += "\n\n".join([f"## {t}\n\n{p}" for t, p in sections])
        except Exception:
            output_text += "\n\n## Offline Summary\n\nUnable to load signals.json to produce sections."

    # Derive repo name from REPO_PATH and write to output/{repo}.md with H1 header
    repo_path = os.getenv("REPO_PATH", ".")
    repo_slug = os.path.basename(os.path.abspath(repo_path)) or "repository"
    def prettify(name: str) -> str:
        import re
        parts = re.split(r"[-_\s]+", name)
        return " ".join(w.capitalize() for w in parts if w)
    repo_title = prettify(repo_slug)

    # Normalize proof links: prefer owner/repo derived from git remote; fallback to env
    guess_owner, guess_repo = get_github_owner_repo(repo_path)
    env_owner = os.getenv("GITHUB_OWNER", "").strip()
    env_repo = os.getenv("GITHUB_REPO", "").strip()
    owner = (guess_owner or env_owner or "").strip()
    repo = (guess_repo or env_repo or "").strip()
    output_text = normalize_proof_links(output_text, owner, repo)
    output_text = sanitize_proof_links(output_text)

    os.makedirs("output", exist_ok=True)
    output_file = os.path.join("output", f"{repo_slug}.md")
    content = f"# {repo_title}\n\n" + (output_text or "") + "\n"
    with open(output_file, "w") as f:
        f.write(content)

    if verbose:
        print("Signals saved to output/signals.json")
        print(f"Bullets saved to {output_file}")

if __name__ == "__main__":
    main()
