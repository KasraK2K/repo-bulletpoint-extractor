import re

def normalize_proof_links(text: str, owner: str, repo: str) -> str:
    if not text or not owner or not repo:
        return text
    base = f"https://github.com/{owner}/{repo}/"
    placeholders = [
        "https://github.com/project/repo/",
        "https://github.com/your-org-or-username/your-repo-name/",
        "https://github.com/org/repo/",
        "https://github.com/owner/repo/",
        "https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/",
        "https://github.com/${owner}/${repo}/",
        "https://github.com/<owner>/<repo>/",
        "https://github.com/<ORG>/<REPO>/",
    ]
    for ph in placeholders:
        text = text.replace(ph, base)
    return text

def sanitize_proof_links(text: str) -> str:
    if not text:
        return text
    def repl(m):
        url = m.group(1)
        if "/commit/" in url:
            sha = url.rsplit("/commit/", 1)[-1].split("/", 1)[0]
            if re.fullmatch(r"[0-9a-fA-F]{7,40}", sha):
                return m.group(0)
            return ""
        if "/pull/" in url:
            num = url.rsplit("/pull/", 1)[-1].split("/", 1)[0]
            if re.fullmatch(r"\d+", num):
                return m.group(0)
            return ""
        return m.group(0)
    text = re.sub(r"\[Proof\]\(([^)]+)\)", repl, text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text

def remove_links(text: str) -> str:
    if not text:
        return text
    # Remove [text](url) -> keep only text
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    # Remove bare URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove lingering 'Proof' tokens if any
    text = text.replace("Proof:", "").replace("Proof", "")
    return text

def validate_and_autofix_sections(text: str) -> str:
    """Ensure output conforms to:
    ## Title
    **Bullet Point:** ... <br />
    **Description:** ...
    - Remove list items
    - Upgrade 'bulletpoint:'/'bullet-point:' and 'description:' to capitalized labels
    - If only a paragraph exists after title, split first sentence into Bullet Point and rest into Description
    """
    if not text:
        return text
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Preserve H1
        if i == 0 and line.startswith('# '):
            out.append(line)
            i += 1
            continue
        # Drop list items entirely
        if line.lstrip().startswith('- '):
            i += 1
            continue
        # Pass through blank lines
        if line.strip() == '':
            out.append(line)
            i += 1
            continue
        # Section logic
        if line.startswith('## '):
            out.append(line.strip())
            # Collect following non-heading lines until next heading or EOF
            body = []
            i += 1
            while i < len(lines) and not lines[i].startswith('## '):
                # Skip bullet list markers inside body
                if not lines[i].lstrip().startswith('- '):
                    body.append(lines[i])
                i += 1
            body_text = '\n'.join([b for b in body if b is not None]).strip()
            # Normalize existing labels
            body_text = re.sub(r'(?im)^bullet\s*[- ]?point\s*:\s*', '**Bullet Point:** ', body_text)
            body_text = re.sub(r'(?im)^description\s*:\s*', '**Description:** ', body_text)
            # If labels already present, ensure exactly one of each, in order
            if re.search(r'(?m)^\*\*Bullet Point:\*\*\s*', body_text) or re.search(r'(?m)^\*\*Description:\*\*\s*', body_text):
                # Extract or synthesize missing pieces
                bp = None
                desc = None
                for m in re.finditer(r'(?m)^\*\*(Bullet Point|Description):\*\*\s*(.*)$', body_text):
                    key = m.group(1)
                    val = m.group(2).strip()
                    # Strip trailing <br /> tokens from values
                    val = re.sub(r"(\s*<br\s*/?>\s*)+$", "", val, flags=re.I)
                    if key == 'Bullet Point' and bp is None:
                        bp = val
                    elif key == 'Description' and desc is None:
                        desc = val
                # If no desc, take remaining lines as desc
                if desc is None:
                    rest = re.sub(r'(?m)^\*\*Bullet Point:\*\*\s*.*$', '', body_text).strip()
                    desc = rest if rest else 'Summary not provided.'
                if bp is None:
                    # Use first sentence of desc as bullet point
                    first_sentence = re.split(r'(?<=[.!?])\s+', desc, 1)[0]
                    bp = first_sentence
                out.append(f'**Bullet Point:** {bp} <br />')
                out.append(f'**Description:** {desc}')
            else:
                # No labels; create from body_text
                if not body_text:
                    out.append('**Bullet Point:** Summary unavailable. <br />')
                    out.append('**Description:** Details unavailable.')
                else:
                    sentences = re.split(r'(?<=[.!?])\s+', body_text.strip(), 1)
                    bp = sentences[0].strip()
                    desc = sentences[1].strip() if len(sentences) > 1 else body_text.strip()
                    out.append(f'**Bullet Point:** {bp} <br />')
                    out.append(f'**Description:** {desc}')
            continue
        # Any other line, keep as-is
        out.append(line)
        i += 1
    return '\n'.join(out)
