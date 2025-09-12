import os
from collections import Counter, defaultdict

def walk_code(repo_path, exts=None, max_files=2000):
    files = []
    for root, _, fns in os.walk(repo_path):
        for fn in fns:
            p = os.path.join(root, fn)
            if exts and not any(p.endswith(f".{e}") for e in exts):
                continue
            files.append(p)
            if len(files) >= max_files:
                return files
    return files

def language_breakdown(files):
    lang = Counter()
    for f in files:
        ext = f.split(".")[-1].lower()
        lang[ext] += 1
    return dict(lang)

def simple_component_detection(files):
    buckets = defaultdict(list)
    for f in files:
        lower = f.lower()
        if any(k in lower for k in ["api", "controller", "router", "endpoint"]):
            buckets["api"].append(f)
        if any(k in lower for k in ["service", "usecase", "domain"]):
            buckets["services"].append(f)
        if any(k in lower for k in ["model", "entity", "schema", "dto"]):
            buckets["models"].append(f)
        if any(k in lower for k in ["infra", "adapter", "db", "repository", "persistence"]):
            buckets["infrastructure"].append(f)
        if any(k in lower for k in ["ui", "view", "component", "page"]):
            buckets["frontend"].append(f)
        if any(k in lower for k in ["test", "spec", "e2e", "integration"]):
            buckets["tests"].append(f)
    return {k: sorted(v) for k, v in buckets.items()}
