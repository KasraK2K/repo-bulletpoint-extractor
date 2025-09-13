from git import Repo
from datetime import datetime
from collections import defaultdict
import os
import re

def load_git_history(repo_path, since=None, until=None, include_merges=False):
    repo = Repo(repo_path)
    assert not repo.bare, "Repo is bare"
    rev = "HEAD"
    kwargs = {}
    if since: kwargs["since"] = since
    if until: kwargs["until"] = until
    if not include_merges: kwargs["no_merges"] = True

    commits = list(repo.iter_commits(rev, **kwargs))
    out = []
    for c in commits:
        out.append({
            "hexsha": c.hexsha,
            "author_name": c.author.name,
            "author_email": c.author.email,
            "authored_datetime": c.authored_datetime.isoformat(),
            "message": c.message.strip(),
            # c.stats.files is a dict keyed by file path strings
            "files": list(c.stats.files.keys()),
            "insertions": c.stats.total["insertions"],
            "deletions": c.stats.total["deletions"]
        })
    return out

def contributions_by_user(commits, aliases, emails):
    def is_you(a_name, a_email):
        return (a_name in aliases) or (a_email in emails)
    yours = [c for c in commits if is_you(c["author_name"], c["author_email"])]
    others = [c for c in commits if c not in yours]
    return yours, others

def summarize_impact(commits):
    total_insert = sum(c["insertions"] for c in commits)
    total_delete = sum(c["deletions"] for c in commits)
    total_commits = len(commits)
    files_touched = set()
    for c in commits:
        for f in c["files"]:
            files_touched.add(f)
    return {
        "total_commits": total_commits,
        "total_insertions": total_insert,
        "total_deletions": total_delete,
        "files_touched_count": len(files_touched),
        "files_touched": sorted(files_touched)
    }

def hot_files(commits, top_n=50):
    freq = defaultdict(int)
    for c in commits:
        for f in c["files"]:
            freq[f] += 1
    ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_n]

def get_github_owner_repo(repo_path: str):
    """Attempt to derive GitHub owner/repo from the git remote URL.

    Supports SSH and HTTPS remotes, e.g.:
    - git@github.com:owner/repo.git
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo
    Returns (owner, repo) or (None, None) if not found/parsable.
    """
    try:
        repo = Repo(repo_path)
        url = None
        try:
            url = next(repo.remote("origin").urls)
        except Exception:
            # No origin remote
            return None, None
        if not url:
            return None, None
        # Normalize
        # SSH: git@github.com:owner/repo.git
        m = re.match(r"git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$", url)
        if not m:
            # HTTPS: https://github.com/owner/repo(.git)?
            m = re.match(r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?(?:/)?$", url)
        if m:
            owner = m.group("owner")
            repo_name = m.group("repo")
            # Strip .git if still present
            repo_name = re.sub(r"\.git$", "", repo_name)
            return owner, repo_name
        return None, None
    except Exception:
        return None, None
