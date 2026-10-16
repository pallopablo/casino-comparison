# Casino Bonus Comparison

A small technical assessment project that automatically scrapes three casino bonus offers from a public comparison page, uses a language model to convert the scraped bonus terms into structured data, saves the results to JSON, and displays the data in a responsive web page.

## Live Website

The live deployment URL will be added here after deployment.

## Features

- Automatically retrieves casino bonus information from a public source
- Checks `robots.txt` before scraping
- Does not bypass authentication, CAPTCHAs, rate limits, or access blocks
- Extracts exactly three casino offers
- Uses an OpenAI language model to structure free-text bonus terms
- Saves structured results to `casinos.json`
- Displays the JSON data in a responsive comparison table
- Includes source links for verification
- Handles missing wagering information without inventing data
- Keeps API credentials outside the Git repository

## Data Fields

Each casino record includes:

- Casino name
- Welcome bonus
- Wagering requirement multiplier
- Minimum deposit
- Source URL

The scraper also preserves the original scraped bonus text for traceability.

## Project Structure

```text
casino-comparison/
│
├── scraper.py
├── casinos.json
├── index.html
├── style.css
├── app.js
├── requirements.txt
├── README.md
├── production-plan.md
├── .gitignore
├── .env.example
└── .env                 # Local only - never commit
```

## Technology Used

- Python
- Requests
- BeautifulSoup
- python-dotenv
- OpenAI API
- HTML5
- CSS3
- Vanilla JavaScript
- JSON

## Setup

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd casino-comparison
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

### 3. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to a new file named `.env`.

Then configure:

```env
SOURCE_URL=https://betproof.co.za/casino-bonuses-south-africa/
SOURCE_NAME=BetProof South Africa Casino Bonuses
LLM_API_KEY=YOUR_PRIVATE_API_KEY
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-5-mini
```

Never commit `.env` or expose the API key publicly.

## Run the Scraper

Once dependencies and `.env` are configured, the scraper itself runs with a single command:

```powershell
.\.venv\Scripts\python.exe scraper.py
```

A successful run:

1. Checks `robots.txt`
2. Downloads the configured source page
3. Finds the casino comparison table
4. Extracts exactly three casinos
5. Sends the scraped free-text terms to the configured language model
6. Validates the structured response
7. Writes the results to `casinos.json`

The scraper stops rather than attempting to bypass a 401, 403, or 429 response.

## Run the Website Locally

Start a local web server:

```powershell
.\.venv\Scripts\python.exe -m http.server 8000
```

Then visit:

```text
http://localhost:8000
```

Opening `index.html` directly is not recommended because browsers can restrict JavaScript from loading local JSON files.

## Language Model Usage

The language model is used for a genuine transformation step rather than for manually entered data.

The scraper first extracts the source's free-text bonus information. The text is then supplied to the model, which returns:

```json
{
  "welcome_bonus": "example",
  "wagering_requirement": 30,
  "minimum_deposit": "R10"
}
```

The program validates the response before adding it to the final JSON file.

When multiple wagering requirements occur, the extraction prompt prioritizes the casino/free-spins component of the welcome offer. If a clear applicable multiplier cannot be determined, the value remains `null` rather than being invented.

## Responsible Scraping

The scraper:

- Uses a descriptive user agent
- Checks `robots.txt`
- Makes a small number of requests
- Includes delays between relevant requests
- Stops on common access-block responses
- Does not bypass logins
- Does not bypass CAPTCHAs
- Does not bypass rate limits or other technical restrictions

`robots.txt` compliance alone should not be interpreted as legal permission. Source terms and policies should also be reviewed before production use.

If the configured source blocks automated access or prohibits the intended use, the correct approach is to stop and use another permitted source.

## Limitations

Casino promotions can change without notice.

The comparison page may contain multiple bonus components with different wagering requirements. Because the assessment requests a single wagering multiplier, the model applies the documented extraction rule and leaves ambiguous values empty.

Changes to the source website's HTML structure could require scraper maintenance.

The static website displays the latest committed `casinos.json`; it does not execute the Python scraper from the browser.

## Security

The real OpenAI API key is stored only in `.env`.

`.env` is excluded by `.gitignore`.

Only `.env.example`, which contains a placeholder key, should be committed.

If a real API key is accidentally exposed, it should be revoked immediately and replaced.

## Production Plan

See [`production-plan.md`](production-plan.md) for the proposed production architecture, scheduling, security, monitoring, cost, and risk considerations.

## AI Reflection

1. AI helped me plan the scraper, JSON structure, error handling, and responsive comparison page.
2. I used an OpenAI language model in the scraper to transform free-text casino bonus terms into structured fields.
3. AI was useful for debugging issues involving Python, the API request, the source table, and the website.
4. I still tested the scraper and website locally and reviewed the generated data instead of relying blindly on AI output.
5. The main lesson was that AI is most useful when combined with validation, source checking, secure secret handling, and human review.

## Time Spent

Actual time spent: **3 hours (assessment time cap)**

I stopped work at the specified 3-hour limit. The core assessment requirements were completed within the time available.

## Disclaimer

This project was created as a technical assessment.

Casino offers can change and should always be verified against the linked source before making any decision. The website is informational and does not endorse gambling.