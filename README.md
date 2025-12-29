# 🤖 Multi-LLM AI-Powered Lead Generator

Generate high-quality business leads using AI-powered search query generation. Supports multiple LLM providers with automatic fallback for maximum reliability.

## 🌟 Features

- **🧠 Multi-LLM Support**: Uses Claude, OpenAI GPT-4, Google Gemini, or Groq
- **🔄 Automatic Fallback**: If one AI provider fails, automatically tries the next
- **🎯 Intelligent Search**: AI generates 3-5 diverse search queries per request
- **📍 Location-Aware**: Supports city and postcode targeting
- **🔍 Comprehensive Coverage**: Scrapes real business data from Google Maps
- **✨ Deduplication**: Automatically removes duplicate results
- **24 Industry Sectors**: Pre-configured for major industries

## 📋 Input Parameters

### Required
- **sector** (required): Select from 24 industry sectors

### Optional
- **city**: Target city (e.g., "Chennai", "Mumbai")
- **postcode**: Postal/ZIP code for precise targeting (e.g., "600001")
- **keyword**: Refine search within sector (e.g., "Dermatologist" for Healthcare)
- **maxResults**: Maximum number of leads (default: 10)

## 🚀 How It Works

### 1. AI Query Generation
When you request leads for "Healthcare" with keyword "pediatric care":

**AI generates multiple targeted searches:**
- "pediatricians"
- "children's hospitals" 
- "child care clinics"
- "pediatric specialists"
- "kids health centers"

### 2. Multi-Source Scraping
Each query searches Google Maps for real businesses, capturing:
- Business name
- Phone number
- Email (when available)
- Website
- Address
- Google rating & review count
- Google Maps URL
- Business category

### 3. Smart Deduplication
Removes duplicate businesses found across multiple searches.

## 🔑 LLM Provider Configuration

The actor tries providers in this order:

1. **Claude (Anthropic)** - Always available in Apify Actors ✅
2. **OpenAI GPT-4** - Requires `OPENAI_API_KEY` environment variable
3. **Google Gemini** - Requires `GOOGLE_API_KEY` environment variable
4. **Groq** - Requires `GROQ_API_KEY` environment variable

### Setting API Keys (Optional)

**Claude works by default** - no setup needed! 

For other providers, add environment variables in Apify Console:

1. Go to your Actor → Settings → Environment Variables
2. Add keys as needed:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `GOOGLE_API_KEY` - Your Google AI API key
   - `GROQ_API_KEY` - Your Groq API key

**Note**: The actor will automatically fall back to the next provider if one is unavailable.

## 📊 Example Usage

### Example 1: Healthcare Leads
```json
{
  "sector": "Healthcare",
  "city": "Chennai",
  "keyword": "Dermatologist",
  "maxResults": 20
}
```

**AI generates:**
- "dermatologists"
- "skin clinics"
- "cosmetic dermatology"
- "dermatology specialists"

**Result:** 20 unique dermatology providers in Chennai

### Example 2: Broad Search
```json
{
  "sector": "IT & Technology",
  "keyword": "AI Startups",
  "maxResults": 50
}
```

**AI generates:**
- "AI companies"
- "machine learning startups"
- "artificial intelligence firms"
- "AI development companies"

**Result:** 50 AI/ML companies (nationwide)

### Example 3: Precise Location
```json
{
  "sector": "Real Estate",
  "city": "Mumbai",
  "postcode": "400001",
  "keyword": "Luxury Properties",
  "maxResults": 15
}
```

**Result:** 15 luxury real estate businesses in Mumbai 400001

## 🎯 Supported Sectors

1. Healthcare
2. Real Estate
3. Manufacturing
4. IT & Technology
5. Education & Training
6. Legal Services
7. Financial Services
8. Hospitality & Tourism
9. Retail & E-commerce
10. Food & Beverage
11. Construction
12. Automotive
13. Marketing & Advertising
14. Consulting
15. Logistics & Transportation
16. Beauty & Wellness
17. Entertainment & Media
18. Agriculture
19. Energy & Utilities
20. Telecommunications
21. Insurance
22. Professional Services
23. Non-Profit & NGO
24. Sports & Fitness

## 📤 Output Format

Each lead contains:

```json
{
  "name": "Apollo Skin Clinic",
  "sector": "Healthcare",
  "searchQuery": "dermatologists",
  "city": "Chennai",
  "postcode": "600001",
  "phone": "+91 44 1234 5678",
  "email": "contact@apolloskin.com",
  "website": "https://apolloskin.com",
  "address": "123 Main St, Chennai 600001",
  "rating": 4.5,
  "reviewCount": 234,
  "googleMapsUrl": "https://maps.google.com/...",
  "category": "Dermatology clinic"
}
```

## 💡 Best Practices

1. **Use specific keywords** for better targeting (e.g., "Pediatrician" vs just "Healthcare")
2. **Add location** for local businesses
3. **Increase maxResults** for comprehensive coverage
4. **Let AI work**: Leave keyword empty to let AI decide the best searches
5. **Multiple runs**: For large campaigns, run multiple times with different keywords

## 🔧 Technical Details

- **Runtime**: Python 3.11
- **Google Maps Scraper**: Uses Apify's official Google Places scraper
- **AI Models**: 
  - Claude Sonnet 4
  - GPT-4o-mini (fast & cost-effective)
  - Gemini 1.5 Flash
  - Llama 3.3 70B (via Groq)
- **Rate Limiting**: Respects Apify platform limits
- **Timeouts**: 30 seconds per LLM call

## 🛠️ Troubleshooting

**"All LLM providers failed"**
- Claude should always work by default
- Check if you've added API keys for other providers
- Check Apify logs for specific errors

**"Dataset is empty"**
- Verify your search parameters
- Try a broader search (remove postcode, use common keywords)
- Check if Google Maps has businesses matching your criteria

**"Too few results"**
- Increase `maxResults`
- Broaden your search area (remove postcode)
- Try a more general keyword

## 📞 Support

For issues or questions:
- Check Apify logs for detailed error messages
- Review input parameters
- Ensure sector and location are valid

## 🎉 Credits

Built with:
- Apify Platform
- Google Maps Scraper (compass/crawler-google-places)
- Multiple LLM providers (Anthropic, OpenAI, Google, Groq)
