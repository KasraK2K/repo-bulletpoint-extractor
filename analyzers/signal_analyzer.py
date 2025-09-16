"""Enhanced signal analysis for better attribution and impact assessment."""
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass

from utils.config import Config
from utils.progress import ProgressTracker
from tools.git_repo import load_git_history, contributions_by_user, hot_files
from tools.github_api import load_github_issues_prs
from tools.code_scan import walk_code, language_breakdown, simple_component_detection


@dataclass
class CommitPattern:
    """Represents a pattern of commits suggesting a larger effort."""
    theme: str
    commits: List[Dict[str, Any]]
    files_affected: List[str]
    time_span: Tuple[datetime, datetime]
    total_changes: int
    complexity_score: int


@dataclass
class ImpactSignal:
    """Represents a signal of significant impact."""
    type: str  # 'performance', 'architecture', 'feature', 'reliability', etc.
    evidence: List[str]
    estimated_impact: str
    confidence: float
    files_involved: List[str]
    metrics_hints: List[str]


class EnhancedSignalAnalyzer:
    """Enhanced signal collection with better pattern detection and attribution."""
    
    def __init__(self, config: Config, progress: ProgressTracker):
        self.config = config
        self.progress = progress
        self.repo_path = os.getenv("REPO_PATH", ".")
    
    def collect_enhanced_signals(self) -> Dict[str, Any]:
        """Collect and analyze signals with enhanced pattern detection."""
        self.progress.set_total_steps(6)
        
        # Step 1: Git History Analysis
        with self.progress.step_context("Analyzing git history with pattern detection"):
            commits = self._load_git_history()
            yours, others = contributions_by_user(
                commits, self.config.person_aliases, self.config.person_emails
            )
            
            self.progress.info(f"Found {len(commits)} total commits, {len(yours)} are yours")
        
        # Step 2: Enhanced Commit Analysis
        with self.progress.step_context("Detecting commit patterns and themes"):
            commit_patterns = self._detect_commit_patterns(yours)
            impact_signals = self._detect_impact_signals(yours)
            
            self.progress.info(f"Detected {len(commit_patterns)} patterns, {len(impact_signals)} impact signals")
        
        # Step 3: Codebase Structure Analysis
        with self.progress.step_context("Analyzing codebase structure and ownership"):
            files = walk_code(
                self.repo_path, 
                self.config.languages_of_interest, 
                self.config.max_files
            )
            langs = language_breakdown(files)
            components = simple_component_detection(files)
            ownership_map = self._calculate_file_ownership(yours, files)
            
            self.progress.info(f"Analyzed {len(files)} files across {len(langs)} languages")
        
        # Step 4: GitHub Integration
        with self.progress.step_context("Fetching GitHub issues and PRs"):
            owner = os.getenv("GITHUB_OWNER", "")
            repo = os.getenv("GITHUB_REPO", "")
            issues_prs = load_github_issues_prs(owner, repo)
            pr_analysis = self._analyze_pr_patterns(issues_prs.get('prs', []))
            
            self.progress.info(f"Analyzed {len(issues_prs.get('issues', []))} issues, {len(issues_prs.get('prs', []))} PRs")
        
        # Step 5: Impact Assessment
        with self.progress.step_context("Calculating impact metrics and confidence scores"):
            base_summary = self._enhanced_summary(yours)
            top_files = hot_files(yours, top_n=self.config.hot_file_top_n)
            
        # Step 6: Signal Compilation
        with self.progress.step_context("Compiling comprehensive signal dataset"):
            payload = self._compile_signals(
                yours, base_summary, top_files, langs, components,
                commit_patterns, impact_signals, ownership_map, pr_analysis,
                issues_prs
            )
            
            # Save enhanced signals
            os.makedirs("output", exist_ok=True)
            with open("output/signals.json", "w") as f:
                json.dump(payload, f, indent=2, default=str)
        
        self.progress.success("Enhanced signal analysis complete")
        return payload
    
    def _load_git_history(self) -> List[Dict[str, Any]]:
        """Load git history with enhanced metadata."""
        return load_git_history(
            self.repo_path,
            self.config.git_since,
            self.config.git_until,
            self.config.include_merge_commits
        )
    
    def _detect_commit_patterns(self, commits: List[Dict[str, Any]]) -> List[CommitPattern]:
        """Detect patterns in commits that suggest larger efforts."""
        patterns = []
        
        # Group commits by time windows and file patterns
        time_windows = self._group_commits_by_time(commits, days=7)
        
        for window_commits in time_windows:
            if len(window_commits) < 3:  # Minimum commits for a pattern
                continue
            
            # Analyze file patterns
            all_files = set()
            for commit in window_commits:
                all_files.update(commit.get('files', []))
            
            # Look for common themes in commit messages
            messages = [c.get('message', '') for c in window_commits]
            theme = self._extract_theme(messages)
            
            if theme and len(all_files) > 1:  # Multi-file effort
                total_changes = sum(
                    c.get('insertions', 0) + c.get('deletions', 0) 
                    for c in window_commits
                )
                
                complexity_score = self._calculate_complexity_score(
                    window_commits, list(all_files)
                )
                
                pattern = CommitPattern(
                    theme=theme,
                    commits=window_commits,
                    files_affected=list(all_files),
                    time_span=(
                        min(c['authored_datetime'] for c in window_commits),
                        max(c['authored_datetime'] for c in window_commits)
                    ),
                    total_changes=total_changes,
                    complexity_score=complexity_score
                )
                patterns.append(pattern)
        
        return sorted(patterns, key=lambda p: p.complexity_score, reverse=True)
    
    def _detect_impact_signals(self, commits: List[Dict[str, Any]]) -> List[ImpactSignal]:
        """Detect signals of significant impact from commits."""
        signals = []
        
        # Performance-related keywords
        perf_keywords = ['optimize', 'performance', 'speed', 'latency', 'cache', 'async', 'parallel']
        arch_keywords = ['refactor', 'architecture', 'design', 'pattern', 'structure', 'migration']
        reliability_keywords = ['fix', 'bug', 'error', 'exception', 'test', 'security', 'validation']
        feature_keywords = ['add', 'implement', 'feature', 'endpoint', 'api', 'ui', 'component']
        
        keyword_groups = {
            'performance': perf_keywords,
            'architecture': arch_keywords,
            'reliability': reliability_keywords,
            'feature': feature_keywords
        }
        
        for signal_type, keywords in keyword_groups.items():
            matching_commits = []
            for commit in commits:
                message = commit.get('message', '').lower()
                if any(keyword in message for keyword in keywords):
                    matching_commits.append(commit)
            
            if matching_commits:
                # Estimate impact based on files and changes
                all_files = set()
                total_changes = 0
                for commit in matching_commits:
                    all_files.update(commit.get('files', []))
                    total_changes += commit.get('insertions', 0) + commit.get('deletions', 0)
                
                confidence = min(1.0, len(matching_commits) / 10.0 + total_changes / 1000.0)
                
                signal = ImpactSignal(
                    type=signal_type,
                    evidence=[c.get('message', '')[:100] for c in matching_commits[:5]],
                    estimated_impact=self._estimate_impact_level(total_changes, len(all_files)),
                    confidence=confidence,
                    files_involved=list(all_files),
                    metrics_hints=self._generate_metrics_hints(signal_type, total_changes, len(all_files))
                )
                signals.append(signal)
        
        return signals
    
    def _group_commits_by_time(self, commits: List[Dict[str, Any]], days: int = 7) -> List[List[Dict[str, Any]]]:
        """Group commits into time windows."""
        if not commits:
            return []
        
        # Sort commits by time
        sorted_commits = sorted(commits, key=lambda c: c['authored_datetime'])
        
        windows = []
        current_window = []
        window_start = None
        
        for commit in sorted_commits:
            commit_time = datetime.fromisoformat(commit['authored_datetime'].replace('Z', '+00:00'))
            
            if window_start is None:
                window_start = commit_time
                current_window = [commit]
            elif commit_time - window_start <= timedelta(days=days):
                current_window.append(commit)
            else:
                if len(current_window) > 1:
                    windows.append(current_window)
                window_start = commit_time
                current_window = [commit]
        
        if len(current_window) > 1:
            windows.append(current_window)
        
        return windows
    
    def _extract_theme(self, messages: List[str]) -> Optional[str]:
        """Extract common theme from commit messages."""
        # Simple keyword extraction
        words = []
        for msg in messages:
            words.extend(msg.lower().split())
        
        # Count frequency of meaningful words
        meaningful_words = [w for w in words if len(w) > 3 and w.isalpha()]
        if not meaningful_words:
            return None
        
        word_counts = Counter(meaningful_words)
        most_common = word_counts.most_common(3)
        
        # Return theme if there's a clear pattern
        if most_common and most_common[0][1] >= 2:
            return most_common[0][0].title()
        
        return None
    
    def _calculate_complexity_score(self, commits: List[Dict[str, Any]], files: List[str]) -> int:
        """Calculate complexity score for a pattern."""
        base_score = len(commits) * 10
        file_diversity_score = len(set(os.path.dirname(f) for f in files)) * 5
        change_volume_score = sum(
            c.get('insertions', 0) + c.get('deletions', 0) for c in commits
        ) // 100
        
        return base_score + file_diversity_score + change_volume_score
    
    def _estimate_impact_level(self, total_changes: int, files_count: int) -> str:
        """Estimate impact level based on changes and files."""
        if total_changes > 1000 or files_count > 10:
            return "High"
        elif total_changes > 200 or files_count > 3:
            return "Medium"
        else:
            return "Low"
    
    def _generate_metrics_hints(self, signal_type: str, changes: int, files: int) -> List[str]:
        """Generate realistic metrics hints based on signal type."""
        hints = []
        
        if signal_type == 'performance':
            hints.extend([
                f"~{min(50, changes//20)}% latency reduction estimate",
                f"~{min(3, files)}x throughput improvement potential"
            ])
        elif signal_type == 'reliability':
            hints.extend([
                f"~{min(90, changes//10)}% error reduction estimate",
                f"Affected {files} critical modules"
            ])
        elif signal_type == 'architecture':
            hints.extend([
                f"Refactored {files} components",
                f"~{changes} lines of architectural changes"
            ])
        elif signal_type == 'feature':
            hints.extend([
                f"Delivered {files} new components",
                f"~{changes} lines of feature code"
            ])
        
        return hints
    
    def _calculate_file_ownership(self, commits: List[Dict[str, Any]], all_files: List[str]) -> Dict[str, float]:
        """Calculate ownership percentage for each file."""
        file_commit_counts = defaultdict(int)
        
        for commit in commits:
            for file_path in commit.get('files', []):
                file_commit_counts[file_path] += 1
        
        # Calculate ownership as percentage of total activity in each file
        ownership_map = {}
        for file_path, count in file_commit_counts.items():
            # This is simplified - in reality you'd compare against all contributors
            ownership_map[file_path] = min(1.0, count / 10.0)  # Assume high ownership after 10+ commits
        
        return ownership_map
    
    def _analyze_pr_patterns(self, prs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze PR patterns for additional insights."""
        if not prs:
            return {}
        
        authored_prs = [pr for pr in prs if pr.get('user') in self.config.person_aliases]
        
        return {
            'total_authored': len(authored_prs),
            'merged_count': len([pr for pr in authored_prs if pr.get('merged', False)]),
            'avg_additions': sum(pr.get('additions', 0) for pr in authored_prs) / max(1, len(authored_prs)),
            'avg_deletions': sum(pr.get('deletions', 0) for pr in authored_prs) / max(1, len(authored_prs)),
            'large_prs': len([pr for pr in authored_prs if pr.get('additions', 0) > 500])
        }
    
    def _enhanced_summary(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate enhanced summary with additional metrics."""
        total_insert = sum(c["insertions"] for c in commits)
        total_delete = sum(c["deletions"] for c in commits)
        total_commits = len(commits)
        
        files_touched = set()
        directories_touched = set()
        
        for c in commits:
            for f in c["files"]:
                files_touched.add(f)
                directories_touched.add(os.path.dirname(f))
        
        # Calculate activity timeline
        if commits:
            commit_dates = [datetime.fromisoformat(c['authored_datetime'].replace('Z', '+00:00')) for c in commits]
            date_range = max(commit_dates) - min(commit_dates)
            avg_commits_per_week = total_commits / max(1, date_range.days / 7)
        else:
            avg_commits_per_week = 0
        
        return {
            "total_commits": total_commits,
            "total_insertions": total_insert,
            "total_deletions": total_delete,
            "net_lines": total_insert - total_delete,
            "files_touched_count": len(files_touched),
            "directories_touched_count": len(directories_touched),
            "files_touched": sorted(files_touched),
            "avg_commits_per_week": round(avg_commits_per_week, 1),
            "largest_single_commit": max((c["insertions"] + c["deletions"] for c in commits), default=0)
        }
    
    def _compile_signals(self, yours: List[Dict[str, Any]], summary: Dict[str, Any], 
                        top_files: List[Tuple[str, int]], langs: Dict[str, int], 
                        components: Dict[str, List[str]], patterns: List[CommitPattern],
                        impact_signals: List[ImpactSignal], ownership_map: Dict[str, float],
                        pr_analysis: Dict[str, Any], issues_prs: Dict[str, Any]) -> Dict[str, Any]:
        """Compile all signals into comprehensive dataset."""
        
        # Limit data for prompt efficiency
        compact_commits = []
        for c in yours[-200:]:  # Last 200 commits
            compact_commits.append({
                "sha": c.get("hexsha", "")[:10],
                "msg": (c.get("message", "") or "").split("\n", 1)[0][:140],
                "files": c.get("files", [])[:10],
                "insertions": c.get("insertions", 0),
                "deletions": c.get("deletions", 0),
                "date": c.get("authored_datetime", "")[:10]
            })
        
        return {
            "metadata": {
                "person_name": self.config.person_name,
                "analysis_date": datetime.now().isoformat(),
                "repo_path": self.repo_path
            },
            "commits_you": compact_commits,
            "summary_you": summary,
            "top_files_you": top_files[:30],
            "languages": langs,
            "components": components,
            "commit_patterns": [
                {
                    "theme": p.theme,
                    "commit_count": len(p.commits),
                    "files_affected": p.files_affected[:20],
                    "total_changes": p.total_changes,
                    "complexity_score": p.complexity_score
                } for p in patterns[:10]
            ],
            "impact_signals": [
                {
                    "type": s.type,
                    "evidence": s.evidence,
                    "estimated_impact": s.estimated_impact,
                    "confidence": s.confidence,
                    "files_count": len(s.files_involved),
                    "metrics_hints": s.metrics_hints
                } for s in impact_signals
            ],
            "ownership_map": {k: v for k, v in ownership_map.items() if v > 0.3},  # Only significant ownership
            "pr_analysis": pr_analysis,
            "issues": issues_prs.get("issues", [])[:100],
            "prs": issues_prs.get("prs", [])[:100]
        }