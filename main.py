from apify import Actor
from apify_client import ApifyClient
import asyncio
import os
import json
import aiohttp
import time

# ===============================
# AI QUERY GENERATION (UNCHANGED)
# ===============================
async def generate_search_queries_with_llm(sector, keyword, city, postcode, country):
    location_parts = []
    if city:
        location_parts.append(city)
    if postcode:
        location_parts.append(postcode)
    if country:
        location_parts.append(country)

    location_context = f"in {' '.join(location_parts)}" if location_parts else ""

    prompt = f"""
You are a business lead generation expert.
Generate 3-5 Google Maps search queries for {sector} {location_context}.
Keyword: {keyword or "use best judgement"}

Return ONLY a JSON array of short strings.
"""

    # Claude only (safe default in Apify)
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            },
        ) as res:
            data = await res.json()
            text = ""
            for c in data.get("content", []):
                if c.get("type") == "text":
                    text += c.get("text", "")
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)


# ===============================
# MAIN ACTOR
# ===============================
async def main():
    async with Actor:
        START_TIME = time.time()

        input_data = await Actor.get_input() or {}
        sector = input_data.get("sector", "Healthcare")
        city = input_data.get("city", "").strip()
        postcode = input_data.get("postcode", "").strip()
        keyword = input_data.get("keyword", "").strip()
        country = input_data.get("country", "Australia")
        max_results = int(input_data.get("maxResults", 10))

        Actor.log.info(f"📋 Sector: {sector}")
        Actor.log.info(f"📍 Location: {city} {postcode} {country}")
        Actor.log.info(f"🔢 Max results: {max_results}")

        # -------------------------------
        # Generate AI queries (LIMIT TO 1)
        # -------------------------------
        queries = await generate_search_queries_with_llm(
            sector, keyword, city, postcode, country
        )
        queries = queries[:1]  # 🔒 CRITICAL FIX

        client = ApifyClient(token=os.environ["APIFY_TOKEN"])
        all_results = []

        for query in queries:
            search_string = f"{query} in {city} {postcode}".strip()
            Actor.log.info(f"🔍 Searching: {search_string}")

            run_input = {
                "searchStringsArray": [search_string],

                # 🔒 HARD STOP LIMITS
                "maxCrawledPlacesPerSearch": max_results,
                "maxSearchResults": max_results,
                "maxTotalPlaces": max_results,

                # 🛑 STOP COUNTRY / MAP EXPANSION
                "searchArea": "city",
                "maxCities": 1,
                "maxMapSegments": 1,
                "maxAutomaticZoomOut": 0,

                # BASIC
                "language": "en",
                "includeWebResults": False,
                "maxReviews": 0,
                "maxImages": 0,
                "countryCode": "au",
            }

            run = client.actor("compass/crawler-google-places").call(
                run_input=run_input
            )

            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                all_results.append({
                    "name": item.get("title"),
                    "phone": item.get("phone"),
                    "website": item.get("website"),
                    "address": item.get("address"),
                    "rating": item.get("totalScore"),
                    "reviews": item.get("reviewsCount"),
                    "category": item.get("categoryName"),
                    "mapsUrl": item.get("url"),
                    "searchQuery": query,
                })

                Actor.log.info(f"✅ Found: {item.get('title')}")

            # ⏱ Safety timeout (2 minutes)
            if time.time() - START_TIME > 120:
                Actor.log.warning("⏱ Time limit reached, stopping early")
                break

        # -------------------------------
        # Deduplicate + limit results
        # -------------------------------
        seen = set()
        unique_results = []
        for r in all_results:
            key = f"{r['name']}_{r['address']}"
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        final_results = unique_results[:max_results]

        await Actor.push_data(final_results)

        Actor.log.info(f"🎉 Done. {len(final_results)} leads saved.")
        Actor.log.info("🛑 Explicit actor exit")
        await Actor.exit()


if __name__ == "__main__":
    asyncio.run(main())
