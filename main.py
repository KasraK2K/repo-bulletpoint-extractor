import os
import argparse
import sys
from dotenv import load_dotenv
from crewai import Crew, Process

from utils.config import Config, ConfigError
from utils.progress import ProgressTracker
from tasks import make_tasks, collect_signals
from tools.git_repo import get_github_owner_repo
from tools.formatting import (
    normalize_proof_links,
    sanitize_proof_links,
    remove_links,
    validate_and_autofix_sections,
)

def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Repo Insights CrewAI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run with default settings
  python main.py --quiet           # Run without progress output
  python main.py --config custom.yaml  # Use custom config file
        """
    )
    vg = parser.add_mutually_exclusive_group()
    vg.add_argument("--verbose", action="store_true", help="Enable detailed progress output")
    vg.add_argument("--quiet", action="store_true", help="Suppress all progress output")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration file")
    parser.add_argument("--validate-only", action="store_true", help="Only validate configuration and exit")
    args = parser.parse_args()

    # Setup progress tracking
    verbose = not args.quiet
    progress = ProgressTracker(verbose=verbose)
    
    # Load and validate configuration
    try:
        progress.step("Loading configuration", f"Reading from {args.config}")
        config = Config(args.config)
        progress.success(f"Configuration loaded for {config.person_name}")
        
        if args.validate_only:
            progress.success("Configuration is valid")
            return
            
    except ConfigError as e:
        progress.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        progress.error(f"Unexpected error loading config: {e}")
        sys.exit(1)

    # Load environment and disable telemetry
    load_dotenv()
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")
    
    agents = None
    crew = None
    
    # Check for API key availability
    has_api_key = bool(os.getenv("OPENAI_API_KEY"))
    
    if has_api_key:
        try:
            progress.step("Initializing AI agents", "Setting up CrewAI agents with enhanced prompts")
            from agents import make_agents
            agents = make_agents(config)
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
                verbose=verbose
            )
            progress.success("AI agents initialized successfully")
        except Exception as e:
            progress.error(f"Failed to initialize agents: {e}")
            progress.warning("Falling back to offline mode")
            has_api_key = False
    
    if not has_api_key:
        progress.warning("No OpenAI API key found - running in offline mode")
        signals = collect_signals(verbose=verbose)

    # Execute the pipeline
    try:
        if crew is None:
            raise RuntimeError("Offline mode: no LLM agents available")
        
        progress.step("Running CrewAI pipeline", "Processing signals through multi-agent system")
        result = crew.kickoff()
        progress.success("CrewAI pipeline completed successfully")
        output_text = str(result).strip()
        
    except Exception as e:
        progress.error(f"CrewAI pipeline failed: {e}")
        progress.step("Generating offline fallback", "Creating summary from local signals")
        
        output_text = (
            "[Enhanced Offline Mode] Could not run full CrewAI pipeline. "
            "Generated an enhanced summary from local signals instead.\n\n"
        )
        # Generate enhanced offline summary
        try:
            import json
            with open("output/signals.json", "r") as sf:
                signals = json.load(sf)
            
            summary = signals.get("summary_you", {})
            patterns = signals.get("commit_patterns", [])
            impact_signals = signals.get("impact_signals", [])
            ownership = signals.get("ownership_map", {})
            
            sections = []
            person_name = config.person_name
            
            # Enhanced contribution summary
            if summary:
                title = "Technical Leadership Impact"
                commits = summary.get('total_commits', 0)
                files = summary.get('files_touched_count', 0)
                net_lines = summary.get('net_lines', 0)
                directories = summary.get('directories_touched_count', 0)
                
                bp = (
                    f"{person_name} delivered {commits} commits across {files} files "
                    f"in {directories} directories (+{summary.get('total_insertions', 0)}/-{summary.get('total_deletions', 0)} LOC), "
                    f"demonstrating sustained technical leadership and architectural ownership."
                )
                desc = (
                    f"Contributions demonstrate systematic approach to software delivery with {summary.get('avg_commits_per_week', 0)} commits per week on average. "
                    f"The breadth across {directories} directories and {net_lines:+} net lines of code indicates "
                    f"significant architectural involvement and feature development leadership. "
                    f"Largest single contribution involved {summary.get('largest_single_commit', 0)} lines, suggesting complex feature implementations."
                )
                sections.append((title, bp, desc))
            
            # Pattern-based achievements
            if patterns:
                top_pattern = patterns[0]
                title = f"{top_pattern.get('theme', 'Technical').title()} Initiative Leadership"
                bp = (
                    f"Led {top_pattern.get('theme', 'technical').lower()} initiative spanning "
                    f"{top_pattern.get('commit_count', 0)} commits and {len(top_pattern.get('files_affected', []))} files, "
                    f"achieving complexity score of {top_pattern.get('complexity_score', 0)}."
                )
                desc = (
                    f"Systematic approach to {top_pattern.get('theme', 'technical').lower()} improvements demonstrated through "
                    f"coordinated changes across {len(top_pattern.get('files_affected', []))} files. "
                    f"The {top_pattern.get('total_changes', 0)} total line changes reflect comprehensive refactoring "
                    f"and architectural enhancement efforts with measurable complexity impact."
                )
                sections.append((title, bp, desc))
            
            # Impact signals summary
            if impact_signals:
                high_impact = [s for s in impact_signals if s.get('estimated_impact') == 'High']
                if high_impact:
                    signal = high_impact[0]
                    title = f"{signal.get('type', 'Technical').title()} Optimization Delivery"
                    bp = (
                        f"Delivered {signal.get('type', 'technical')} improvements across "
                        f"{signal.get('files_count', 0)} files with {signal.get('confidence', 0):.0%} confidence, "
                        f"achieving {signal.get('estimated_impact', 'significant').lower()} impact."
                    )
                    hints = signal.get('metrics_hints', [])
                    metrics_text = " ".join(hints[:2]) if hints else "measurable performance improvements"
                    desc = (
                        f"Technical leadership in {signal.get('type', 'system')} optimization resulted in {metrics_text}. "
                        f"Evidence from commit patterns shows systematic approach to improvement with "
                        f"focus on {signal.get('files_count', 0)} critical system components."
                    )
                    sections.append((title, bp, desc))
            
            if not sections:
                sections = [("Limited Signal Analysis", 
                           "Analysis completed with available local signals.", 
                           "Enhanced offline mode provided basic contribution analysis from repository data.")]
            
            formatted_sections = []
            for title, bp, desc in sections:
                formatted_sections.append(f"## {title}\n\n**Bullet Point:** {bp} <br />\n\n**Description:** {desc}")
            
            output_text += "\n\n" + "\n\n".join(formatted_sections)
            
        except Exception as e:
            progress.warning(f"Could not generate enhanced offline summary: {e}")
            output_text += "\n\n## Basic Offline Summary\n\nUnable to load enhanced signals for detailed analysis."

    # Process and save output
    progress.step("Processing output", "Formatting and saving results")
    
    repo_path = os.getenv("REPO_PATH", ".")
    repo_slug = os.path.basename(os.path.abspath(repo_path)) or "repository"
    
    def prettify(name: str) -> str:
        import re
        parts = re.split(r"[-_\s]+", name)
        return " ".join(w.capitalize() for w in parts if w)
    
    repo_title = prettify(repo_slug)
    
    # Enhanced output processing
    guess_owner, guess_repo = get_github_owner_repo(repo_path)
    env_owner = os.getenv("GITHUB_OWNER", "").strip()
    env_repo = os.getenv("GITHUB_REPO", "").strip()
    owner = (guess_owner or env_owner or "").strip()
    repo = (guess_repo or env_repo or "").strip()
    
    # Apply formatting improvements
    output_text = normalize_proof_links(output_text, owner, repo)
    output_text = sanitize_proof_links(output_text)
    output_text = remove_links(output_text)
    output_text = validate_and_autofix_sections(output_text)
    
    # Save output
    os.makedirs("output", exist_ok=True)
    output_file = os.path.join("output", f"{repo_slug}.md")
    
    # Enhanced header with metadata
    header = f"# {repo_title}\n\n"
    if has_api_key:
        header += f"*Generated by Enhanced CrewAI Assistant for {config.person_name}*\n\n"
    else:
        header += f"*Generated in Enhanced Offline Mode for {config.person_name}*\n\n"
    
    content = header + (output_text or "") + "\n"
    
    with open(output_file, "w") as f:
        f.write(content)
    
    # Final status
    progress.success("Analysis complete!")
    progress.info(f"Signals: output/signals.json")
    progress.info(f"CV Content: {output_file}")
    
    if config.bullets_count > 10:
        progress.info(f"Generated {config.bullets_count} sections - consider reviewing for quality")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
