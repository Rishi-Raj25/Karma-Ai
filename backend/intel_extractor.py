"""Lightweight intelligence extraction from scammer messages."""

import re

# Known bank keywords
_BANKS = [
    "sbi", "state bank", "hdfc", "icici", "axis", "kotak", "pnb",
    "punjab national", "canara", "bob", "bank of baroda", "union bank",
    "indian bank", "central bank", "uco", "idbi", "yes bank", "bandhan",
    "rbl", "federal bank", "indusind", "paytm", "phonepe", "gpay",
    "google pay", "amazon pay", "bhim",
]

# Scam type keywords
_SCAM_TYPES = {
    "KYC Fraud": ["kyc", "verify", "verification", "update kyc", "kyc update", "link aadhaar"],
    "Lottery/Prize": ["lottery", "prize", "winner", "jackpot", "lucky draw", "congrat"],
    "Bank Impersonation": ["bank manager", "bank officer", "account block", "account freeze", "suspend"],
    "Tech Support": ["computer", "virus", "microsoft", "windows", "antivirus", "remote access"],
    "Insurance Fraud": ["insurance", "policy", "premium", "maturity", "lic", "claim"],
    "Refund Scam": ["refund", "cashback", "return amount", "overpaid"],
    "OTP Fraud": ["otp", "one time password", "verification code", "pin number"],
    "UPI Fraud": ["upi", "google pay", "phonepe", "paytm", "send money", "request money"],
}

# Organization patterns
_ORG_PATTERNS = [
    r"(?:i am|main|mai|hum)\s+(?:from|se)\s+(.+?)(?:\s+(?:bol|call|speak|baat)|\.|,|$)",
    r"(?:calling from|from)\s+(.+?)(?:\s+(?:regarding|about|ke|ka)|\.|,|$)",
    r"(?:this is|ye)\s+(.+?)(?:\s+(?:helpline|customer|service|support))",
]


def extract_intel(text: str) -> list[dict]:
    """Extract intelligence from a single scammer message.

    Returns list of dicts: [{field_name, field_value, confidence}]
    """
    if not text:
        return []

    results = []
    text_lower = text.lower()

    # ── UPI IDs ───────────────────────────────────────────
    upi_matches = re.findall(r"[a-zA-Z0-9._-]+@[a-zA-Z]{2,}", text)
    for upi in upi_matches:
        # Skip email-like addresses with common domains
        if any(upi.endswith(d) for d in ["@gmail", "@yahoo", "@hotmail", "@outlook"]):
            continue
        results.append({"field_name": "upi_id", "field_value": upi, "confidence": 0.8})

    # ── Phone numbers ─────────────────────────────────────
    phone_matches = re.findall(r"(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}", text)
    for phone in phone_matches:
        clean = re.sub(r"[\s-]", "", phone)
        if len(clean) >= 10:
            results.append({"field_name": "phone_number", "field_value": clean, "confidence": 0.7})

    # ── Account numbers (10+ digit sequences) ─────────────
    acct_matches = re.findall(r"\b\d{10,18}\b", text)
    for acct in acct_matches:
        results.append({"field_name": "account_number", "field_value": acct, "confidence": 0.6})

    # ── Aadhaar (12 digit) ────────────────────────────────
    aadhaar_matches = re.findall(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text)
    for a in aadhaar_matches:
        clean = re.sub(r"\s", "", a)
        if len(clean) == 12:
            results.append({"field_name": "aadhaar_number", "field_value": clean, "confidence": 0.7})

    # ── Bank names ────────────────────────────────────────
    for bank in _BANKS:
        if bank in text_lower:
            results.append({"field_name": "bank_mentioned", "field_value": bank.upper(), "confidence": 0.7})
            break

    # ── Scam type detection ───────────────────────────────
    for scam_type, keywords in _SCAM_TYPES.items():
        if any(kw in text_lower for kw in keywords):
            results.append({"field_name": "scam_type", "field_value": scam_type, "confidence": 0.7})
            break

    # ── Name extraction ───────────────────────────────────
    name_patterns = [
        r"(?:my name is|mera naam|i am|main|mai)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:my name is|mera naam|i am|main|mai)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
    ]
    for pat in name_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            # Filter out common false positives
            if name.lower() not in ("calling", "from", "here", "sir", "madam", "hai", "hoon", "hu"):
                results.append({"field_name": "scammer_name", "field_value": name, "confidence": 0.6})
                break

    # ── Organization claimed ──────────────────────────────
    for pat in _ORG_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            org = m.group(1).strip()
            if len(org) > 2 and org.lower() not in ("the", "your", "aap", "tum"):
                results.append({"field_name": "organization_claimed", "field_value": org, "confidence": 0.6})
                break

    return results
