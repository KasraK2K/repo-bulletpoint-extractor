import os
import argparse
from dotenv import load_dotenv
from crewai import Crew, Process
from agents import ResearchAgent, AttributionAgent, SynthesisAgent, BulletEditor
from tasks import make_tasks

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
        # Use saved signals to craft simple bullets
        try:
            import json
            with open("output/signals.json","r") as sf:
                signals = json.load(sf)
            summary = signals.get("summary_you", {})
            hot = signals.get("top_files_you", [])[:5]
            langs = signals.get("languages", {})
            bullets = []
            if summary:
                bullets.append(
                    f"Authored {summary.get('total_commits', 0)} commits touching "
                    f"{summary.get('files_touched_count', 0)} files with "
                    f"+{summary.get('total_insertions', 0)}/-{summary.get('total_deletions', 0)} LOC changes."
                )
            if hot:
                bullets.append(
                    "Top touched files: " + ", ".join(f"{p} ({n})" for p, n in hot)
                )
            if langs:
                bullets.append(
                    "Language breakdown: " + ", ".join(f"{k}:{v}" for k, v in sorted(langs.items()))
                )
            if not bullets:
                bullets = ["No signals available to summarize."]
            output_text += "\n".join(f"- {b}" for b in bullets)
        except Exception:
            output_text += "- Unable to load signals.json."

    # Derive repo name from REPO_PATH and write to output/{repo}.md with H1 header
    repo_path = os.getenv("REPO_PATH", ".")
    repo_slug = os.path.basename(os.path.abspath(repo_path)) or "repository"
    def prettify(name: str) -> str:
        import re
        parts = re.split(r"[-_\s]+", name)
        return " ".join(w.capitalize() for w in parts if w)
    repo_title = prettify(repo_slug)

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
