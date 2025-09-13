import os
import sys
import tempfile

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.formatting import (
    normalize_proof_links,
    sanitize_proof_links,
    remove_links,
    validate_and_autofix_sections,
)
from tools.git_repo import get_github_owner_repo
from git import Repo


def test_normalize_proof_links_replaces_placeholder():
    text = (
        "Ref: [Proof](https://github.com/project/repo/commit/abc123) and "
        "[Proof](https://github.com/project/repo/pull/42)."
    )
    out = normalize_proof_links(text, "owner", "repo")
    assert "https://github.com/owner/repo/commit/abc123" in out
    assert "https://github.com/owner/repo/pull/42" in out


def test_remove_links_strips_markdown_and_urls():
    text = (
        "See [Proof](https://example.com/path) and https://example.org/raw."
    )
    out = remove_links(text)
    assert "[Proof]" not in out
    assert "https://example.org" not in out


def test_validate_and_autofix_sections_from_paragraph():
    text = """# Title\n\n## Section One\nThis is the first sentence. The rest explains more.\n\n## Section Two\nBullet Point: Already present\nDescription: Existing description."""
    fixed = validate_and_autofix_sections(text)
    assert "## Section One" in fixed
    assert "Bullet Point: This is the first sentence." in fixed
    assert "Description: The rest explains more." in fixed
    # Ensure labels preserved for section two
    assert "Bullet Point: Already present" in fixed
    assert "Description: Existing description." in fixed


def test_get_github_owner_repo_from_remote():
    with tempfile.TemporaryDirectory() as d:
        repo = Repo.init(d)
        repo.create_remote('origin', url='git@github.com:someowner/somerepo.git')
        owner, name = get_github_owner_repo(d)
        assert owner == 'someowner'
        assert name == 'somerepo'
