import json, os, yaml
from crewai import Task
from tools.git_repo import load_git_history, contributions_by_user, summarize_impact, hot_files, get_github_owner_repo
from tools.github_api import load_github_issues_prs
from tools.code_scan import walk_code, language_breakdown, simple_component_detection

def load_cfg():
    with open("config.yaml","r") as f:
        return yaml.safe_load(f)

def collect_signals(verbose: bool = True):
    cfg = load_cfg()
    repo_path = os.getenv("REPO_PATH", ".")
    if verbose:
        print(f"[1/4] Scanning git history for {repo_path}...", flush=True)
    commits = load_git_history(
        repo_path, cfg["git"]["since"], cfg["git"]["until"], cfg["git"]["include_merge_commits"]
    )
    yours, others = contributions_by_user(commits, cfg["you"]["aliases"], cfg["you"]["emails"])
    base_summary = summarize_impact(yours)
    top_files = hot_files(yours, top_n=cfg["analysis"]["hot_file_top_n"])
    if verbose:
        print(
            f"  → Found {len(commits)} commits; yours: {len(yours)}; files touched: {base_summary.get('files_touched_count', 0)}",
            flush=True,
        )

    if verbose:
        print("[2/4] Analyzing codebase structure and languages...", flush=True)
    files = walk_code(repo_path, cfg["analysis"]["languages_of_interest"], cfg["analysis"]["max_files"])
    langs = language_breakdown(files)
    components = simple_component_detection(files)
    if verbose:
        print(f"  → Considered {len(files)} files; languages: {', '.join(sorted(langs.keys()))}", flush=True)

    if verbose:
        print("[3/4] Fetching GitHub issues/PRs (if configured)...", flush=True)
    owner = os.getenv("GITHUB_OWNER", "")
    repo = os.getenv("GITHUB_REPO", "")
    issues_prs = load_github_issues_prs(owner, repo)
    if verbose:
        print(
            f"  → Issues: {len(issues_prs.get('issues', []))}, PRs: {len(issues_prs.get('prs', []))}",
            flush=True,
        )

    payload = {
        "commits_you": yours[-500:],            # cap for prompt size
        "summary_you": base_summary,
        "top_files_you": top_files,
        "languages": langs,
        "components": components,
        "issues": issues_prs.get("issues", [])[:300],
        "prs": issues_prs.get("prs", [])[:300]
    }
    os.makedirs("output", exist_ok=True)
    with open("output/signals.json","w") as f:
        json.dump(payload, f, indent=2)
    if verbose:
        print("[4/4] Signals saved to output/signals.json", flush=True)
    return payload

def make_tasks(agents, verbose: bool = True):
    cfg = load_cfg()
    signals = collect_signals(verbose=verbose)

    # Determine GitHub base URL for proof links
    repo_path = os.getenv("REPO_PATH", ".")
    env_owner = os.getenv("GITHUB_OWNER", "").strip()
    env_repo = os.getenv("GITHUB_REPO", "").strip()
    guess_owner, guess_repo = get_github_owner_repo(repo_path)
    owner = (guess_owner or env_owner or "").strip()
    repo = (guess_repo or env_repo or "").strip()
    if owner and repo:
        github_base = f"https://github.com/{owner}/{repo}/"
        base_instruction = (
            f"Use full GitHub links with base {github_base} (commit/<hash> or pull/<number>)."
        )
    else:
        github_base = ""
        base_instruction = (
            "Use full GitHub links to commits or PRs from the repository's GitHub remote; avoid placeholders."
        )

    research = Task(
        description=(
            "Analyze repo signals and list candidate achievements attributable to Kasra. "
            "Focus on: architecture decisions, performance/reliability wins, major features, tooling, CI/CD, security, data migrations, "
            "mentoring/reviews, cross-team leadership. Provide evidence snippets and metrics. "
            + base_instruction
        ),
        agent=agents["ResearchAgent"],
        expected_output="A JSON with fields: achievements[], each has {title, evidence, metric_guess, files, time_window, area}"
    )

    attribution = Task(
        description=(
            "From research JSON, validate authorship using commits_you, PRs authored/assigned, and review activity. "
            "Boost confidence when Kasra authored most diffs or was assignee/reviewer on merged PRs. "
            "Return top 10 achievements with confidence scores and concrete metrics or reasonable estimates. "
            "Include proof_links as full URLs to commits or PRs in the repository's GitHub. "
            + base_instruction
        ),
        agent=agents["AttributionAgent"],
        context=[research],
        expected_output=("JSON with fields: validated_achievements[] {title, impact, metrics, confidence, proof_links?, proof_snippets}")
    )

    synthesis = Task(
        description=(
            "Turn validated achievements into STAR-shaped statements with tech stack and business impact. "
            f"Target {cfg['output']['bullets_count']} bullets. Keep ≤30 words each. Prefer %/ms/$/throughput/user metrics. "
            "Append a [Proof](<full-link>) where available; do NOT use placeholder domains. "
            + base_instruction
        ),
        agent=agents["SynthesisAgent"],
        context=[attribution],
        expected_output="List of concise bullet points (plain text, one per line)."
    )

    editing = Task(
        description=(
            "Polish bullets per style config. Deduplicate, fix tense, unify terminology, and ensure measurability. "
            "Use prompts/bulletpoint_system.txt and prompts/styles.md."
        ),
        agent=agents["BulletEditor"],
        context=[synthesis],
        expected_output="Final bullets ready for CV (plain text list)."
    )

    return [research, attribution, synthesis, editing], signals
