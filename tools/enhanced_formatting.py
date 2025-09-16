"""Enhanced formatting utilities for better output quality."""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SectionQuality:
    """Quality assessment for a CV section."""
    has_metrics: bool
    has_technical_terms: bool
    appropriate_length: bool
    active_voice: bool
    score: float
    suggestions: List[str]


class EnhancedFormatter:
    """Enhanced formatting with quality assessment and improvements."""
    
    # Technical keywords that indicate depth
    TECHNICAL_KEYWORDS = {
        'architecture': ['microservices', 'api', 'rest', 'graphql', 'database', 'cache', 'queue'],
        'performance': ['latency', 'throughput', 'optimization', 'scaling', 'load', 'performance'],
        'infrastructure': ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'ci/cd', 'deployment'],
        'languages': ['python', 'javascript', 'typescript', 'java', 'go', 'rust', 'kotlin'],
        'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'express'],
        'databases': ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb'],
        'tools': ['git', 'jira', 'jenkins', 'terraform', 'ansible', 'prometheus', 'grafana']
    }
    
    # Metrics patterns to recognize
    METRICS_PATTERNS = [
        r'\d+%',  # Percentages
        r'\d+x',  # Multipliers
        r'\d+ms',  # Milliseconds
        r'\d+s',   # Seconds
        r'\d+\.\d+[a-z]*',  # Decimal numbers with units
        r'\$\d+',  # Dollar amounts
        r'\d+k\b',  # Thousands
        r'\d+m\b',  # Millions
        r'\d+ (users?|files?|requests?|transactions?|errors?)',  # Count metrics
    ]
    
    def assess_section_quality(self, title: str, bullet_point: str, description: str) -> SectionQuality:
        """Assess the quality of a CV section."""
        full_text = f"{title} {bullet_point} {description}".lower()
        
        # Check for metrics
        has_metrics = any(re.search(pattern, full_text, re.IGNORECASE) for pattern in self.METRICS_PATTERNS)
        
        # Check for technical terms
        tech_count = sum(
            len([term for term in terms if term in full_text])
            for terms in self.TECHNICAL_KEYWORDS.values()
        )
        has_technical_terms = tech_count >= 2
        
        # Check length appropriateness
        desc_words = len(description.split())
        appropriate_length = 20 <= desc_words <= 80  # 3-5 sentences
        
        # Check for active voice (simplified heuristic)
        passive_indicators = ['was', 'were', 'been', 'being']
        passive_count = sum(1 for word in passive_indicators if word in full_text)
        active_voice = passive_count <= 1
        
        # Calculate score
        score = (
            (1.0 if has_metrics else 0.0) * 0.3 +
            (1.0 if has_technical_terms else 0.0) * 0.3 +
            (1.0 if appropriate_length else 0.0) * 0.2 +
            (1.0 if active_voice else 0.0) * 0.2
        )
        
        # Generate suggestions
        suggestions = []
        if not has_metrics:
            suggestions.append("Add specific metrics (percentages, time improvements, scale)")
        if not has_technical_terms:
            suggestions.append("Include more technical terminology and technologies")
        if not appropriate_length:
            if desc_words < 20:
                suggestions.append("Expand description with more technical details")
            else:
                suggestions.append("Condense description to focus on key achievements")
        if not active_voice:
            suggestions.append("Use more active voice constructions")
        
        return SectionQuality(
            has_metrics=has_metrics,
            has_technical_terms=has_technical_terms,
            appropriate_length=appropriate_length,
            active_voice=active_voice,
            score=score,
            suggestions=suggestions
        )
    
    def enhance_section(self, title: str, bullet_point: str, description: str) -> Dict[str, str]:
        """Enhance a section based on quality assessment."""
        quality = self.assess_section_quality(title, bullet_point, description)
        
        enhanced_title = self._enhance_title(title)
        enhanced_bullet = self._enhance_bullet_point(bullet_point, quality)
        enhanced_desc = self._enhance_description(description, quality)
        
        return {
            'title': enhanced_title,
            'bullet_point': enhanced_bullet,
            'description': enhanced_desc,
            'quality_score': quality.score,
            'suggestions': quality.suggestions
        }
    
    def _enhance_title(self, title: str) -> str:
        """Enhance section title for impact."""
        # Ensure title starts with strong action verb
        strong_verbs = {
            'built': 'Architected',
            'made': 'Implemented', 
            'created': 'Developed',
            'improved': 'Optimized',
            'fixed': 'Resolved',
            'updated': 'Enhanced',
            'added': 'Delivered'
        }
        
        enhanced = title
        for weak, strong in strong_verbs.items():
            if enhanced.lower().startswith(weak):
                enhanced = enhanced.replace(weak, strong, 1)
                break
        
        # Ensure outcome focus
        if not any(word in enhanced.lower() for word in ['performance', 'efficiency', 'reliability', 'scalability', 'delivery']):
            # Try to infer outcome from content
            if 'api' in enhanced.lower():
                enhanced = enhanced.replace('API', 'API Performance').replace('api', 'API Performance')
        
        return enhanced
    
    def _enhance_bullet_point(self, bullet_point: str, quality: SectionQuality) -> str:
        """Enhance bullet point for impact."""
        enhanced = bullet_point.strip()
        
        # Remove redundant words
        redundant_phrases = ['successfully', 'effectively', 'efficiently']
        for phrase in redundant_phrases:
            enhanced = enhanced.replace(phrase, '').strip()
        
        # Ensure it ends with <br />
        if not enhanced.endswith('<br />'):
            enhanced = enhanced.rstrip('.') + ' <br />'
        
        return enhanced
    
    def _enhance_description(self, description: str, quality: SectionQuality) -> str:
        """Enhance description based on quality gaps."""
        enhanced = description.strip()
        
        # Fix passive voice where possible
        passive_fixes = {
            'was implemented': 'implemented',
            'was created': 'created',
            'was developed': 'developed',
            'were improved': 'improved',
            'has been': 'is'
        }
        
        for passive, active in passive_fixes.items():
            enhanced = enhanced.replace(passive, active)
        
        return enhanced
    
    def format_complete_output(self, sections: List[Dict[str, str]], 
                             repo_title: str, person_name: str) -> str:
        """Format complete output with quality enhancements."""
        output_lines = [f"# {repo_title}", ""]
        
        # Add quality summary
        if sections:
            avg_quality = sum(s.get('quality_score', 0) for s in sections) / len(sections)
            quality_indicator = "🔥" if avg_quality > 0.8 else "✨" if avg_quality > 0.6 else "📝"
            output_lines.append(f"*{quality_indicator} Enhanced CV content generated for {person_name}*")
            output_lines.append("")
        
        # Format sections
        for section in sections:
            output_lines.extend([
                f"## {section['title']}",
                f"**Bullet Point:** {section['bullet_point']}",
                f"**Description:** {section['description']}",
                ""
            ])
        
        return "\n".join(output_lines)
    
    def validate_output_quality(self, output_text: str) -> Dict[str, Any]:
        """Validate overall output quality."""
        sections = self._extract_sections(output_text)
        
        if not sections:
            return {
                'valid': False,
                'issues': ['No valid sections found'],
                'suggestions': ['Check section formatting']
            }
        
        issues = []
        suggestions = []
        quality_scores = []
        
        for i, section in enumerate(sections, 1):
            title = section.get('title', '')
            bullet = section.get('bullet_point', '')
            desc = section.get('description', '')
            
            if not title or not bullet or not desc:
                issues.append(f"Section {i}: Missing required components")
                continue
            
            quality = self.assess_section_quality(title, bullet, desc)
            quality_scores.append(quality.score)
            
            if quality.score < 0.5:
                issues.append(f"Section {i} '{title}': Low quality score ({quality.score:.1f})")
                suggestions.extend([f"Section {i}: {s}" for s in quality.suggestions])
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            'valid': len(issues) == 0,
            'average_quality': avg_quality,
            'section_count': len(sections),
            'issues': issues,
            'suggestions': suggestions[:5],  # Limit to top 5 suggestions
            'quality_distribution': {
                'high': len([s for s in quality_scores if s > 0.8]),
                'medium': len([s for s in quality_scores if 0.5 <= s <= 0.8]),
                'low': len([s for s in quality_scores if s < 0.5])
            }
        }
    
    def _extract_sections(self, text: str) -> List[Dict[str, str]]:
        """Extract sections from formatted text."""
        sections = []
        lines = text.split('\n')
        
        current_section = {}
        for line in lines:
            line = line.strip()
            if line.startswith('## '):
                if current_section:
                    sections.append(current_section)
                current_section = {'title': line[3:].strip()}
            elif line.startswith('**Bullet Point:**'):
                current_section['bullet_point'] = line[17:].strip()
            elif line.startswith('**Description:**'):
                current_section['description'] = line[16:].strip()
        
        if current_section:
            sections.append(current_section)
        
        return sections