import os
import argparse
from dotenv import load_dotenv
from crewai import Crew, Process
from tasks import make_tasks, collect_signals
from tools.git_repo import get_github_owner_repo
from tools.formatting import (
    normalize_proof_links,
    sanitize_proof_links,
    remove_links,
    validate_and_autofix_sections,
)

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
    agents = None
    crew = None
    # Only initialize LLM agents if we have an API key
    if os.getenv("OPENAI_API_KEY"):
        from agents import make_agents  # lazy import to avoid requiring API key in offline mode
        agents = make_agents()
        tasks, signals = make_tasks(agents, verbose=verbose)
        crew = Crew(
            agents=[
                agents["ResearchAgent"],
                agents["AttributionAgent"],
                agents["SynthesisAgent"],
                agents["BulletEditor"],
            ],
            tasks=tasks,
            process=Process.sequential,
        )
    else:
        # Offline mode: still collect signals for fallback output
        signals = collect_signals(verbose=verbose)

    if verbose:
        print("Initializing agents and tasks...", flush=True)
    # Attempt to run the crew; fall back to offline summary if environment blocks it
    try:
        if crew is None:
            raise RuntimeError("Offline mode: no LLM agents available")
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
                # Use configured name
                try:
                    import yaml as _yaml
                    with open("config.yaml","r") as _f:
                        _cfg = _yaml.safe_load(_f)
                    _person = _cfg.get("you",{}).get("full_name","The author")
                except Exception:
                    _person = "The author"
                title = "Impactful Contribution Summary"
                bp = (
                    f"{_person} authored {summary.get('total_commits', 0)} commits across {summary.get('files_touched_count', 0)} files "
                    f"(+{summary.get('total_insertions', 0)}/-{summary.get('total_deletions', 0)} LOC), reflecting sustained delivery."
                )
                desc = (
                    f"Contributions span key modules, showing consistent feature delivery and refactoring. The breadth and depth of changes "
                    f"point to end-to-end ownership and maintainability improvements across the codebase."
                )
                sections.append((title, bp, desc))
            # Section: Hot Files
            if hot:
                title = "Ownership Across Hotspots"
                hot_list = ", ".join(f"{os.path.basename(p)} ({n})" for p, n in hot)
                bp = f"High activity in hotspots: {hot_list}, indicating iterative optimization in critical paths."
                desc = (
                    f"Focus on high-churn modules that shape runtime behaviour and user-visible features suggests targeted improvements driven by usage. "
                    f"This pattern aligns with steady hardening and performance tuning."
                )
                sections.append((title, bp, desc))
            # Section: Language Footprint
            if langs:
                title = "Multi-Language Footprint"
                ld = ", ".join(f"{k}:{v}" for k, v in sorted(langs.items()))
                bp = f"Cross-layer changes across languages ({ld}) demonstrate end-to-end ownership."
                desc = (
                    f"Work spans APIs/services and data/infrastructure layers, enabling coherent architectural decisions and integrated delivery. "
                    f"This breadth improves cohesion and reduces handoffs."
                )
                sections.append((title, bp, desc))
            if not sections:
                sections = [("No Signals Available", "No summary", "Could not derive sections from local signals.")]
            output_text += "\n\n".join([f"## {t}\n\nBullet Point: {bp}\n\nDescription: {d}" for t, bp, d in sections])
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
    output_text = remove_links(output_text)
    output_text = validate_and_autofix_sections(output_text)

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
