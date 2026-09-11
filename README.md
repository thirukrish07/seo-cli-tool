SEO CLI Tool 🚀
A high-performance, terminal-based SEO audit tool powered by Python 3.14, Playwright, and Google Gemini. Designed to perform automated technical SEO analysis, execute client-side JavaScript for dynamic rendering, and generate competitive gap reports side-by-side.

Key Features
Dynamic DOM Extraction: Built with Playwright (headless Chromium) to scrape JavaScript-heavy web applications, single-page applications (SPAs), and dynamic content seamlessly.

AI-Powered Analysis: Leverages gemini-3.6-flash via the google-genai SDK to produce structured technical SEO recommendations, search intent evaluations, and actionable metadata rewrites.

Competitive Comparison Mode: Compare your target URL against a competitor side-by-side with formatted terminal tables and a strategic AI gap analysis report.

Multi-Format Export Options: Save audit results directly as raw JSON (--json) or export complete Markdown reports (-o).

Secure Setup: Keeps API keys secure using environment variables managed by python-dotenv.

Tech Stack
Language: Python 3.14

Browser Automation: Playwright (Chromium)

HTML Parsing: BeautifulSoup4

AI Engine: Google Gemini SDK (google-genai)

Environment Management: python-dotenv

Getting Started
Prerequisites
Python 3.14+ installed

Google Gemini API Key (Get your key from Google AI Studio)

Installation
Clone the repository:

Bash
git clone https://github.com/your-username/seo-cli-tool.git
cd seo-cli-tool
Install dependencies:

Bash
python -m pip install -r requirements.txt
Install Chromium browser binaries:

Bash
python -m playwright install chromium
Configure Environment Variables:
Create a .env file in the root directory and add your Gemini API key:

Code snippet
GEMINI_API_KEY=your_actual_api_key_here
Usage
1. Run a Single URL Audit
Extract dynamic metadata and generate an AI SEO report for a target website:

Bash
python seo_audit.py https://www.apple.com/
2. Side-by-Side Competitive Analysis
Compare two websites concurrently to identify structural and metadata gaps:

Bash
python seo_audit.py https://www.apple.com/ --compare https://www.samsung.com/
3. Save Markdown Report to File
Save the AI-generated audit report to a Markdown file:

Bash
python seo_audit.py https://www.apple.com/ -o report.md
4. Export Raw JSON Metadata
Scrape and dump the rendered DOM metadata to a JSON file:

Bash
python seo_audit.py https://www.apple.com/ --json metadata.json
5. Scrape Raw Data Only (Skip AI Analysis)
Scrape metadata and view the terminal summary without invoking the Gemini API:

Bash
python seo_audit.py https://www.apple.com/ --raw-only
Terminal Output Example
Plaintext
======================================================================
 SIDE-BY-SIDE METRIC COMPARISON
======================================================================
Metric                    | Target Site          | Competitor Site     
----------------------------------------------------------------------
Title Length              | 5 chars              | 68 chars            
Meta Desc Length          | 110 chars            | 158 chars           
H1 Tags Count             | 1                    | 1                   
Missing Alt Images        | 12/23                | 4/45                
Approx Word Count         | 473                  | 1250                
======================================================================

[*] Requesting Competitive AI Gap Analysis from Gemini...
