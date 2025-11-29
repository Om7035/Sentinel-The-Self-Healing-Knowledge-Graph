# 🚀 Sentinel - Quick Setup Guide

## ✅ Project Structure (Clean!)

Your Sentinel project now has a clean, professional structure:

```
Sentinel/
├── sentinel_core/          # Core library (pip-installable)
├── sentinel_service/       # FastAPI backend
├── sentinel_ui/            # Next.js frontend
├── examples/               # Usage examples
├── tests/                  # Test suite
├── docker-compose.yml      # Infrastructure
├── pyproject.toml          # Package config
├── requirements.txt        # Dependencies
├── .env.example            # Environment template
└── README.md               # Documentation
```

## 📋 Prerequisites

Before starting, ensure you have:

- ✅ **Docker Desktop** installed and running
- ✅ **Python 3.11+** installed
- ✅ **Node.js 18+** installed (for the UI)
- ✅ **Ollama** running locally (for LLM extraction)
- ✅ **Firecrawl API Key** from [firecrawl.dev](https://firecrawl.dev)

## 🎯 Setup Steps

### Step 1: Start Infrastructure (Neo4j, Postgres)

```bash
docker-compose up -d
```

**Verify it's running:**
```bash
docker-compose ps
```

You should see:
- `sentinel_neo4j` - Running on ports 7474 (HTTP) and 7687 (Bolt)
- `sentinel_postgres` - Running on port 5433

**Access Neo4j Browser:**
- URL: http://localhost:7474
- Username: `neo4j`
- Password: `password`

### Step 2: Install the Package

```bash
pip install -e .
```

**Verify installation:**
```bash
python -c "from sentinel_core import Sentinel; print('✅ Installed!')"
```

### Step 3: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your credentials
# Required variables:
# - FIRECRAWL_API_KEY=your_key_here
# - NEO4J_PASSWORD=password
# - POSTGRES_PASSWORD=sentinel_password
```

### Step 4: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_phase1.py -v

# Run with coverage
pytest --cov=sentinel_core --cov-report=html
```

### Step 5: Start the API Service

```bash
cd sentinel_service
python main.py
```

The API will be available at: **http://localhost:8000**

**API Endpoints:**
- `GET /` - Health check
- `GET /api/health` - Detailed health status
- `GET /api/graph-snapshot` - Get graph visualization data
- `GET /api/stats` - Graph statistics
- `POST /api/ingest` - Ingest a URL
- `POST /api/query` - Natural language query

**Test the API:**
```bash
curl http://localhost:8000/api/health
```

### Step 6: Start the UI (Optional)

In a **new terminal**:

```bash
cd sentinel_ui
npm install
npm run dev
```

The UI will be available at: **http://localhost:3000**

## 🧪 Testing the System

### Test 1: Ingest a URL

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://en.wikipedia.org/wiki/Tesla,_Inc."}'
```

### Test 2: Query the Graph

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Who founded Tesla?"}'
```

### Test 3: View the Graph

```bash
curl http://localhost:8000/api/graph-snapshot | jq
```

## 🧹 Cleanup Notes

### Legacy Frontend Folder

The old `frontend/` folder is still present because it's locked by a process. To remove it:

1. **Close VSCode** and any terminals
2. **Stop any Node processes**: `taskkill /F /IM node.exe` (Windows)
3. **Delete manually**: Right-click → Delete
4. Or run: `python cleanup_legacy.py` again

### What Was Removed

✅ Removed:
- `backend/` - Old backend structure
- `scripts/` - Old scripts
- `config/` - Old config directory
- `test_data/` - Test artifacts
- All unnecessary `.md` files (11 files)
- Test scripts: `inspect_*.py`, `test_*.py`, `seed_graph.py`

✅ Kept:
- `README.md` - Main documentation
- `REFACTORING_COMPLETE.md` - Migration guide
- `verify_refactoring.py` - Verification script
- `cleanup_legacy.py` - Cleanup script

## 📊 Project Status

✅ **Package Installation**: Working  
✅ **Import System**: Working  
✅ **Tests**: Ready to run  
✅ **API Service**: Ready to start  
✅ **Frontend**: Ready to start  
✅ **Docker Infrastructure**: Configured  

## 🎉 You're Ready!

Your Sentinel project is now:
- ✅ Clean and organized
- ✅ Following Python best practices
- ✅ Pip-installable as a package
- ✅ Ready for development
- ✅ Ready for production deployment

## 🐛 Troubleshooting

### Docker Issues

```bash
# View logs
docker-compose logs -f neo4j
docker-compose logs -f postgres

# Restart services
docker-compose restart

# Clean start
docker-compose down -v
docker-compose up -d
```

### Import Errors

```bash
# Reinstall in editable mode
pip install -e .

# Verify installation
python -c "from sentinel_core import Sentinel; print('OK')"
```

### Frontend Locked

If you can't delete the `frontend/` folder:
1. Close all VSCode windows
2. Stop all Node processes
3. Restart your computer if needed
4. Then delete manually or run `cleanup_legacy.py`

## 📚 Next Steps

1. **Read the documentation**: `README.md`
2. **Check examples**: `examples/basic_bot.py`
3. **Run the tests**: `pytest tests/ -v`
4. **Start building**: Use the API or library directly

---

**Need help?** Check `README.md` or `REFACTORING_COMPLETE.md` for detailed information.
