# AI Operations Assistant

A production-ready multi-agent AI system that accepts natural language tasks and executes them using a combination of LLM reasoning and real API integrations.

## Key Features

- **Multi-Agent Architecture**: Planner → Executor → Verifier agents working in sequence
- **Fast & Async**: Built with FastAPI for high-performance async operations with parallel tool execution
- **6 Real API Integrations**: GitHub, Weather, News, Countries, Crypto, Wikipedia
- **Production-Ready**: Proper error handling, logging, and structured outputs
- **Streamlit UI**: Beautiful, professional web interface for task execution

## Architecture

```
User Request (Streamlit UI / FastAPI)
    ↓
┌─────────────────────────────────┐
│  Multi-Agent Pipeline           │
├─────────────────────────────────┤
│  Step 1: Planner Agent          │
│    ↓ (LLM-powered planning)     │
│  Step 2: Executor Agent         │
│    ↓ (Parallel API calls)       │
│  Step 3: Verifier Agent         │
│    ↓ (LLM verification)         │
│  Return: Formatted Result       │
└─────────────────────────────────┘
    ↓
User receives: Summary + Details
```

### Agent Responsibilities

1. **Planner Agent**
   - Uses an LLM (OpenAI) to convert natural language into structured execution plan
   - Selects appropriate tools and defines parameters
   - Returns JSON plan with sequential steps

2. **Executor Agent**
   - Executes each step from the plan
   - **Runs independent steps in parallel** for 3-4x faster performance
   - Calls real APIs (GitHub, Weather, News, etc.)
   - Collects results and handles errors gracefully

3. **Verifier Agent**
   - Uses an LLM (OpenAI) to validate results
   - Formats output into user-friendly summary
   - Extracts sources and verifies completeness

## Key Advantages & Advanced Features

This implementation goes beyond the basic requirements with several production-ready features:

### 1. AI-Powered Query Optimization
- **Intelligent typo correction**: Automatically corrects misspelled city names, cryptocurrency IDs, and country names using LLM
- **Context-aware**: Understands different contexts (city, crypto, general) for better correction accuracy
- **User-friendly**: Provides correction notes so users know when their input was corrected
- **Example**: "Bengalore" → "Bangalore", "btc" → "bitcoin"

### 2. Resilient API Calls with Retry Logic
- **Automatic retries**: Uses exponential backoff (1s → 2s → 4s) for transient failures
- **Smart error handling**: Retries on network errors, 5xx server errors, and rate limits (429)
- **No unnecessary retries**: Doesn't retry on 4xx client errors (invalid requests)
- **Production-ready**: Handles API failures gracefully without crashing

### 3. Parallel Execution for Performance
- **3-4x faster**: Independent tool calls run concurrently using `asyncio.gather()`
- **Smart dependency detection**: Automatically detects when steps depend on previous results
- **Optimal resource usage**: Maximizes throughput while maintaining correctness
- **Example**: Weather + GitHub + News calls happen simultaneously instead of sequentially

### 4. Comprehensive Error Handling
- **Graceful degradation**: System continues even if some tools fail
- **Detailed error messages**: Provides helpful, context-aware error explanations
- **Verification notes**: Clearly indicates what succeeded and what failed
- **User guidance**: Suggests corrections and alternatives when queries fail

### 5. Structured LLM Outputs
- **Type-safe**: Uses Pydantic models for validation
- **Consistent**: Structured JSON responses from LLM with schema validation
- **Reliable**: Handles JSON parsing errors gracefully with fallbacks

### 6. Production-Ready Architecture
- **Separation of concerns**: Clear agent responsibilities (Planner, Executor, Verifier)
- **Modular design**: Easy to add new tools or agents
- **Comprehensive logging**: Detailed logs for debugging and monitoring
- **API-first**: RESTful API with OpenAPI documentation

### 7. Beautiful User Interface
- **Professional design**: Dark theme with modern UI/UX
- **Real-time feedback**: Progress indicators and status updates
- **Rich results display**: Expandable sections, formatted summaries, source links
- **Task history**: Quick access to recent tasks

### 8. Developer Experience
- **Clear code structure**: Well-organized, readable codebase
- **Type hints**: Full type annotations for better IDE support
- **Documentation**: Comprehensive docstrings and comments
- **Easy to extend**: Simple pattern for adding new tools

