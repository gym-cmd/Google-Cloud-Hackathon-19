import re
from pathlib import Path

routes = {"/", "/chat", "/profile", "/context", "/roadmap", "/resources", "/code", "/quiz", "/quiz-results"}

# Some html attributes have spaces, so we allow that.
for path in Path("src/templates").glob("*.html"):
    print(f"\n====================== {path.name} ======================")
    content = path.read_text()
    
    # Simple regex for links and buttons
    links = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', content, re.DOTALL)
    for href, inner in links:
        inner_clean = re.sub(r'<[^>]+>', ' ', inner).strip().replace('\n', ' ')
        inner_clean = re.sub(r'\s+', ' ', inner_clean)
        # Check validity
        valid = href in routes or href.startswith("http") or href.startswith("mailto:") or href.startswith("#")
        status = "✅ OK" if valid else "❌ INVALID"
        print(f"[A] {href:25} | {status} | {inner_clean[:40]}")
        
    buttons = re.findall(r'<button\s+[^>]*(onclick="[^"]+"|onclick=\'[^\']+\')[^>]*>(.*?)</button>', content, re.DOTALL)
    for onclick, inner in buttons:
        inner_clean = re.sub(r'<[^>]+>', ' ', inner).strip().replace('\n', ' ')
        inner_clean = re.sub(r'\s+', ' ', inner_clean)
        print(f"[BTN] {onclick:25} | {inner_clean[:40]}")
