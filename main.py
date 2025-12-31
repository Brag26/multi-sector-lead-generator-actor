from apify import Actor
from apify_client import ApifyClient
import asyncio
import os
import json
import aiohttp
import time


# =====================================================
# SAFE AI QUERY GENERATION (NEVER CRASHES)
# =====================================================
async def generate_search_queries_with_llm(sector, keyword, city, postcode, country):
    location = " ".join(filter(None, [city, postcode, country]))

    prompt = f"""
Generate 3–5 Google Maps search queries for {sector} in {location}.

RULES:
- Return ONLY a JSON array
- No explanation
- Example: ["clinics", "medical centre", "doctors"]
"""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as res:
                data = await res.json()

        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")

        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)

        if not isinstance(parsed, list) or not parsed:
            raise ValueError("Invalid JSON")

        return parsed

    except Exception as e:
        Actor.log.warning(f"⚠️ LLM failed, fallback used: {e}")
        return [keyword] if keyword else [sector]


# =====================================================
# MAIN ACTOR
# =====================================================
async def main():
    async with Actor:
        START_TIME = time.time()

        input_data = await Actor.get_input() or {}

        sector = input_data.get("sector", "Healthcare")
        city = input_data.get("city", "").strip()
        state = input_data.get("state", "").strip()
        postcode = input_data.get("postcode", "").strip()
        keyword = input_data.get("keyword", "").strip()
        country = input_data.get("country", "").strip()
        max_results = int(input_data.get("maxResults", 10))

        Actor.log.info(f"📋 Sector: {sector}")
        Actor.log.info(f"📍 Location: {city} {state} {postcode} {country}")
        Actor.log.info(f"🔢 Max results: {max_results}")

        # -------------------------------------------------
        # Generate queries (HARD LIMIT TO ONE)
        # -------------------------------------------------
        queries = await generate_search_queries_with_llm(
            sector, keyword, city, postcode, country
        )
        query = queries[0]

        location = " ".join(filter(None, [city, state, postcode, country]))
        search_string = f"{query} in {location}".strip()

        Actor.log.info(f"🔍 Searching: {search_string}")

        client = ApifyClient(token=os.environ["APIFY_TOKEN"])

        run_input = {
            "searchStringsArray": [search_string],
            "language": "en",
            "includeWebResults": False,
            "maxReviews": 0,
            "maxImages": 0,
            "maxCrawledPlacesPerSearch": max_results
        }

        # -------------------------------------------------
        # OPTIONAL: countryCode ONLY if user provided country
        # -------------------------------------------------
        country_map = {
            "india": "in",
            "australia": "au",
            "united states": "us",
            "usa": "us",
            "united kingdom": "gb",
            "uk": "gb",
            "canada": "ca"
        }

        if country:
            code = country_map.get(country.lower())
            if code:
                run_input["countryCode"] = code

        # -------------------------------------------------
        # START CRAWLER
        # -------------------------------------------------
        run = client.actor("compass/crawler-google-places").start(
            run_input=run_input
        )

        run_id = run["id"]
        dataset_id = run["defaultDatasetId"]

        Actor.log.info(f"🚀 Crawler started (runId={run_id})")

        collected = 0

        while True:
            items = list(client.dataset(dataset_id).iterate_items())
            collected = len(items)

            Actor.log.info(f"📊 Collected {collected} places so far")

            if collected >= max_results:
                client.run(run_id).abort()
                break

            if time.time() - START_TIME > 90:
                client.run(run_id).abort()
                break

            await asyncio.sleep(3)

        # -------------------------------------------------
        # DEDUPLICATE + PUSH RESULTS
        # -------------------------------------------------
        seen = set()
        final_results = []

        for item in items:
            key = f"{item.get('title')}_{item.get('address')}"
            if key not in seen:
                seen.add(key)
                final_results.append({
                    "name": item.get("title"),
                    "phone": item.get("phone"),
                    "website": item.get("website"),
                    "address": item.get("address"),
                    "rating": item.get("totalScore"),
                    "reviewCount": item.get("reviewsCount"),
                    "category": item.get("categoryName"),
                    "googleMapsUrl": item.get("url"),
                    "searchQuery": query
                })

        await Actor.push_data(final_results[:max_results])
        Actor.log.info(f"🎉 Finished. {len(final_results)} leads saved.")


if __name__ == "__main__":
    asyncio.run(main())