## Quick Start

### Prerequisites

- Python 3.9+
- API Keys (see below)

### 1. Clone & Install

```bash
Create a folder having any name
# Clone the repository
git clone https://github.com/Rohit-2703/AI-Operation-Assistant.git
cd .\AI-Operation-Assistant\

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Environment Variables

Create a `.env` file in the project root:

```bash

OPENAI_API_KEY=sk-...  # Get from: https://platform.openai.com/
OPENAI_MODEL=gpt-4o-mini
# OpenWeatherMap API Key (REQUIRED)
OPENWEATHERMAP_API_KEY=your_key  # Get from: https://openweathermap.org/api
# NewsAPI Key (REQUIRED)
NEWS_API_KEY=your_key  # Get from: https://newsapi.org/
```

**Note**: GitHub, Countries, Crypto, and Wikipedia APIs don't require keys!

### 3. Run the Backend API

```bash
uvicorn main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

### 4. Run the Streamlit UI

Open a **new terminal** and run:

```bash
cd .\AI-Operation-Assistant\ (make sure you are in the root)
streamlit run streamlit_app.py
```

The UI will be available at:
- **Streamlit UI**: http://localhost:8501

## API Documentation

### Execute a Task

**POST** `/api/task/execute`

Execute a task and get results immediately.

```json
{
  "task": "Find the top 3 Python ML repos and get the weather in London"
}
```

**Response:**
```json
{
  "task": "Find the top 3 Python ML repos and get the weather in London",
  "summary": "## Results\n\n**GitHub Repositories:**\n- ...\n\n**Weather:**\n- ...",
  "details": {
    "github": {...},
    "weather": {...}
  },
  "sources": ["https://github.com/..."],
  "execution_plan": {...},
  "verified": true,
  "verification_notes": null
}
```

### List Available Tools

**GET** `/api/tools`

Returns all available tools and their capabilities.

### Get Example Tasks

**GET** `/api/examples`

Returns example tasks you can try.

### Health Check

**GET** `/health`

Check if the service is running.

## Example Tasks to Try

### 1. GitHub + Weather
```
Find the top 3 Python machine learning repos and get the weather in San Francisco
```

### 2. News + Countries
```
Get the latest news about climate change and tell me about the countries mentioned
```

### 3. Crypto + Weather
```
What's the current Bitcoin price and the weather in London?
```

### 4. GitHub + Wikipedia
```
Search for 'quantum computing' repositories and give me a Wikipedia summary of quantum computing
```

### 5. Multi-Tool Complex Task
```
Find top AI repositories, get trending cryptocurrencies, and summarize recent AI news
```

### 6. News + Wikipedia + Countries
```
Get news about space exploration and tell me about countries with space programs
```

## Integrated APIs

| API | Purpose | Auth Required | Actions |
|-----|---------|---------------|---------|
| **GitHub** | Repository search, stars, contributors | No | `search_repositories`, `get_repository`, `get_contributors` |
| **OpenWeatherMap** | Current weather, forecasts | Yes | `get_current_weather`, `get_forecast` |
| **NewsAPI** | Latest news articles | Yes | `get_top_headlines`, `search_news` |
| **REST Countries** | Country information | No | `get_country_by_name`, `get_countries_by_region` |
| **CoinGecko** | Crypto prices, market data | No | `get_price`, `get_trending`, `get_market_data` |
| **Wikipedia** | Article summaries, search | No | `search`, `get_summary` |

## Using the Streamlit UI

The Streamlit UI provides a beautiful, professional interface for interacting with the AI Operations Assistant.

**Features:**
- Task input with example tasks
- Real-time execution with progress indicators
- Detailed results display with expandable sections
- Execution plan visualization
- Detailed tool outputs
- Verification notes and error messages
- Recent task history

**Layout:**
- **Left Sidebar**: Recent tasks, About section, Metrics
- **Main Area**: Task input, Execute button, Results
- **Right Column**: Example tasks, Available tools

## Testing the System

### Using the Streamlit UI (Recommended):

1. Start the backend: `uvicorn main:app --reload`
2. Start the UI: `streamlit run streamlit_app.py`
3. Open http://localhost:8501
4. Enter a task or click an example task
5. Click "Execute Task"
6. View results immediately

