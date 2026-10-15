"""
Scrapes Workday career APIs using direct POST requests.
Supports pre-filters with operators: contains_any, contains_all, contains_none
"""

import asyncio
import httpx
from loguru import logger


def job_passes_prefilters(job: dict, pre_filters: list) -> bool:
    """Apply generic pre‑filters (AND between conditions)."""
    if not pre_filters:
        return True
    
    for cond in pre_filters:
        field = cond.get("field")
        operator = cond.get("operator", "contains_any")
        values = cond.get("values", [])
        
        if not field or not values:
            continue
            
        field_value = job.get(field, "")
        field_lower = field_value.lower()
        
        if operator == "contains_any":
            # Job must contain AT LEAST ONE of the values
            if not any(v.lower() in field_lower for v in values):
                return False
                
        elif operator == "contains_all":
            # Job must contain ALL of the values
            if not all(v.lower() in field_lower for v in values):
                return False
                
        elif operator == "contains_none":
            # Job must NOT contain ANY of the values (SKIP LIST)
            if any(v.lower() in field_lower for v in values):
                return False
                
    return True


async def scrape_company(
    client: httpx.AsyncClient,
    company: dict,
    scraper_config: dict,
    pre_filters: list = None
) -> list[dict]:
    """
    Fetch jobs and apply pre‑filters (contains_any, contains_all, contains_none).
    """
    all_jobs = []
    offset = 0
    limit = scraper_config.get("jobs_per_page", 20)
    max_pages = scraper_config.get("max_pages_per_company", 50)
    delay = scraper_config.get("delay_between_pages", 1)
    timeout = scraper_config.get("request_timeout_seconds", 30)
    enable_prefilter = scraper_config.get("enable_prefilter", False)

    api_url = company["api_url"]
    base_url = company["base_url"]
    company_name = company["name"]

    page = 1
    while True:
        if page > max_pages:
            logger.warning(f"[{company_name}] Reached max pages limit ({max_pages}), stopping.")
            break

        logger.debug(f"[{company_name}] Fetching page {page} (offset={offset})...")

        payload = {
            "appliedFacets": {},
            "limit": limit,
            "offset": offset,
            "searchText": ""
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        try:
            resp = await client.post(api_url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[{company_name}] Request failed at offset {offset}: {e}")
            break

        total = data.get("total", 0)
        postings = data.get("jobPostings", [])

        if not postings:
            break

        for posting in postings:
            bullet = posting.get("bulletFields", ["UNKNOWN"])
            job_id = bullet[0] if bullet else "UNKNOWN"

            external = posting.get("externalPath", "")
            full_url = base_url + external if external.startswith("/") else base_url + "/" + external

            job = {
                "id": job_id,
                "title": posting.get("title", ""),
                "location": posting.get("locationsText", ""),
                "posted_on": posting.get("postedOn", ""),
                "remote_type": posting.get("remoteType", ""),
                "url": full_url,
                "company": company_name,
            }

            # Apply pre‑filters if enabled
            if enable_prefilter and pre_filters:
                if not job_passes_prefilters(job, pre_filters):
                    logger.debug(f"[{company_name}] Skipped (pre-filter): {job['title']} [ID: {job_id}]")
                    continue

            all_jobs.append(job)

        # Pagination
        offset += limit
        page += 1
        if offset >= total:
            break
        await asyncio.sleep(delay)

    logger.info(f"[{company_name}] Fetched {len(all_jobs)} jobs after pre‑filters.")
    return all_jobs


async def scrape_all(companies: list, scraper_config: dict) -> list[dict]:
    """
    Scrape all companies – applies pre_filters from config.
    """
    all_jobs = []
    delay_between = scraper_config.get("delay_between_companies", 2)
    pre_filters = scraper_config.get("pre_filters", [])

    async with httpx.AsyncClient() as client:
        for company in companies:
            try:
                jobs = await scrape_company(
                    client,
                    company,
                    scraper_config,
                    pre_filters=pre_filters if scraper_config.get("enable_prefilter", False) else None
                )
                all_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"Error scraping {company.get('name', 'unknown')}: {e}")
            await asyncio.sleep(delay_between)

    return all_jobs