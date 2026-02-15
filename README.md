# DocDrift 📄🔍

**Documentation-Code Sync Drift Detection Engine**

Catch stale documentation before your users do. DocDrift scans your codebase and cross-references every symbol mentioned in docs against actual code — flagging references to functions, classes, and APIs that no longer exist.

> 🎯 Every stale doc = $25-50 per support ticket, 4-8h wasted per new hire, lost deals from broken API examples.

## 🚀 Quick Start

```bash
pip install -e .
docdrift .                        # Scan current project
docdrift /path/to/project          # Scan specific project
docdrift . --json                  # JSON output for CI
docdrift . --fail-under 80         # Fail if freshness < 80%
```

### GitHub Actions

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
- run: pip install -e .
- run: docdrift . --fail-under 80
```

## 🔍 What It Detects

| Detection | Example |
|-----------|------|
| Removed functions | Doc references `process_payment()` but function was deleted |
| Renamed symbols | Doc calls `fetch_user()` but it's now `get_user()` |
| Stale code blocks | `from auth import validate` but `validate` no longer exists |
| Dead inline refs | Markdown mentions `` `old_handler()` `` which was removed |

## 💰 Pricing

| Feature | Free (OSS) | Pro $49/mo | Enterprise $499/mo |
|---------|:-:|:-:|:-:|
| CLI scanning | ✅ | ✅ | ✅ |
| Python symbol detection | ✅ | ✅ | ✅ |
| Markdown / MDX / RST | ✅ | ✅ | ✅ |
| JSON output for CI | ✅ | ✅ | ✅ |
| Freshness score gate | ✅ | ✅ | ✅ |
| GitHub Action | ✅ | ✅ | ✅ |
| JS/TS/Go/Rust support | ❌ | ✅ | ✅ |
| OpenAPI route validation | ❌ | ✅ | ✅ |
| PR comments & blocking | ❌ | ✅ | ✅ |
| Slack / Teams alerts | ❌ | ✅ | ✅ |
| Multi-repo dashboard | ❌ | ❌ | ✅ |
| Trend analytics | ❌ | ❌ | ✅ |
| SSO / SAML | ❌ | ❌ | ✅ |
| SOC2 audit trail | ❌ | ❌ | ✅ |
| Self-hosted option | ❌ | ❌ | ✅ |

## 📊 Why Pay?

- **1 support ticket from stale docs = $25-50** → Pro pays for itself after 1-2 prevented tickets/month
- **New hire onboarding** — stale README wastes 4-8h × $50/hr = **$200-400 per hire**
- **Customer churn** — broken API docs during integration → lost deals worth **$10K+**
- **Compliance** — SOC2/ISO require evidence that documentation is current
- **ROI**: A 20-person eng team saving 2h/week on doc-related confusion = **$10K/month saved**

## Architecture

```
Code (.py)  →  AST Parser   →  Symbol Registry
                                      ↓
Docs (.md)  →  Regex Parser  →  Ref List  →  Cross-Ref  →  Drift Report + Score
```

## Security Notes

- **No code execution** — uses `ast.parse()` (parse only, never eval/exec)
- **No network calls** — fully offline, your code never leaves your machine
- **Path-safe** — scans only within the specified directory
- **Deterministic** — same input always produces same output

## License

AGPL-3.0 — Free for open source. Commercial license required for proprietary use.
