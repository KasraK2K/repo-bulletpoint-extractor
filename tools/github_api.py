import os
from github import Github

def load_github_issues_prs(owner, repo):
    token = os.getenv("GITHUB_TOKEN")
    # Require token and valid owner/repo; otherwise skip network
    if not token or not owner or not repo or owner == "your-org-or-username" or repo == "your-repo-name":
        return {"issues": [], "prs": []}

    try:
        gh = Github(token, per_page=100)
        r = gh.get_repo(f"{owner}/{repo}")
        issues = []
        prs = []

        for i in r.get_issues(state="all"):
            issues.append({
                "id": i.id, "number": i.number, "title": i.title,
                "state": i.state, "user": i.user.login if i.user else None,
                "created_at": i.created_at.isoformat() if i.created_at else None,
                "closed_at": i.closed_at.isoformat() if i.closed_at else None,
                "comments": i.comments, "labels": [l.name for l in i.labels],
                "assignees": [a.login for a in i.assignees],
                "is_pr": i.pull_request is not None,
                "body": (i.body or "")[:4000]
            })

        for p in r.get_pulls(state="all"):
            comments = list(p.get_comments()) + list(p.get_review_comments())
            prs.append({
                "number": p.number, "title": p.title, "state": p.state,
                "user": p.user.login if p.user else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "closed_at": p.closed_at.isoformat() if p.closed_at else None,
                "merged": p.is_merged(),
                "additions": p.additions, "deletions": p.deletions, "changed_files": p.changed_files,
                "labels": [l.name for l in p.get_labels()],
                "assignees": [a.login for a in p.assignees],
                "comments_count": len(comments),
                "comments_sample": [c.body[:1000] for c in comments[:10]]
            })
        return {"issues": issues, "prs": prs}
    except Exception:
        # Network errors or API issues: degrade gracefully
        return {"issues": [], "prs": []}
