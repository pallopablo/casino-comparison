import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

USER_AGENT = "CasinoBonusAssessmentBot/1.0"
TIMEOUT = 30


def required_env(name):
    """Read a required value from the .env file."""

    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"Configure {name} in your .env file before running the scraper."
        )

    if "YOUR_" in value or "REPLACE" in value:
        raise RuntimeError(
            f"Replace the placeholder value for {name} in your .env file."
        )

    return value


# =========================================================
# ROBOTS.TXT + PAGE DOWNLOAD
# =========================================================

def fetch_page(source_url):
    """
    Check robots.txt before downloading the source page.

    The scraper stops if access is explicitly blocked.
    It does not bypass authentication, CAPTCHAs,
    rate limits, or access restrictions.
    """

    parsed = urlparse(source_url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise RuntimeError("SOURCE_URL is not a valid URL.")

    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    headers = {
        "User-Agent": USER_AGENT
    }

    print(f"Checking robots.txt: {robots_url}")

    try:
        robots_response = requests.get(
            robots_url,
            headers=headers,
            timeout=TIMEOUT
        )

        if robots_response.status_code in (401, 403, 429):
            raise RuntimeError(
                f"robots.txt returned HTTP "
                f"{robots_response.status_code}. Stopping."
            )

        if robots_response.status_code == 404:
            print(
                "WARNING: robots.txt was not found. "
                "Verify the website terms before scraping."
            )

        elif robots_response.ok:
            robot_parser = RobotFileParser()
            robot_parser.set_url(robots_url)
            robot_parser.parse(
                robots_response.text.splitlines()
            )

            if not robot_parser.can_fetch(
                USER_AGENT,
                source_url
            ):
                raise RuntimeError(
                    "robots.txt does not allow this scraper "
                    "to access the source page."
                )

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not check robots.txt: {exc}"
        ) from exc

    print("robots.txt check passed.")

    # Polite delay before requesting the source page.
    time.sleep(1)

    print(f"Downloading source page: {source_url}")

    try:
        response = requests.get(
            source_url,
            headers=headers,
            timeout=TIMEOUT
        )

        if response.status_code in (401, 403, 429):
            raise RuntimeError(
                f"The website returned HTTP "
                f"{response.status_code}. "
                "The scraper will not bypass the block."
            )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not download source page: {exc}"
        ) from exc

    print(
        f"Source downloaded successfully "
        f"(HTTP {response.status_code})."
    )

    return response.text


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_text(value):
    """Collapse unnecessary whitespace."""

    return " ".join(value.split())


# =========================================================
# FIND CASINO COMPARISON TABLE
# =========================================================

def find_comparison_table(soup):
    """
    Find a table containing the required casino fields.
    """

    tables = soup.find_all("table")

    print(f"Found {len(tables)} HTML table(s).")

    for table in tables:
        rows = table.find_all("tr")

        if not rows:
            continue

        first_row_text = clean_text(
            rows[0].get_text(
                " ",
                strip=True
            )
        ).lower()

        required_words = [
            "casino",
            "bonus",
            "wagering",
            "deposit"
        ]

        if all(
            word in first_row_text
            for word in required_words
        ):
            return table

    return None


# =========================================================
# EXTRACT EXACTLY THREE CASINOS
# =========================================================