### Using curl:

```bash
curl -X POST "http://localhost:8000/api/task/execute" \
  -H "Content-Type: application/json" \
  -d '{"task": "Find top Python repos and get weather in Tokyo"}'
```

### Using Python:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/task/execute",
    json={"task": "Get the latest AI news and Bitcoin price"}
)
result = response.json()
print(result["summary"])  # View the formatted summary
print(result["details"])  # View detailed tool outputs
```

### Using the API Docs:

1. Go to http://localhost:8000/docs
2. Click on **POST /api/task/execute**
3. Click "Try it out"
4. Enter your task and execute
5. View the complete response with summary and details

## Project Structure

```
ai_ops_assistant/
├── agents/
│   ├── __init__.py
│   ├── planner.py          # Planner Agent (LLM-powered)
│   ├── executor.py         # Executor Agent (API calls)
│   └── verifier.py         # Verifier Agent (LLM validation)
├── tools/
│   ├── __init__.py
│   ├── github_tool.py      # GitHub API integration
│   ├── weather_tool.py     # OpenWeatherMap integration
│   ├── news_tool.py        # NewsAPI integration
│   ├── countries_tool.py   # REST Countries integration
│   ├── crypto_tool.py      # CoinGecko integration
│   └── wikipedia_tool.py   # Wikipedia integration
├── llm/
│   ├── __init__.py
│   └── client.py           # OpenAI API wrapper
├── models/
│   ├── __init__.py
│   └── schemas.py          # Pydantic models
├── workflows/
│   ├── __init__.py
│   └── ai_ops_workflow.py  # Pipeline step functions
├── streamlit_app.py         # Streamlit UI frontend
├── main.py                 # FastAPI application
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

### Environment Variables

**Required:**
- `OPENAI_API_KEY`: OpenAI API key (required)
- `OPENWEATHERMAP_API_KEY`: Weather API key (required)
- `NEWS_API_KEY`: News API key (required)

**Optional:**
- `OPENAI_MODEL`: OpenAI model name (default: "gpt-4o-mini")

### Performance Tuning

The system automatically executes independent tool calls in parallel for 3-4x faster performance. No configuration needed!

## Known Limitations

1. **API Rate Limits**: Free tier APIs have rate limits
   - NewsAPI: 100 requests/day on free tier
   - OpenWeatherMap: 1000 calls/day on free tier
   - CoinGecko: 50 calls/minute

2. **LLM Costs**: OpenAI API is paid (pay-per-use)

3. **No Persistent Storage**: Results are not stored in a database
   - Can be added with PostgreSQL/MongoDB
   - Task history is stored in Streamlit session state (temporary)

## Future Improvements

Potential enhancements:

- [ ] **Parallel Execution**: Implemented - **Independent steps run concurrently**
- [ ] **Result Caching**: Cache API responses to reduce costs
- [ ] **Result Storage**: Store execution history in database
- [ ] **More Tools**: Add Slack, Email, Google Sheets, etc.
- [ ] **Streaming Responses**: Stream results as they're generated

## Troubleshooting

### Issue: "OPENAI_API_KEY environment variable is required"
**Solution**: Make sure you've created `.env` file in the project root and added your OpenAI API key.

### Issue: "Backend API not running" in Streamlit
**Solution**: Make sure FastAPI is running (`uvicorn main:app --reload`) before starting Streamlit.

### Issue: Tool API calls failing
**Solution**: 
- Check that your API keys are valid and have available quota
- Check the logs for specific error messages
- Verify API keys in `.env` file

### Issue: Task execution times out
**Solution**: 
- Check network connectivity
- Verify API keys are correct
- Check API rate limits haven't been exceeded
- Increase timeout in `streamlit_app.py` if needed (default: 60s)

### Issue: Empty results or missing data
**Solution**: 
- Check the "Verification Notes" section in results
- Review logs for failed steps
- Verify the task is clear and specific

## Acknowledgments

- **OpenAI**: For powerful LLM capabilities
- **FastAPI**: For the amazing async web framework
- **Streamlit**: For the beautiful UI framework
- All the open APIs that made this possible!

---

Built for the GenAI Intern Assignment
