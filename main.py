from apify import Actor
from apify_client import ApifyClient
import asyncio
import os
import json
import aiohttp

async def generate_search_queries_with_llm(sector, keyword, city, postcode):
    """Use multiple LLMs to generate intelligent search queries with fallback"""
    
    # Build location context
    location_context = ""
    if city and postcode:
        location_context = f"in {city} {postcode}"
    elif city:
        location_context = f"in {city}"
    elif postcode:
        location_context = f"in postcode {postcode}"
    
    # Build the prompt
    prompt = f"""You are a business lead generation expert. Generate 3-5 highly specific search queries to find businesses in the {sector} sector {location_context}.

User's specific keyword: {keyword if keyword else "Not specified - use your expertise"}

Requirements:
- Generate diverse search terms that cover different business types in this sector
- Include specific roles, services, and business types
- Make queries that will find real businesses on Google Maps
- Each query should be 2-5 words maximum
- Return ONLY a JSON array of strings, nothing else

Example format: ["doctors", "medical clinics", "specialist hospitals"]

Generate the search queries now:"""

    # Try multiple LLM providers in order
    llm_providers = [
        {"name": "Claude", "func": call_claude_api},
        {"name": "OpenAI", "func": call_openai_api},
        {"name": "Google Gemini", "func": call_gemini_api},
        {"name": "Groq", "func": call_groq_api},
    ]
    
    for provider in llm_providers:
        try:
            Actor.log.info(f"🤖 Trying {provider['name']} API...")
            queries = await provider["func"](prompt)
            if queries and len(queries) > 0:
                Actor.log.info(f"✅ {provider['name']} generated {len(queries)} queries: {queries}")
                return queries
        except Exception as e:
            Actor.log.warning(f"⚠️ {provider['name']} failed: {e}")
            continue
    
    # Final fallback to basic keyword
    Actor.log.warning("⚠️ All LLM providers failed, using fallback keywords")
    return [keyword if keyword else sector]

async def call_claude_api(prompt):
    """Call Anthropic Claude API"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            data = await response.json()
            
            # Extract response text
            response_text = ""
            for content in data.get("content", []):
                if content.get("type") == "text":
                    response_text += content.get("text", "")
            
            # Parse JSON
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(response_text)

async def call_openai_api(prompt):
    """Call OpenAI API (GPT-4, GPT-3.5, etc.)"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise Exception("OpenAI API key not configured")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "gpt-4o-mini",  # Fast and cost-effective
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.7
            },
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            data = await response.json()
            response_text = data["choices"][0]["message"]["content"]
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(response_text)

async def call_gemini_api(prompt):
    """Call Google Gemini API"""
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise Exception("Google API key not configured")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1000
                }
            },
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            data = await response.json()
            response_text = data["candidates"][0]["content"]["parts"][0]["text"]
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(response_text)

async def call_groq_api(prompt):
    """Call Groq API (Fast inference with Llama, Mixtral models)"""
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        raise Exception("Groq API key not configured")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "llama-3.3-70b-versatile",  # Fast and powerful
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.7
            },
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            data = await response.json()
            response_text = data["choices"][0]["message"]["content"]
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(response_text)