def extract_three_casinos(html, source_url):
    """
    Automatically extract exactly three casinos
    from the source comparison table.
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    table = find_comparison_table(soup)

    if table is None:
        raise RuntimeError(
            "Could not find the Casino / Bonus / "
            "Wagering / Min Deposit comparison table."
        )

    print("Casino comparison table found.")

    rows = table.find_all("tr")

    records = []

    # Skip the heading row.
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])

        if len(cells) < 4:
            continue

        # Casino name
        casino = clean_text(
            cells[0].get_text(
                " ",
                strip=True
            )
        )

        # Remove decorative arrow from source link text.
        casino = casino.replace("→", "").strip()

        # Welcome bonus
        bonus = clean_text(
            cells[1].get_text(
                " ",
                strip=True
            )
        )

        # Wagering requirement
        wagering = clean_text(
            cells[2].get_text(
                " ",
                strip=True
            )
        )

        # Minimum deposit
        minimum_deposit = clean_text(
            cells[3].get_text(
                " ",
                strip=True
            )
        )

        if not casino or not bonus:
            continue

        print(f"Scraped casino: {casino}")

        # Preserve the original information scraped
        # from the comparison table.
        raw_terms = (
            f"Casino: {casino}. "
            f"Welcome bonus: {bonus}. "
            f"Wagering requirement: {wagering}. "
            f"Minimum deposit: {minimum_deposit}."
        )

        records.append(
            {
                "casino": casino,
                "bonus_terms_original": raw_terms,
                "source_url": source_url
            }
        )

        if len(records) == 3:
            break

    if len(records) != 3:
        raise RuntimeError(
            f"Found {len(records)} usable casino rows; "
            "expected exactly 3."
        )

    print("Successfully scraped exactly 3 casinos.")

    return records


# =========================================================
# OPENAI STRUCTURED EXTRACTION
# =========================================================

def extract_with_llm(record):
    """
    Use an OpenAI language model to convert the scraped
    free-text bonus terms into structured fields.
    """

    api_key = required_env("LLM_API_KEY")
    base_url = required_env("LLM_BASE_URL")
    model = required_env("LLM_MODEL")

    endpoint = (
        base_url.rstrip("/")
        + "/chat/completions"
    )

    system_prompt = """
You are a structured data extraction system.

Your job is to convert scraped casino bonus terms into
three structured fields.

Return ONLY valid JSON with exactly these keys:

{
  "welcome_bonus": string or null,
  "wagering_requirement": number or null,
  "minimum_deposit": string or null
}

EXTRACTION RULES:

1. Never invent information.

2. Preserve the advertised welcome bonus accurately.

3. wagering_requirement must contain ONE numeric
   multiplier only.

4. Never include the letter "x" in the
   wagering_requirement JSON value.

5. minimum_deposit must preserve the currency when
   the currency is available.

6. A source may advertise multiple components of a
   welcome offer, for example:
   - a sports bonus
   - casino credit
   - free spins
   - a deposit match

7. When several wagering multipliers are present,
   identify the main casino welcome-offer component.

8. Prefer the wagering requirement attached to the
   CASINO or FREE-SPINS component over a sports-only
   wagering requirement when the welcome offer
   contains both sports and casino components.

9. Example:
   Bonus: R1,000 sports + R2,000 casino
   Wagering: 3x sports / 30x casino

   wagering_requirement should be:

   30

10. Example:
    Bonus: R25 sign-up + 50 free spins
    Wagering: 1x sports / 10x spins

    Because the casino welcome offer contains free
    spins, wagering_requirement should be:

    10

11. If the offer only contains a sports/free-bet
    component and no casino or free-spins component,
    use the multiplier associated with that offer.

12. If there is no clear wagering multiplier,
    return null.

13. Do not calculate or infer a multiplier that is
    not explicitly present in the supplied text.

14. Return JSON only.

