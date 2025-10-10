# 🧠 Project Overview — CLAUDE.md

## Purpose

This repository hosts an **autonomous development system** coordinated by the `OrchestratorAgent`.
The system builds, validates, and maintains a **FastAPI + React (TypeScript)** application with integrated **LangGraph reasoning workflows** and optional **web-scraping pipelines**.

Agents collaborate through structured instructions and follow the standards defined here.

---

## ⚙️ Project Architecture

### Core Agents

| Agent                    | Responsibility                                                                                |
| ------------------------ | --------------------------------------------------------------------------------------------- |
| **OrchestratorAgent**    | Reads issues, routes tasks to specialized agents, manages commits/PRs.                        |
| **BackendAgent**         | Builds and maintains FastAPI routers, schemas, and services using Pydantic v2.                |
| **FrontendAgent**        | Generates React + TypeScript components, MUI-based styling, Axios-based API handling.         |
| **ValidatorAgent**       | Ensures backend ↔ frontend consistency (data flow, logic parity, schema matching).            |
| **RealityManager**       | Performs functional reality checks; identifies gaps between claimed vs. actual completion.    |
| **TestCreatorAgent**     | Creates or updates lightweight unit/integration tests.                                        |
| **WebScrapingValidator** | Builds Playwright / Requests-HTML scrapers with rate limiting, then validates data integrity. |

---

## 🧩 Folder Structure

```
/app
  /routers        # FastAPI routers
  /schemas        # Pydantic models
  /services       # Business logic / DB calls
  /langgraph      # Reasoning / node definitions
  /scrapers       # Web scraping utilities
/frontend
  /components     # React components
  /hooks          # Reusable logic
  /api            # Axios clients
  /types          # TypeScript definitions (generated from backend schemas)
/agents
  orchestrator/
  backend_agent/
  frontend_agent/
  validator_agent/
  test_creator/
  webscraping_validator/
  reality_manager/
/tests
  backend/
  frontend/
  e2e/
/.github/workflows
  claude.yml
```

---

## 🧠 General Agentic Standards

### 1. Core Principles

* **Pragmatism over perfection** – prioritize code that runs and delivers.
* **Explicit contracts** – every agent must define inputs, outputs, and completion criteria.
* **Composable autonomy** – agents should be callable independently or as part of orchestration.
* **Idempotence** – repeated runs should not duplicate results or break previous logic.
* **Traceability** – all agent actions must be reproducible and verifiable via logs or Git commits.

---

## 🐍 Pythonic Standards (BackendAgent / LangGraph)

### Language & Libraries

* Python 3.11+
* FastAPI + Pydantic v2
* SQLAlchemy (if DB used)
* LangGraph for reasoning tasks
* Tenacity for retries
* httpx or requests for external calls

### Structure & Style

* Use type hints (`from __future__ import annotations`)
* Follow `black` + `isort` + `ruff` for formatting
* Avoid circular imports via clear modular design
* Place reusable logic in `/app/services/`
* Use dependency injection for database/session objects
* Validate all external inputs with Pydantic schemas

### LangGraph Nodes

Each node must explicitly define:

```python
class MyNode(LangGraphNode):
    inputs = {"user_query": str}
    outputs = {"response": str}

    def process(self, inputs: dict) -> dict:
        # your logic
        return {"response": "done"}
```

---

## ⚛️ TypeScript / React Standards (FrontendAgent)

### Language & Stack

* React 18+, TypeScript 5+
* MUI v6+ for components
* Axios for API handling
* React Router for navigation
* React Query (optional) for async data fetching

### Code Style

* Use functional components and hooks
* Avoid `any` type usage; prefer generics or interfaces
* Maintain API response typing in `/frontend/types/`
* Follow this naming convention:

  * Components: `PascalCase`
  * Hooks: `useCamelCase`
  * Types/interfaces: `UpperCamelCase`
* Handle all errors gracefully using fallback UIs or toast notifications
* Keep UI logic separate from data logic (`hooks/` for logic, `components/` for display)

Example Axios wrapper:

```ts
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
});

export async function getUser(id: string) {
  const { data } = await api.get<User>(`/users/${id}`);
  return data;
}
```

---

## 🌐 Web Scraping Standards (WebScrapingValidator)

* Prefer **Playwright** for dynamic pages, **Requests-HTML** for static.
* Use async scraping patterns (`async/await`).
* Implement rate limiting (1 req/sec default).
* Store scraping results in `/app/scrapers/data/` (JSON/CSV).
* Add fallback logic for empty or malformed HTML.
* Use randomized user agents when scraping public pages.
* Log all scraping attempts and errors.

Example structure:

```python
class ExampleScraper:
    async def scrape(self, url: str):
        try:
            r = await self.session.get(url, timeout=10)
            r.html.render(timeout=15)
            data = self.parse_html(r.html)
            return data
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
```

---

