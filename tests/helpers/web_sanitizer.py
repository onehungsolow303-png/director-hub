"""Web content sanitizer for agent security.

Sanitizes web-fetched content before it enters agent context.
Detects prompt injection attempts, strips dangerous elements,
and scores risk level. Flags suspicious content for user review.
"""

import re
import html
from urllib.parse import urlparse

# ── Trusted domains ───────────────────────────────────────────────────

TRUSTED_DOMAINS = {
    "github.com", "raw.githubusercontent.com", "stackoverflow.com",
    "arxiv.org", "docs.opencv.org", "scikit-image.org", "pypi.org",
    "developer.mozilla.org", "en.wikipedia.org",
}

SEMI_TRUSTED_DOMAINS = {
    "medium.com", "dev.to", "huggingface.co", "towardsdatascience.com",
    "blog.cloudflare.com",
}

# ── Injection patterns ────────────────────────────────────────────────

# (pattern_regex, risk_points, description)
INJECTION_PATTERNS = [
    # High risk (3 points)
    (r"(?i)ignore\s+(all\s+)?previous\s+instructions?", 3, "Instruction override attempt"),
    (r"(?i)you\s+are\s+now\b", 3, "Role reassignment attempt"),
    (r"(?i)system\s*prompt\s*:", 3, "System prompt injection"),
    (r"(?i)forget\s+(all\s+|your\s+|previous\s+)", 3, "Memory wipe attempt"),
    (r"(?i)disregard\s+(all\s+|your\s+|previous\s+)", 3, "Disregard attempt"),
    (r"(?i)<\s*system\s*>", 3, "System tag injection"),
    # Medium risk (2 points)
    (r"(?i)act\s+as\s+(a\s+|an\s+)?", 2, "Role-play trigger"),
    (r"(?i)pretend\s+(you\s+are|to\s+be)", 2, "Persona change trigger"),
    (r"(?i)reveal\s+(your\s+)?(system\s+)?prompt", 2, "Prompt extraction attempt"),
    (r"(?i)what\s+are\s+your\s+(instructions|rules|system)", 2, "Rule extraction attempt"),
    (r"(?i)output\s+your\s+(system|initial)\s+prompt", 2, "Prompt leak attempt"),
    # Low risk (1 point)
    (r"(?i)api[_\s]?key", 1, "API key reference"),
    (r"(?i)password\s*[:=]", 1, "Password reference"),
    (r"(?i)secret\s*[:=]", 1, "Secret reference"),
    (r"(?i)token\s*[:=]", 1, "Token reference"),
]

# ── Dangerous HTML elements ───────────────────────────────────────────

DANGEROUS_TAGS = re.compile(
    r"<\s*(?:script|iframe|object|embed|applet|form|input|button|textarea|select)"
    r"[^>]*>.*?</\s*(?:script|iframe|object|embed|applet|form|input|button|textarea|select)\s*>",
    re.DOTALL | re.IGNORECASE,
)

DANGEROUS_SELF_CLOSING = re.compile(
    r"<\s*(?:script|iframe|object|embed|applet|link|meta)\s[^>]*/?\s*>",
    re.IGNORECASE,
)

EVENT_HANDLERS = re.compile(
    r"\s+on\w+\s*=\s*[\"'][^\"']*[\"']",
    re.IGNORECASE,
)

DATA_URIS = re.compile(
    r"(?:src|href|action)\s*=\s*[\"']data:[^\"']*[\"']",
    re.IGNORECASE,
)


def check_domain(url: str) -> dict:
    """Check if a URL's domain is allowed.

    Returns: { allowed: bool, trust_level: str, domain: str }
    """
    parsed = urlparse(url)
    domain = parsed.hostname or ""

    # Block private IPs
    if domain in ("localhost", "127.0.0.1") or domain.startswith("192.168.") or domain.startswith("10."):
        return {"allowed": False, "trust_level": "blocked", "domain": domain,
                "reason": "Private IP address blocked"}

    # Check allowlists
    for trusted in TRUSTED_DOMAINS:
        if domain == trusted or domain.endswith("." + trusted):
            return {"allowed": True, "trust_level": "trusted", "domain": domain}

    for semi in SEMI_TRUSTED_DOMAINS:
        if domain == semi or domain.endswith("." + semi):
            return {"allowed": True, "trust_level": "semi-trusted", "domain": domain}

    return {"allowed": False, "trust_level": "blocked", "domain": domain,
            "reason": f"Domain {domain} not in allowlist"}


