import argparse
import json
import os
import sys
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from playwright.sync_api import sync_playwright

# Load environment variables from .env file at launch
load_dotenv()


def extract_single_page_data(context, url: str) -> dict:
    """Helper function to fetch dynamic DOM metadata using an active Playwright context."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        rendered_html = page.content()
        page.close()
    except Exception as e:
        return {"error": f"Failed to render {url}: {str(e)}", "url": url}

    soup = BeautifulSoup(rendered_html, "html.parser")

    # Extract Metadata
    title = soup.title.string.strip() if soup.title and soup.title.string else None

    meta_desc = None
    desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all("h1")]
    h2_tags = [h2.get_text(strip=True) for h2 in soup.find_all("h2")[:10]]

    images = soup.find_all("img")
    images_without_alt = sum(1 for img in images if not img.get("alt"))

    body_text = soup.body.get_text(strip=True) if soup.body else ""
    word_count = len(body_text.split())

    return {
        "url": url,
        "title": title,
        "title_length": len(title) if title else 0,
        "meta_description": meta_desc,
        "meta_description_length": len(meta_desc) if meta_desc else 0,
        "h1_tags": h1_tags,
        "h2_tags_sample": h2_tags,
        "total_images": len(images),
        "images_missing_alt": images_without_alt,
        "approx_word_count": word_count,
    }


def scrape_urls(urls: list[str]) -> list[dict]:
    """Launches Playwright once and scrapes single or multiple URLs."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        for url in urls:
            results.append(extract_single_page_data(context, url))
        browser.close()
    return results


def get_gemini_client() -> genai.Client:
    """Validates API key and initializes Gemini Client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(
            "[!] Error: GEMINI_API_KEY not found in environment or .env file.",
            file=sys.stderr,
        )
        sys.exit(1)
    return genai.Client(api_key=api_key)


def analyze_single_seo(seo_data: dict) -> str:
    """Passes single URL metadata to Gemini for standard audit."""
    client = get_gemini_client()

    prompt = f"""
    You are an expert Technical SEO Specialist.
    Analyze the following scraped webpage SEO metadata and write a concise, actionable audit.

    Raw Scraped Metadata:
    {json.dumps(seo_data, indent=2)}

    Please structure your output in plain Markdown:
    1. **SEO Health Score** (Out of 100 with quick verdict)
    2. **Critical Technical Issues**
    3. **Content & Search Intent Analysis**
    4. **Actionable Rewrites** (Title & Meta Description)
    """

    config = types.GenerateContentConfig(tools=[])
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite", contents=prompt, config=config
    )
    return response.text


def analyze_competitive_seo(site_a: dict, site_b: dict) -> str:
    """Passes two sets of metadata to Gemini to generate a competitive gap analysis."""
    client = get_gemini_client()

    prompt = f"""
    You are an expert SEO Strategist performing a competitive gap analysis between two URLs.

    TARGET SITE (Your Site):
    {json.dumps(site_a, indent=2)}

    COMPETITOR SITE:
    {json.dumps(site_b, indent=2)}

    Please structure your response in plain Markdown:
    1. **Executive Summary & Score Comparison** (Give individual scores out of 100 and declare a winner)
    2. **Content Depth & Keyword Strategy Gaps** (Compare word count, H1/H2 usage, and coverage depth)
    3. **Technical Metadata Comparison** (Compare Title/Meta quality and image ALT accessibility compliance)
    4. **Strategic Action Plan** (Top 3 prioritized steps the Target Site must take to outrank the Competitor)
    """

    config = types.GenerateContentConfig(tools=[])
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite", contents=prompt, config=config
    )
    return response.text


def print_comparison_table(site_a: dict, site_b: dict):
    """Prints a terminal side-by-side metric comparison safely without nested quotes."""
    alt_a = f"{site_a['images_missing_alt']}/{site_a['total_images']}"
    alt_b = f"{site_b['images_missing_alt']}/{site_b['total_images']}"

    title_a = f"{site_a['title_length']} chars"
    title_b = f"{site_b['title_length']} chars"

    desc_a = f"{site_a['meta_description_length']} chars"
    desc_b = f"{site_b['meta_description_length']} chars"

    print("\n" + "=" * 70)
    print(" SIDE-BY-SIDE METRIC COMPARISON")
    print("=" * 70)
    print(f"{'Metric':<25} | {'Target Site':<20} | {'Competitor Site':<20}")
    print("-" * 70)
    print(f"{'Title Length':<25} | {title_a:<20} | {title_b:<20}")
    print(f"{'Meta Desc Length':<25} | {desc_a:<20} | {desc_b:<20}")
    print(f"{'H1 Tags Count':<25} | {len(site_a['h1_tags']):<20} | {len(site_b['h1_tags']):<20}")
    print(f"{'Missing Alt Images':<25} | {alt_a:<20} | {alt_b:<20}")
    print(f"{'Approx Word Count':<25} | {site_a['approx_word_count']:<20} | {site_b['approx_word_count']:<20}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="CLI tool to perform single or competitive AI SEO audits using Playwright & Gemini."
    )
    parser.add_argument("url", help="Target URL (e.g., https://example.com)")
    parser.add_argument(
        "-c", "--compare", help="Competitor URL to analyze side-by-side"
    )
    parser.add_argument("-o", "--output", help="Save AI Markdown report to a file")
    parser.add_argument("--json", help="Save raw scraped metadata as JSON to a file")
    parser.add_argument(
        "--raw-only", action="store_true", help="Only scrape metadata; skip AI analysis"
    )

    args = parser.parse_args()

    targets = [args.url]
    if args.compare:
        targets.append(args.compare)

    print(f"[*] Rendering DOM and scraping URL(s): {', '.join(targets)}")
    scraped_results = scrape_urls(targets)

    # Error Check
    for res in scraped_results:
        if "error" in res:
            print(f"[!] Error: {res['error']}", file=sys.stderr)
            sys.exit(1)

    site_a = scraped_results[0]

    # Save JSON if requested
    if args.json:
        output_data = scraped_results if args.compare else site_a
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        print(f"[+] Saved raw JSON metadata to: {args.json}")

    # Mode: Competitive Compare
    if args.compare:
        site_b = scraped_results[1]
        print_comparison_table(site_a, site_b)

        if args.raw_only:
            return

        print("[*] Requesting Competitive AI Gap Analysis from Gemini...")
        report = analyze_competitive_seo(site_a, site_b)

        print("\n" + "=" * 70)
        print(" AI COMPETITIVE SEO GAP REPORT")
        print("=" * 70)
        print(report)

    # Mode: Single Audit
    else:
        print("\n" + "=" * 50)
        print(" METADATA SUMMARY")
        print("=" * 50)
        print(f"URL:                {site_a['url']}")
        print(f"Title:              {site_a['title']} ({site_a['title_length']} chars)")
        print(f"Meta Description:   {site_a['meta_description']} ({site_a['meta_description_length']} chars)")
        print(f"H1 Tags Count:      {len(site_a['h1_tags'])}")
        print(f"Missing Alt Images: {site_a['images_missing_alt']} / {site_a['total_images']}")
        print(f"Word Count:         {site_a['approx_word_count']}")
        print("=" * 50 + "\n")

        if args.raw_only:
            return

        print("[*] Requesting AI SEO analysis from Gemini...")
        report = analyze_single_seo(site_a)

        print("\n" + "=" * 50)
        print(" AI SEO AUDIT REPORT")
        print("=" * 50)
        print(report)

    # Save Markdown report if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n[+] Saved Markdown audit report to: {args.output}")


if __name__ == "__main__":
    main()