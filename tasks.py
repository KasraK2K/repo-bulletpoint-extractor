import json, os
from crewai import Task
from utils.config import Config
from utils.progress import ProgressTracker
from analyzers.signal_analyzer import EnhancedSignalAnalyzer
from prompts.enhanced_prompts import PromptTemplates

def collect_signals(verbose: bool = True):
    """Collect signals using enhanced analyzer."""
    config = Config()
    progress = ProgressTracker(verbose=verbose)
    analyzer = EnhancedSignalAnalyzer(config, progress)
    return analyzer.collect_enhanced_signals()

def make_tasks(agents, verbose: bool = True):
    config = Config()
    signals = collect_signals(verbose=verbose)
    person = config.person_name
    templates = PromptTemplates()

    # Build enhanced evidence blob
    import json as _json
    evidence_blob = _json.dumps(signals, ensure_ascii=False, indent=2)

    research = Task(
        description=templates.research_prompt(person, evidence_blob),
        agent=agents["ResearchAgent"],
        expected_output=(
            "A JSON with achievements[] array containing validated, evidence-backed achievements with complexity scores and impact assessments"
        )
    )

    attribution = Task(
        description=templates.attribution_prompt(person, config.bullets_count),
        agent=agents["AttributionAgent"],
        context=[research],
        expected_output="JSON with validated_achievements[] ranked by confidence and impact with realistic metrics"
    )

    synthesis = Task(
        description=templates.synthesis_prompt(config.bullets_count),
        agent=agents["SynthesisAgent"],
        context=[attribution],
        expected_output=(
            f"Exactly {config.bullets_count} polished Markdown sections with technical leadership focus and measurable impact"
        )
    )

    editing = Task(
        description=templates.editing_prompt(config.output_style),
        agent=agents["BulletEditor"],
        context=[synthesis],
        expected_output=(
            "Professional, polished CV sections optimized for senior technical leadership roles with consistent formatting and strong metrics"
        )
    )

    return [research, attribution, synthesis, editing], signals
