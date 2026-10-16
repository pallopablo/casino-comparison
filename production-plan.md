# Production Plan

## Architecture

For production, I would separate the data collection process from the public website. The scraper would run as a scheduled backend job rather than when a visitor opens the site. The job would retrieve the permitted public source, extract the bonus information, use the language model to structure the required fields, validate the results, and publish a known-good JSON file. The public website would remain a lightweight static application served through a CDN over HTTPS.

## Scheduling and Data Updates

The scraper could run on a scheduled cloud job, for example once or twice per day. Casino promotions do not require requests on every website visit, so scheduled updates reduce unnecessary traffic to the source. The job should continue to respect `robots.txt`, the source's applicable terms and policies, and rate limits. If automated access is prohibited or blocked, the job should stop rather than attempting to bypass the restriction.

## Validation and Reliability

Before replacing production data, the pipeline should validate that exactly the expected records and fields are present. Required values should be checked for valid types, source URLs should use HTTP or HTTPS, and unexpected model responses should be rejected. A failed scrape should not overwrite the last known-good JSON file. Logs should record successful runs, failures, HTTP status codes, validation errors, and update timestamps.

## Security

API keys and other credentials should be stored in a managed secrets service or protected environment variables, never in source control or client-side JavaScript. The production site should use HTTPS and restrictive deployment permissions. Dependencies should be kept up to date, and the application should continue to avoid injecting scraped HTML directly into the page.

## Monitoring

Monitoring should alert the operator when the scraper repeatedly fails, the source HTML structure changes, API requests fail, or the generated data does not pass validation. A simple health check could track the timestamp of the most recent successful update so stale data can be detected quickly.

## Cost

The architecture is intentionally small. Static hosting can often be free or very inexpensive. A scheduled serverless job, low-volume model requests, logging, and storage would normally have modest costs at this scale. A rough early-stage infrastructure budget could be approximately US$10–60 per month before domain costs and depending on provider usage and current language-model pricing.

## Main Risks and Mitigations

The main technical risk is that the source changes its HTML structure. This can be mitigated with validation, monitoring, automated tests, and clear failure alerts. Promotional information can also change quickly, so every record should preserve its source URL and generation timestamp. Language-model extraction can occasionally be ambiguous, so the system should use strict structured output, validation, documented extraction rules, and human review when necessary. The scraper should never attempt to defeat access restrictions; if the source no longer permits the intended automated access, another permitted source should be selected.