def strip_dangerous_html(content: str) -> str:
    """Remove dangerous HTML elements, event handlers, and data URIs."""
    content = DANGEROUS_TAGS.sub("[STRIPPED: dangerous HTML element]", content)
    content = DANGEROUS_SELF_CLOSING.sub("[STRIPPED: dangerous tag]", content)
    content = EVENT_HANDLERS.sub("", content)
    content = DATA_URIS.sub('src="[STRIPPED]"', content)
    return content


def scan_for_injections(content: str) -> dict:
    """Scan content for prompt injection patterns.

    Returns: { risk_score: int, detections: list[{pattern, risk, description, match}] }
    """
    detections = []
    total_risk = 0

    for pattern, risk, description in INJECTION_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            match_str = matches[0] if isinstance(matches[0], str) else str(matches[0])
            detections.append({
                "pattern": pattern,
                "risk": risk,
                "description": description,
                "match": match_str[:100],
            })
            total_risk += risk * len(matches)

    return {"risk_score": total_risk, "detections": detections}


def detect_encoding_attacks(content: str) -> list:
    """Detect Base64, hex, or Unicode obfuscation of injection attempts."""
    findings = []

    # Check for suspicious Base64 blocks
    b64_pattern = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")
    b64_matches = b64_pattern.findall(content)
    for match in b64_matches[:5]:
        try:
            import base64
            decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
            inner_scan = scan_for_injections(decoded)
            if inner_scan["risk_score"] > 0:
                findings.append({
                    "type": "base64_encoded_injection",
                    "decoded_preview": decoded[:100],
                    "inner_risk": inner_scan["risk_score"],
                })
        except Exception:
            pass

    # Check for Unicode homoglyph abuse (Cyrillic/Latin lookalikes)
    cyrillic_pattern = re.compile(r"[\u0400-\u04FF]")
    if cyrillic_pattern.search(content):
        latin_context = content[:500]
        if re.search(r"[a-zA-Z]", latin_context):
            findings.append({
                "type": "mixed_script_homoglyph",
                "description": "Mixed Cyrillic and Latin characters detected",
            })

    return findings


def sanitize_web_content(content: str, source_url: str) -> dict:
    """Full sanitization pipeline for web-fetched content.

    Returns: {
        content: str (sanitized),
        source_url: str,
        risk_score: int,
        detections: list,
        encoding_findings: list,
        sanitized: bool,
        safe: bool (risk_score <= 5),
        user_prompt_required: bool (risk_score > 5),
    }
    """
    cleaned = strip_dangerous_html(content)
    injection_result = scan_for_injections(cleaned)
    encoding_findings = detect_encoding_attacks(cleaned)
    encoding_risk = sum(f.get("inner_risk", 2) for f in encoding_findings)
    total_risk = injection_result["risk_score"] + encoding_risk

    safe = total_risk <= 5
    return {
        "content": cleaned,
        "source_url": source_url,
        "risk_score": total_risk,
        "detections": injection_result["detections"],
        "encoding_findings": encoding_findings,
        "sanitized": True,
        "safe": safe,
        "user_prompt_required": not safe,
    }


def format_security_alert(result: dict) -> str:
    """Format a human-readable security alert for the user."""
    if result["safe"]:
        return ""

    lines = [
        f"**SECURITY ALERT** — Suspicious content from {result['source_url']}",
        f"Risk score: {result['risk_score']} (threshold: 5)",
        "",
        "Detections:",
    ]
    for d in result["detections"]:
        lines.append(f"  - [{d['risk']}pt] {d['description']}: \"{d['match']}\"")
    for f in result["encoding_findings"]:
        lines.append(f"  - [encoded] {f.get('description', f.get('type', 'unknown'))}")
    lines.append("")
    lines.append("Allow sanitized version into agent context? [y/n]")
    return "\n".join(lines)
