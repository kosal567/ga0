# /// script
# requires-python = ">=3.13"
# dependencies = ["faker"]
# ///
from pathlib import Path
from faker import Faker
import os
import random

# Reproducibility (same pattern as your repo)
seed_value = int(os.environ.get("TDS_RANDOM_SEED", 42))
random.seed(seed_value)
fake = Faker()
fake.seed_instance(seed_value)

OUTPUT_DIR = Path("cdp_trap")
NUM_PAGES = 15  # Recommended: 12–20 for CDP assignment


def runtime_script(page_id: int) -> str:
    """
    JavaScript that personalizes console logs & errors
    based on ?student=<id> query parameter.
    """
    return f"""
<script>
(function() {{
    // Extract student identifier from URL
    const params = new URLSearchParams(window.location.search);
    const studentId = params.get("student") || "default_student";

    // Deterministic hash function (stable across browsers)
    function hashCode(str) {{
        let hash = 0;
        for (let i = 0; i < str.length; i++) {{
            hash = ((hash << 5) - hash) + str.charCodeAt(i);
            hash |= 0;
        }}
        return Math.abs(hash);
    }}

    const seed = hashCode(studentId);
    const pageId = {page_id};

    // Deterministic behavior per student + per page
    const logIntensity = (seed + pageId) % 5;
    const shouldWarn = (seed + pageId) % 3 === 0;
    const shouldError = (seed + pageId) % 4 === 0;
    const asyncDelay = 1000 + (seed % 2000);

    // Visible logs (for CDP capture)
    console.log(`[TDS] Student: ${{studentId}} | Page: ${{pageId}} initialized`);
    console.info(`[TDS] Seed: ${{seed}} | Runtime diagnostics active`);

    if (logIntensity >= 2) {{
        console.debug(`[TDS] Debug telemetry enabled on page ${{pageId}}`);
    }}

    if (shouldWarn) {{
        console.warn(`[TDS] Deprecated analytics API detected on page ${{pageId}}`);
    }}

    // Async logs (forces proper runtime listening)
    setTimeout(() => {{
        console.log(`[TDS] Background sync started on page ${{pageId}}`);
    }}, asyncDelay);

    // Hidden async runtime error (key CDP signal)
    if (shouldError) {{
        setTimeout(() => {{
            console.error(`[TDS] Critical module failure on page ${{pageId}}`);
            // Real uncaught exception (students must capture pageerror)
            undefinedFunctionCall_TDS_{page_id}();
        }}, asyncDelay + 1500);
    }}

    // Continuous noise to prevent hardcoding outputs
    setInterval(() => {{
        console.debug(`[TDS] Heartbeat | Student: ${{studentId}} | Page: ${{pageId}} | ` + new Date().toISOString());
    }}, 4000);

}})();
</script>
"""


def navigation_links(all_pages, current_page):
    """Create cross-links similar to crawl_html.py philosophy."""
    possible = [p for p in all_pages if p != current_page]
    k = min(3, len(possible))
    links = random.sample(possible, k=k) if possible else []

    nav_html = "".join(
        f'<a href="{link}">Go to {Path(link).stem.title()}</a><br>\n'
        for link in links
    )
    return f"<nav><h3>Navigation</h3>{nav_html}</nav>"


def generate_html(page_name, page_id, all_pages):
    title = fake.sentence(nb_words=3).replace(".", "")
    nav = navigation_links(all_pages, page_name)
    script = runtime_script(page_id)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body data-page-id="{page_id}">
    <h1>{title}</h1>
    <p><strong>TDS Monitoring Dashboard</strong></p>
    <p>Page ID: {page_id}</p>
    <p>Status: All systems operational.</p>
    <p><em>Note: Runtime diagnostics active.</em></p>

    {nav}

    <div id="content">
        <p>Loading analytics modules...</p>
    </div>

    {script}
</body>
</html>
"""


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Generate pages (index + multiple linked pages)
    pages = ["index.html"] + [f"page_{i}.html" for i in range(1, NUM_PAGES)]

    for i, page in enumerate(pages):
        html = generate_html(
            page_name=page,
            page_id=i,
            all_pages=pages
        )
        (OUTPUT_DIR / page).write_text(html, encoding="utf-8")

    print(f"Generated {len(pages)} CDP trap pages in '{OUTPUT_DIR}/'")
    print("Personalization enabled via URL query parameter: ?student=<id>")


if __name__ == "__main__":
    main()