async def main():
    async with Actor:
        Actor.log.info("=== Starting Multi-LLM AI-Powered Lead Generator ===")
        
        # Get input
        input_data = await Actor.get_input() or {}
        sector = input_data.get("sector", "Healthcare")
        city = input_data.get("city", "").strip()
        postcode = input_data.get("postcode", "").strip()
        keyword = input_data.get("keyword", "").strip()
        max_results = input_data.get("maxResults", 10)
        
        # Define comprehensive keywords for each sector (final fallback)
        sector_keywords = {
            "Healthcare": "Doctors, Clinics, Hospitals, Medical Centers, Specialists, Dentists, Physiotherapy, Diagnostic Centers",
            "Real Estate": "Real Estate Agents, Property Developers, Realtors, Real Estate Companies, Property Consultants, Builders",
            "Manufacturing": "Manufacturing Companies, Factories, Industrial Units, Production Facilities, OEM Manufacturers",
            "IT & Technology": "IT Companies, Software Companies, Tech Startups, Web Development, App Development, IT Services, Cloud Services",
            "Education & Training": "Schools, Colleges, Universities, Training Centers, Coaching Classes, Online Education, Tutors",
            "Legal Services": "Lawyers, Law Firms, Legal Consultants, Attorneys, Advocates, Legal Advisors",
            "Financial Services": "Banks, Financial Advisors, Investment Firms, Accounting Firms, Tax Consultants, Financial Planners",
            "Hospitality & Tourism": "Hotels, Resorts, Travel Agencies, Tour Operators, Restaurants, Guest Houses, Holiday Packages",
            "Retail & E-commerce": "Retail Stores, Shopping Centers, Online Stores, E-commerce, Supermarkets, Outlets",
            "Food & Beverage": "Restaurants, Cafes, Food Delivery, Catering Services, Bakeries, Cloud Kitchens, Food Manufacturers",
            "Construction": "Construction Companies, Contractors, Builders, Civil Engineers, Architecture Firms, Interior Designers",
            "Automotive": "Car Dealers, Auto Repair, Car Service Centers, Vehicle Sales, Auto Parts, Garages",
            "Marketing & Advertising": "Marketing Agencies, Advertising Firms, Digital Marketing, SEO Services, Creative Agencies, PR Firms",
            "Consulting": "Business Consultants, Management Consulting, Strategy Consulting, HR Consultants, Advisory Services",
            "Logistics & Transportation": "Logistics Companies, Freight Forwarders, Courier Services, Transportation Services, Warehousing",
            "Beauty & Wellness": "Beauty Salons, Spas, Wellness Centers, Gyms, Yoga Studios, Beauty Parlors, Cosmetics",
            "Entertainment & Media": "Event Planners, Production Houses, Media Companies, Photography Studios, Entertainment Services",
            "Agriculture": "Agricultural Services, Farming Equipment, Agro Products, Organic Farming, Agricultural Consultants",
            "Energy & Utilities": "Solar Companies, Energy Consultants, Utility Services, Renewable Energy, Power Solutions",
            "Telecommunications": "Telecom Companies, Network Providers, Internet Services, Broadband Providers, Mobile Services",
            "Insurance": "Insurance Companies, Insurance Agents, Insurance Brokers, Life Insurance, Health Insurance",
            "Professional Services": "Business Services, Corporate Services, Document Services, Translation Services, Notary Services",
            "Non-Profit & NGO": "NGOs, Charitable Organizations, Non-Profit Organizations, Foundations, Social Services",
            "Sports & Fitness": "Fitness Centers, Sports Clubs, Personal Trainers, Sports Equipment, Martial Arts, Dance Studios"
        }
        
        # Use fallback keyword if no keyword provided
        if not keyword:
            keyword = sector_keywords.get(sector, sector)
        
        # Build location string
        if city and postcode:
            location = f"{city} {postcode}"
        elif city:
            location = city
        elif postcode:
            location = postcode
        else:
            location = ""
        
        Actor.log.info(f"📋 Sector: {sector}, Location: {location or 'Not specified'}")
        Actor.log.info(f"🔍 User keyword: {keyword}")
        Actor.log.info("🤖 Generating intelligent search queries using AI...")
        
        # Generate AI-powered search queries with multi-LLM fallback
        search_queries = await generate_search_queries_with_llm(sector, keyword, city, postcode)
        
        # Initialize Apify client
        token = os.environ.get('APIFY_TOKEN')
        client = ApifyClient(token=token)
        
        all_results = []
        results_per_query = max(1, max_results // len(search_queries))
        
        # Run searches for each AI-generated query
        for query in search_queries:
            # Build full search string
            if location:
                search_string = f"{query} in {location}"
            else:
                search_string = query
            
            Actor.log.info(f"🔍 Searching: {search_string}")
            
            # Run Google Maps Scraper
            run_input = {
                "searchStringsArray": [search_string],
                "maxCrawledPlacesPerSearch": results_per_query,
                "language": "en",
                "includeWebResults": False,
                "maxReviews": 0,
                "maxImages": 0
            }
            
            try:
                run = client.actor("compass/crawler-google-places").call(run_input=run_input)
                
                # Process results
                for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                    lead = {
                        "name": item.get("title", "N/A"),
                        "sector": sector,
                        "searchQuery": query,
                        "city": city if city else "N/A",
                        "postcode": postcode if postcode else "N/A",
                        "phone": item.get("phone", "N/A"),
                        "email": item.get("email", "N/A"),
                        "website": item.get("website", "N/A"),
                        "address": item.get("address", "N/A"),
                        "rating": item.get("totalScore", 0),
                        "reviewCount": item.get("reviewsCount", 0),
                        "googleMapsUrl": item.get("url", "N/A"),
                        "category": item.get("categoryName", "N/A")
                    }
                    all_results.append(lead)
                    Actor.log.info(f"✅ Found: {lead['name']}")
                    
            except Exception as e:
                Actor.log.error(f"❌ Error searching '{query}': {e}")
                continue
        
        # Remove duplicates based on name and address
        unique_results = []
        seen = set()
        for lead in all_results:
            identifier = f"{lead['name']}_{lead['address']}"
            if identifier not in seen:
                seen.add(identifier)
                unique_results.append(lead)
        
        # Limit to max_results
        final_results = unique_results[:max_results]
        
        # Push to dataset
        await Actor.push_data(final_results)
        Actor.log.info(f"=== ✨ Successfully generated {len(final_results)} unique leads using AI ===")

if __name__ == '__main__':
    asyncio.run(main())
