"""Tests for enhanced features."""
import os
import sys
import tempfile
import yaml
from unittest.mock import patch, MagicMock

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.config import Config, ConfigError
from utils.progress import ProgressTracker
from tools.enhanced_formatting import EnhancedFormatter
from analyzers.signal_analyzer import EnhancedSignalAnalyzer
import pytest


def test_config_validation():
    """Test configuration validation."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            'you': {
                'full_name': 'Test User',
                'emails': ['test@example.com']
            },
            'git': {'since': '2023-01-01'},
            'analysis': {'max_files': 1000},
            'output': {'bullets_count': 5}
        }, f)
        f.flush()
        
        config = Config(f.name)
        assert config.person_name == 'Test User'
        assert config.bullets_count == 5
        
        os.unlink(f.name)


def test_config_validation_missing_fields():
    """Test configuration validation with missing fields."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            'you': {'full_name': 'Test User'},  # Missing emails
            'git': {},
            'analysis': {},
            'output': {}
        }, f)
        f.flush()
        
        with pytest.raises(ConfigError, match="emails.*must be a non-empty list"):
            Config(f.name)
        
        os.unlink(f.name)


def test_progress_tracker():
    """Test progress tracking functionality."""
    import io
    output = io.StringIO()
    tracker = ProgressTracker(verbose=True, output=output)
    
    tracker.set_total_steps(3)
    tracker.step("Step 1", "Details for step 1")
    tracker.step("Step 2")
    tracker.success("Operation completed")
    
    output_text = output.getvalue()
    assert "[1/3]" in output_text
    assert "[2/3]" in output_text
    assert "Step 1" in output_text
    assert "Details for step 1" in output_text
    assert "✓" in output_text


def test_enhanced_formatter_quality_assessment():
    """Test section quality assessment."""
    formatter = EnhancedFormatter()
    
    # High quality section
    title = "Optimized Database Performance"
    bullet = "Reduced query latency by 45% and improved throughput 3x through Redis caching <br />"
    desc = "Implemented comprehensive database optimization using PostgreSQL query optimization and Redis caching layer. The changes affected 12 critical API endpoints and reduced P95 latency from 800ms to 440ms."
    
    quality = formatter.assess_section_quality(title, bullet, desc)
    
    assert quality.has_metrics  # Contains percentages and numbers
    assert quality.has_technical_terms  # Contains Redis, PostgreSQL, API
    assert quality.score > 0.7  # Should be high quality


def test_enhanced_formatter_low_quality():
    """Test detection of low quality sections."""
    formatter = EnhancedFormatter()
    
    # Low quality section
    title = "Worked on stuff"
    bullet = "Did some programming work <br />"
    desc = "Made changes to files."
    
    quality = formatter.assess_section_quality(title, bullet, desc)
    
    assert not quality.has_metrics
    assert not quality.has_technical_terms
    assert quality.score < 0.3
    assert len(quality.suggestions) > 0


@patch('analyzers.signal_analyzer.load_git_history')
@patch('analyzers.signal_analyzer.walk_code')
@patch('analyzers.signal_analyzer.load_github_issues_prs')
def test_signal_analyzer_integration(mock_github, mock_walk, mock_git):
    """Test enhanced signal analyzer integration."""
    # Mock dependencies
    mock_git.return_value = [
        {
            'hexsha': 'abc123',
            'message': 'optimize database performance',
            'files': ['db/queries.py', 'api/endpoints.py'],
            'insertions': 150,
            'deletions': 80,
            'author_name': 'Test User',
            'author_email': 'test@example.com',
            'authored_datetime': '2023-06-01T10:00:00'
        }
    ]
    
    mock_walk.return_value = ['file1.py', 'file2.js']
    mock_github.return_value = {'issues': [], 'prs': []}
    
    # Create config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            'you': {
                'full_name': 'Test User',
                'aliases': ['Test User'],
                'emails': ['test@example.com']
            },
            'git': {'since': '2023-01-01', 'until': '2023-12-31'},
            'analysis': {'max_files': 1000, 'hot_file_top_n': 10, 'languages_of_interest': ['py', 'js']},
            'output': {'bullets_count': 5}
        }, f)
        f.flush()
        
        config = Config(f.name)
        progress = ProgressTracker(verbose=False)
        
        analyzer = EnhancedSignalAnalyzer(config, progress)
        
        # Mock the file operations
        with patch('builtins.open'), patch('json.dump'), patch('os.makedirs'):
            signals = analyzer.collect_enhanced_signals()
        
        assert 'commits_you' in signals
        assert 'summary_you' in signals
        assert 'commit_patterns' in signals
        assert 'impact_signals' in signals
        
        os.unlink(f.name)


def test_section_extraction():
    """Test section extraction from formatted text."""
    formatter = EnhancedFormatter()
    
    text = """# Repository
    
## Database Optimization
**Bullet Point:** Improved query performance by 50% <br />
**Description:** Optimized PostgreSQL queries and added Redis caching.

## API Development  
**Bullet Point:** Built REST API with 99.9% uptime <br />
**Description:** Developed microservices architecture using FastAPI and Docker.
"""
    
    sections = formatter._extract_sections(text)
    
    assert len(sections) == 2
    assert sections[0]['title'] == 'Database Optimization'
    assert 'Improved query performance' in sections[0]['bullet_point']
    assert 'PostgreSQL' in sections[0]['description']
    assert sections[1]['title'] == 'API Development'


if __name__ == '__main__':
    pytest.main([__file__])