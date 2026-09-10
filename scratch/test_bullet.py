import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tailor_engine import apply_format_preserving_tailoring

orig = """# ALEX MORGAN
alex@email.com

## WORK EXPERIENCE
- Coordinated cross-functional teams during product release cycles.
• Managed task backlogs in Jira.
"""

imp = [
    {
        "original": "Coordinated cross-functional teams during product release cycles.",
        "tailored": "Coordinated Agile cross-functional teams on AWS."
    },
    {
        "original": "Managed task backlogs in Jira.",
        "tailored": "Managed backlog refinement in Jira."
    }
]

for l in orig.splitlines():
    if l.strip():
        s = l.strip()
        print(f"DEBUG: {repr(s)} | ord(0): {ord(s[0])} | is_bullet: {bool(re.match(r'^[^\w\s#]', s, re.ASCII))}")

res = apply_format_preserving_tailoring(orig, imp)
print("=== TAILORED RESULT ===")
print(repr(res))