15. Do not return Markdown or explanations.
""".strip()

    user_prompt = (
        "Extract the required structured fields "
        "from this scraped casino bonus information.\n\n"
        + record["bonus_terms_original"]
    )

    payload = {
        "model": model,
        "response_format": {
            "type": "json_object"
        },
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
    }

    print(
        f"Using OpenAI to structure: "
        f"{record['casino']}..."
    )

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=TIMEOUT
        )

    except requests.RequestException as exc:
        raise RuntimeError(
            f"OpenAI request failed: {exc}"
        ) from exc

    if response.status_code == 401:
        raise RuntimeError(
            "OpenAI rejected the API key. "
            "Check LLM_API_KEY in your .env file."
        )

    if response.status_code == 429:
        raise RuntimeError(
            "OpenAI returned HTTP 429. "
            "Check your API credits or rate limit."
        )

    if not response.ok:
        safe_error = response.text[:500]

        raise RuntimeError(
            f"OpenAI returned HTTP "
            f"{response.status_code}: "
            f"{safe_error}"
        )

    # Parse the language model response.
    try:
        response_json = response.json()

        content = (
            response_json["choices"][0]
            ["message"]["content"]
        )

        structured = json.loads(content)

    except (
        KeyError,
        IndexError,
        TypeError,
        json.JSONDecodeError
    ) as exc:
        raise RuntimeError(
            "OpenAI returned an unexpected response."
        ) from exc

    # Make sure the model returned exactly
    # the required structured fields.
    expected_keys = {
        "welcome_bonus",
        "wagering_requirement",
        "minimum_deposit"
    }

    if set(structured.keys()) != expected_keys:
        raise RuntimeError(
            "OpenAI response did not contain "
            "exactly the required fields."
        )

    # =====================================================
    # NORMALIZE WAGERING MULTIPLIER
    # =====================================================

    wagering = structured[
        "wagering_requirement"
    ]

    if wagering is not None:
        if isinstance(wagering, str):
            match = re.search(
                r"\d+(?:\.\d+)?",
                wagering
            )

            if match:
                wagering = float(
                    match.group()
                )

                if wagering.is_integer():
                    wagering = int(wagering)

                structured[
                    "wagering_requirement"
                ] = wagering

            else:
                structured[
                    "wagering_requirement"
                ] = None

        elif not isinstance(
            wagering,
            (int, float)
        ):
            structured[
                "wagering_requirement"
            ] = None

    print(
        f"LLM extraction completed: "
        f"{record['casino']}"
    )

    return structured


# =========================================================
# SAVE JSON
# =========================================================

def save_results(records, source_name):
    """
    Save all final records to casinos.json.
    """

    output = {
        "source_name": source_name,

        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        "count": len(records),

        "casinos": records
    }

    temporary_path = "casinos.json.tmp"

    with open(
        temporary_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False
        )

        file.write("\n")

    # Atomic replacement prevents an incomplete
    # JSON file if something fails during writing.
    os.replace(
        temporary_path,
        "casinos.json"
    )

    print(
        "casinos.json saved successfully."
    )


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():
    print()

    print(
        "======================================"
    )

    print(
        " Casino Comparison Scraper"
    )

    print(
        "======================================"
    )

    print()

    source_url = required_env(
        "SOURCE_URL"
    )

    source_name = required_env(
        "SOURCE_NAME"
    )

    # STEP 1:
    # Check robots.txt and download the source.
    html = fetch_page(
        source_url
    )

    # STEP 2:
    # Automatically scrape exactly three casinos.
    casinos = extract_three_casinos(
        html,
        source_url
    )

    # STEP 3:
    # Send each scraped record to the language model.
    final_records = []

    for record in casinos:
        structured = extract_with_llm(
            record
        )

        final_record = {
            "casino": record["casino"],

            "welcome_bonus": structured[
                "welcome_bonus"
            ],

            "wagering_requirement": structured[
                "wagering_requirement"
            ],

            "minimum_deposit": structured[
                "minimum_deposit"
            ],

            "source_url": record[
                "source_url"
            ],

            "bonus_terms_original": record[
                "bonus_terms_original"
            ]
        }

        final_records.append(
            final_record
        )

        # Small delay between API requests.
        time.sleep(1)

    # STEP 4:
    # Save the final JSON.
    save_results(
        final_records,
        source_name
    )

    print()

    print(
        "======================================"
    )

    print(
        " SUCCESS"
    )

    print(
        "======================================"
    )

    print(
        "3 casinos scraped."
    )

    print(
        "OpenAI extraction completed."
    )

    print(
        "Data saved to casinos.json."
    )

    print()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print()

        print(
            f"ERROR: {exc}",
            file=sys.stderr
        )

        sys.exit(1)