import json, os, yaml
from crewai import Task
from tools.git_repo import load_git_history, contributions_by_user, summarize_impact, hot_files
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

    # Build a compact, grounded evidence blob to reduce hallucinations
    def _compact_signals(s):
        you = s.get("commits_you", [])[-100:]
        commits = [{
            "sha": c.get("hexsha", "")[:10],
            "msg": (c.get("message", "") or "").split("\n", 1)[0][:140],
            "files": c.get("files", [])[:10],
        } for c in you]
        return {
            "summary_you": s.get("summary_you", {}),
            "top_files_you": s.get("top_files_you", [])[:20],
            "components": s.get("components", {}),
            "languages": s.get("languages", {}),
            "commits_you": commits,
        }

    import json as _json
    evidence_blob = _json.dumps(_compact_signals(signals), ensure_ascii=False)

    research = Task(
        description=(
            "Analyze repo signals and list candidate achievements attributable to Kasra. "
            "Focus on: architecture decisions, performance/reliability wins, major features, tooling, CI/CD, security, data migrations, "
            "mentoring/reviews, cross-team leadership. Provide evidence snippets and metrics. "
            "Do not include links; capture commit/PR identifiers as plain text only if needed for context. "
            "Only use evidence from the provided signals; do not fabricate files or modules.\n\n"
            f"Signals: {evidence_blob}"
        ),
        agent=agents["ResearchAgent"],
        expected_output=(
            "A JSON with fields: achievements[], each has {title, evidence, metric_guess, files, time_window, area, evidence_paths[], commits[]}"
        )
    )

    attribution = Task(
        description=(
            "From research JSON, validate authorship using commits_you, PRs authored/assigned, and review activity. "
            "Boost confidence when Kasra authored most diffs or was assignee/reviewer on merged PRs. "
            "Return top 10 achievements with confidence scores and concrete metrics or reasonable estimates. "
            "Do not include any hyperlinks. "
            "Reject any achievement that lacks direct evidence (no matching files in signals or no commit shas authored by Kasra)."
        ),
        agent=agents["AttributionAgent"],
        context=[research],
        expected_output="JSON with fields: validated_achievements[] {title, impact, metrics, confidence, proof_links?, proof_snippets}"
    )

    synthesis = Task(
        description=(
            "Turn validated achievements into Markdown sections rather than a list. "
            f"Produce {cfg['output']['bullets_count']} sections. Each section MUST follow this exact template: \n"
            "## <Short, outcome-focused title>\n"
            "Bullet Point: <one-sentence, punchy summary of the title and description; no leading dashes>\n"
            "Description: <3–5 sentences explaining why this was written and how it happened in the repo: reference files/modules and scope; include metrics; no hyperlinks>\n"
            "No list items. No links. No raw URLs."
        ),
        agent=agents["SynthesisAgent"],
        context=[attribution],
        expected_output=(
            "Markdown text with repeated sections strictly matching: \n"
            "## <Title>\n"
            "Bullet Point: <one sentence>\n"
            "Description: <3–5 sentences>\n"
        )
    )

    editing = Task(
        description=(
            "Polish sections per style config: strong titles, active voice, consistent terminology, and specific metrics. "
            "Ensure each section matches the template exactly (H2, Bullet Point:, Description:). "
            "Remove any hyperlinks and list formatting. Use prompts/bulletpoint_system.txt and prompts/styles.md."
        ),
        agent=agents["BulletEditor"],
        context=[synthesis],
        expected_output=(
            "Final Markdown sections only (no lists): repeated blocks of '## <Title>', 'Bullet Point: ...', 'Description: ...'."
        )
    )

    return [research, attribution, synthesis, editing], signals
