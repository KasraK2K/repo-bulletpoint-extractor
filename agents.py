import os
from crewai import Agent
from utils.config import Config

# Support multiple LangChain import paths for ChatOpenAI
try:
    from langchain_openai import ChatOpenAI  # modern path
except Exception:
    try:
        from langchain_community.chat_models import ChatOpenAI  # community package path
    except Exception:
        from langchain.chat_models import ChatOpenAI  # legacy fallback


def make_llm():
    """Create LLM only if OPENAI_API_KEY is present; else raise to allow offline mode."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set")
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def make_agents(config: Config = None):
    if config is None:
        config = Config()
    
    person = config.person_name
    role = config.person_role
    llm = make_llm()
    ResearchAgent = Agent(
        role="Repo Researcher",
        goal=f"Collect high-quality signals about {person}'s contributions from code, commits, PRs, issues, and comments.",
        backstory="Experienced software archaeologist skilled at diffing, attributing authorship, and summarizing impact.",
        allow_delegation=False,
        llm=llm,
    )

    AttributionAgent = Agent(
        role="Authorship Attributor",
        goal=f"Distinguish {person}'s contributions from others and estimate impact with concrete metrics.",
        backstory="Understands commit statistics, ownership heuristics, PR authorship, assignees, and review activity.",
        allow_delegation=False,
        llm=llm,
    )

    SynthesisAgent = Agent(
        role="Impact Synthesizer",
        goal="Synthesize achievements into crisp, outcome-focused sections with quantifiable results.",
        backstory="Turns raw data into hard-hitting narrative statements oriented to outcomes and scale.",
        allow_delegation=False,
        llm=llm,
    )

    BulletEditor = Agent(
        role="CV Bullet Editor",
        goal=f"Produce polished, grounded sections tailored for a {role}.",
        backstory="Seasoned CV editor for senior ICs and tech leads.",
        allow_delegation=False,
        llm=llm,
    )

    return {
        "ResearchAgent": ResearchAgent,
        "AttributionAgent": AttributionAgent,
        "SynthesisAgent": SynthesisAgent,
        "BulletEditor": BulletEditor,
    }
