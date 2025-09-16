"""Enhanced prompt templates for better CV bullet point generation."""

from typing import Dict, Any
from utils.config import Config


class PromptTemplates:
    """Enhanced prompt templates with better context and structure."""
    
    @staticmethod
    def research_prompt(person_name: str, evidence_blob: str) -> str:
        """Enhanced research prompt with better achievement detection."""
        return f"""You are an expert software engineering analyst. Your task is to identify significant, measurable achievements from {person_name}'s repository contributions.

**ANALYSIS GUIDELINES:**
1. **Focus on Impact**: Look for changes that improved performance, reliability, scalability, or user experience
2. **Seek Metrics**: Prioritize achievements with quantifiable outcomes (performance gains, reduced errors, increased throughput)
3. **Technical Depth**: Identify architectural decisions, complex implementations, and technical leadership
4. **Scope Assessment**: Evaluate the breadth and complexity of changes

**ACHIEVEMENT CATEGORIES TO IDENTIFY:**
- **Architecture & Design**: System redesigns, pattern implementations, architectural decisions
- **Performance Optimization**: Latency improvements, throughput increases, resource optimization
- **Reliability & Security**: Error reduction, monitoring improvements, security enhancements
- **Feature Development**: Major features, API implementations, user-facing functionality
- **Infrastructure & DevOps**: CI/CD improvements, deployment optimizations, tooling
- **Code Quality**: Refactoring efforts, test coverage improvements, technical debt reduction
- **Leadership & Mentoring**: Code reviews, team collaboration, knowledge sharing

**EVIDENCE REQUIREMENTS:**
- Only use evidence from the provided signals
- Match achievements to specific files, commit patterns, or PR activity
- Estimate reasonable metrics based on code changes and scope
- Reject any claim that cannot be backed by concrete evidence

**OUTPUT FORMAT:**
Return a JSON with this structure:
```json
{{
  "achievements": [
    {{
      "title": "Specific, outcome-focused title",
      "evidence": "Concrete evidence from signals",
      "metric_guess": "Reasonable quantified impact estimate",
      "files": ["list", "of", "relevant", "files"],
      "time_window": "When this occurred",
      "area": "Category from above list",
      "evidence_paths": ["specific", "code", "paths"],
      "commits": ["relevant", "commit", "identifiers"],
      "complexity_score": 1-10,
      "impact_scope": "team/service/organization"
    }}
  ]
}}
```

**REPOSITORY SIGNALS:**
{evidence_blob}

Analyze these signals and identify the most significant achievements attributable to {person_name}. Focus on quality over quantity."""

    @staticmethod
    def attribution_prompt(person_name: str, bullets_count: int) -> str:
        """Enhanced attribution prompt with confidence scoring."""
        return f"""You are a senior technical recruiter and engineering manager. Your task is to validate and rank achievements based on authorship evidence and impact.

**VALIDATION CRITERIA:**
1. **Authorship Confidence**: How certain are we that {person_name} was the primary contributor?
   - High: Clear commit authorship, PR ownership, or explicit assignments
   - Medium: Significant contributions but shared ownership
   - Low: Minor contributions or unclear attribution

2. **Impact Assessment**: Evaluate the business and technical impact
   - High: System-wide improvements, major performance gains, architectural changes
   - Medium: Feature implementations, moderate improvements, team-level impact
   - Low: Bug fixes, minor optimizations, individual task completion

3. **Evidence Quality**: How well-supported is the achievement?
   - Strong: Multiple commits, clear file changes, measurable outcomes
   - Moderate: Some evidence but incomplete picture
   - Weak: Limited evidence or speculative metrics

**RANKING STRATEGY:**
- Prioritize achievements with High authorship confidence AND High impact
- Include diverse achievement types (don't over-weight one area)
- Ensure metrics are realistic and defensible
- Remove achievements lacking concrete evidence

**OUTPUT REQUIREMENTS:**
Return exactly {bullets_count} validated achievements in JSON format:
```json
{{
  "validated_achievements": [
    {{
      "title": "Clear, outcome-focused title",
      "impact": "Quantified business/technical impact",
      "metrics": "Specific, realistic measurements",
      "confidence": "High/Medium/Low",
      "proof_snippets": ["concrete", "evidence", "quotes"],
      "ranking_score": 1-100
    }}
  ]
}}
```

Reject any achievement where {person_name}'s contribution cannot be clearly established or where metrics appear fabricated."""

    @staticmethod
    def synthesis_prompt(bullets_count: int) -> str:
        """Enhanced synthesis prompt for better section generation."""
        return f"""You are a senior CV editor specializing in technical leadership resumes. Transform validated achievements into compelling, structured sections.

**SECTION REQUIREMENTS:**
Create exactly {bullets_count} sections following this EXACT template:

```
## <Outcome-Focused Title>
**Bullet Point:** <One powerful sentence summarizing the achievement and impact> <br />
**Description:** <3-5 sentences explaining the technical context, implementation approach, and measurable results>
```

**WRITING GUIDELINES:**
1. **Titles**: Start with action verbs (Architected, Optimized, Implemented, Led, Designed)
2. **Bullet Points**: Lead with the outcome, include key metrics, avoid technical jargon
3. **Descriptions**: 
   - Explain the technical challenge and solution approach
   - Reference specific technologies, patterns, or methodologies
   - Include concrete metrics and timeframes
   - Show progression from problem to solution to impact

**TONE & STYLE:**
- Active voice throughout
- Confident, measurable language
- Senior technical leadership perspective
- British English spelling and grammar
- No "I" statements (use implicit STAR format)

**METRIC GUIDELINES:**
- Performance: Latency reductions (ms), throughput increases (req/s, transactions)
- Reliability: Error rate reductions (%), uptime improvements
- Scale: Data volumes (rows, GB, users), code complexity (files, LOC)
- Business: Cost savings, time reductions, efficiency gains
- Team: People mentored, processes improved, adoption rates

**FORBIDDEN ELEMENTS:**
- No bullet lists or dashes
- No hyperlinks or URLs
- No passive voice ("was implemented" → "implemented")
- No vague terms ("helped", "assisted", "worked on")

Transform the validated achievements into polished sections that demonstrate technical leadership and measurable impact."""

    @staticmethod
    def editing_prompt(style: str) -> str:
        """Enhanced editing prompt with style-specific guidance."""
        style_guides = {
            "senior_technical_lead": """
**SENIOR TECHNICAL LEAD STYLE:**
- Emphasize architectural decisions and system-level thinking
- Include 2-3 sections on scalability/reliability improvements  
- Include 1 section on team leadership or mentoring
- Show progression from individual contributor to technical leader
- Balance hands-on technical work with strategic thinking
- Metrics should reflect organization-level impact
            """,
            "simple": """
**SIMPLE STYLE:**
- Keep descriptions concise (2-3 sentences max)
- Focus on the most impactful metrics
- Use straightforward language
- Emphasize concrete deliverables
            """
        }
        
        guide = style_guides.get(style, style_guides["senior_technical_lead"])
        
        return f"""You are a professional CV editor. Polish the provided sections to meet high professional standards.

{guide}

**EDITING CHECKLIST:**
□ Each section follows the exact template format
□ Titles are outcome-focused and start with strong action verbs
□ Bullet points are single, powerful sentences ending with <br />
□ Descriptions provide technical context and measurable impact
□ All metrics are realistic and specific
□ Language is active, confident, and professional
□ No hyperlinks, lists, or formatting issues remain
□ Consistent terminology and style throughout

**FINAL OUTPUT:**
Return only the polished Markdown sections with NO additional commentary or explanation."""


def get_enhanced_prompts(config: Config) -> Dict[str, str]:
    """Get all enhanced prompts configured for the specific user."""
    templates = PromptTemplates()
    
    return {
        "research_template": templates.research_prompt,
        "attribution_template": templates.attribution_prompt, 
        "synthesis_template": templates.synthesis_prompt,
        "editing_template": templates.editing_prompt
    }