## ✅ Validation and Testing Standards

### Validation Agent Rules

* Ensure backend → frontend schema parity.
* Verify endpoint availability and response shape.
* Flag mismatched field names, missing properties, or inconsistent data transformations.
* Report findings as `file_path:line` format with severity:

  * **Critical:** Breaks data flow or functionality.
  * **High:** Logic inconsistent between layers.
  * **Medium:** Missing validation or fallback.
  * **Low:** Cosmetic or optimization suggestions.

### TestCreator Standards

* Unit tests for each function/class.
* E2E tests for user flows.
* Prefer `pytest` for backend, `vitest` for frontend.
* All tests must run headlessly in CI via GitHub Actions.

---

## 🧱 Commit & PR Standards

* Each agent’s action should be atomic and traceable.
* PR titles: `[agent-name]: summary of change`
* Include test evidence or validator output in PR description.
* Orchestrator auto-comments must include:

  * Summary of changes
  * Validation or test status
  * Next-step recommendations

---

## 🔒 Security & Environment

* Never hardcode secrets.
* Use `.env` + Pydantic `BaseSettings` for config management.
* Sanitize all scraped data before storage.
* Log only necessary information; redact sensitive fields.

---

## 🧩 Integration Rules

* The **OrchestratorAgent** is the only entity allowed to commit directly or open PRs.
* Sub-agents generate JSON-based write instructions:

  ```json
  [
    { "path": "app/routers/users.py", "write_mode": "overwrite", "contents": "..." }
  ]
  ```
* The orchestrator interprets and applies these instructions via GitHub Actions.

---

## 🚀 Development & Production Deployment

### Local Development Setup

**Backend Setup:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup:**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

**Docker Development Setup:**
```bash
# Stop any running local processes first (Ctrl+C in their terminals)

# Build and start all services
docker-compose up --build

# Or to run in background:
docker-compose up --build -d

# To stop all services:
docker-compose down

# To restart services:
docker-compose restart

# To rebuild and restart (after code changes):
docker-compose down && docker-compose up --build

# To view logs:
docker-compose logs -f

# To view logs for specific service:
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Access Points:**
- Backend API: `http://localhost:8000`
- Frontend UI: `http://localhost:3000`
- API Documentation: `http://localhost:8000/docs`

### Production Deployment

**Docker Deployment (Recommended):**

```dockerfile
# Dockerfile.backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Dockerfile.frontend
FROM node:18-alpine
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///app/dotbot.db
    volumes:
      - ./exports:/app/exports

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://backend:8000
```

**Cloud Deployment:**

*AWS/GCP/Azure:*
- Use container services (ECS, Cloud Run, Container Instances)
- Set up load balancers for high availability
- Configure environment variables for production settings
- Set up monitoring and logging

*Vercel/Netlify (Frontend):*
```bash
# Build command
npm run build

# Environment variables
REACT_APP_API_URL=https://your-backend-api.com
```

**Production Environment Variables:**
```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@host:port/db
LLM_API_KEY=your-openai-api-key
CORS_ORIGINS=https://your-frontend-domain.com
LOG_LEVEL=INFO

# Frontend (.env.production)
REACT_APP_API_URL=https://your-backend-api.com
```

### Performance Optimization

**Backend:**
- Enable FastAPI response caching
- Use connection pooling for database
- Implement rate limiting with Redis
- Add CDN for static exports

**Frontend:**
- Enable code splitting and lazy loading
- Compress images and assets
- Use service workers for caching
- Optimize bundle size with tree shaking

### Monitoring & Health Checks

**Health Endpoints:**
- Backend: `GET /health`
- Database: `GET /health/db`
- Services: `GET /health/services`

**Logging:**
- Structured JSON logging
- Error tracking with Sentry
- Performance monitoring
- Request/response logging

---

## 📈 Continuous Improvement

* RealityManager runs post-deployment audits weekly.
* Reports incomplete or over-engineered modules.
* Recommends simplifications and refactors.
* ValidatorAgent periodically checks schema drift.
* TestCreator adds missing coverage automatically.

---

## 🔄 Recent Implementation Status (October 2025)

### ✅ Completed Major Features

#### **Robust Web Scraping System**
- **Challenge**: Original scraping only extracted 2 articles from LessWrong vs required 20+
- **Solution**: Implemented browser-use AI agent with Playwright fallback
- **Result**: Now successfully extracts 25+ articles from complex sites like LessWrong
- **Tech Stack**: browser-use v0.7.11, Playwright, OpenAI GPT-4o-mini

#### **Async Task Orchestrator**
- **Challenge**: Long scraping operations (25+ articles) timed out at 60 seconds
- **Solution**: Built comprehensive background task system with concurrency
- **Features**:
  - Real-time progress tracking
  - Concurrent article processing (5-10 parallel)
  - Intelligent retry mechanisms with circuit breakers
  - Graceful timeout handling with partial results
