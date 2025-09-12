import yaml
from crewai import Agent

# Support multiple LangChain import paths for ChatOpenAI
try:
    from langchain_openai import ChatOpenAI  # modern path
except Exception:
    try:
        from langchain_community.chat_models import ChatOpenAI  # community package path
    except Exception:
        from langchain.chat_models import ChatOpenAI  # legacy fallback

def llm():
    # Adjust model name as you wish
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

def load_cfg():
    with open("config.yaml","r") as f:
        return yaml.safe_load(f)

cfg = load_cfg()

ResearchAgent = Agent(
    role="Repo Researcher",
    goal="Collect high-quality signals about Kasra's contributions from code, commits, PRs, issues, and comments.",
    backstory="Experienced software archaeologist skilled at diffing, attributing authorship, and summarizing impact.",
    allow_delegation=False,
    llm=llm()
)

AttributionAgent = Agent(
    role="Authorship Attributor",
    goal="Distinguish Kasra's contributions from others and estimate impact with concrete metrics.",
    backstory="Understands commit statistics, ownership heuristics, PR authorship, assignees, and review activity.",
    allow_delegation=False,
    llm=llm()
)

SynthesisAgent = Agent(
    role="Impact Synthesizer",
    goal="Synthesize achievements into crisp STAR-shaped claims with quantifiable results.",
    backstory="Turns raw data into hard-hitting narrative statements oriented to outcomes and scale.",
    allow_delegation=False,
    llm=llm()
)

BulletEditor = Agent(
    role="CV Bullet Editor",
    goal="Produce polished, de-duplicated bullet points that match the selected style.",
    backstory="Seasoned CV editor for senior ICs and tech leads.",
    allow_delegation=False,
    llm=llm()
)