- **API Endpoints**:
  - `POST /scraping/async-scrape` - Submit background tasks
  - `GET /scraping/tasks/{id}/status` - Monitor progress
  - `GET /scraping/tasks/{id}/results` - Retrieve results

#### **AI Misalignment Detection Categories**
- **Enhancement**: Expanded from 5 to 10 AI behavior categories
- **New Categories Added**:
  - Proxy Goal Formation
  - Power Seeking  
  - Social Engineering
  - Cognitive Off-Policy Behavior
  - Collusion
- **Frontend**: Dynamic category selection with Material-UI chips
- **Backend**: Updated schemas and analysis workflows

#### **UI/UX Improvements**
- **Modern Interface**: Material-UI v6 with consistent theming
- **Export Options**: Simplified to JSON/CSV (removed database option)
- **Form Validation**: Real-time URL validation and error handling
- **Responsive Design**: Mobile-friendly layout with proper spacing

### 🛠 Technical Architecture Improvements

#### **Browser Automation Strategy**
```python
# Hybrid approach for optimal performance:
# 1. Playwright for fast link discovery (no LLM costs)
# 2. AI agents for intelligent content extraction
# 3. Fallback mechanisms for reliability

class BrowserScraper:
    async def scrape_with_depth(self, url: str, max_depth: int = 2):
        # Homepage: Extract links with Playwright
        if depth == 0:
            result = await self._scrape_and_extract_links_playwright(url)
            # Found 25+ links from LessWrong in seconds
        
        # Articles: Use AI agent for intelligent extraction  
        else:
            result = await self.run_browser_agent(task, url)
```

#### **Concurrent Processing Architecture**
```python
# Task orchestrator with production-ready features:
class TaskOrchestrator:
    async def process_urls_concurrently(self, urls: List[str]):
        # Process 5-10 articles simultaneously
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        tasks = [self._process_with_semaphore(semaphore, url) 
                for url in urls]
        
        # Real-time progress tracking
        results = await asyncio.gather(*tasks, return_exceptions=True)
```

#### **API Performance Optimizations**
- **Response Time**: Sub-second task submission
- **Scalability**: Handles 25+ concurrent article processing
- **Memory Efficiency**: Batched processing with cleanup
- **Error Recovery**: Individual article failures don't break entire operation

### 📊 Performance Metrics

#### **Before Implementation**:
- ❌ 60-second timeouts on multi-depth scraping
- ❌ Only 2 articles extracted from LessWrong  
- ❌ Mock data instead of real content
- ❌ Synchronous processing blocking API

#### **After Implementation**:
- ✅ **26/26 articles** successfully scraped from LessWrong
- ✅ **100% completion rate** with robust error handling
- ✅ **~2 articles/second** processing speed
- ✅ **Real-time progress tracking** (80.77% complete, 21/26 items)
- ✅ **Zero timeouts** with background task processing

### 🔧 Development Tools & Infrastructure

#### **API Key Management**
- **OpenAI Integration**: Configured for browser-use AI agent
- **Environment Variables**: Secure .env configuration
- **Fallback Strategy**: Playwright-only mode when AI unavailable

#### **Testing & Validation**
- **Live Testing**: Successfully tested with LessWrong, example.com
- **Error Scenarios**: Tested timeout handling, partial failures
- **Performance Testing**: Validated 25+ article concurrent processing
- **API Endpoints**: All async orchestrator endpoints tested and functional

#### **Monitoring & Observability**
- **Task Status Tracking**: Real-time progress with detailed metrics
- **Error Classification**: Retry vs permanent failure distinction  
- **Performance Metrics**: Processing time, success rates, concurrency stats
- **Health Checks**: Service status and capability reporting

### 📋 Configuration Standards

#### **Environment Variables**
```bash
# Required for browser-use AI agent
OPENAI_API_KEY=sk-proj-...

# LangGraph integration
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT="data agent"

# Optional for enhanced functionality
GOOGLE_API_KEY=...  # For Gemini models (not required)
```

#### **Scraping Configuration**
```python
# Optimized settings for production
MAX_DEPTH = 2              # Deep enough for comprehensive content
MAX_CONCURRENT_TASKS = 5   # Balanced performance vs resources  
REQUEST_TIMEOUT = 30       # Per-article timeout
TASK_TIMEOUT = 300         # Overall task timeout (5 minutes)
MAX_ARTICLES_PER_SITE = 25 # Reasonable limit per domain
```

### 🎯 Next Development Priorities

1. **Schema Updates**: Change "severity" → "relevance_to_category" in AI reports
2. **SQL Logging**: Implement automatic database logging (pending credentials)
3. **Advanced Analytics**: Enhanced AI behavior detection algorithms
4. **Performance Tuning**: Further optimization for enterprise scale
5. **UI Polish**: Real-time progress display in frontend

---
