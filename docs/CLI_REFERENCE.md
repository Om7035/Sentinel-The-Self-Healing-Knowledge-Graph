# 📘 Sentinel CLI Reference

Complete reference for all Sentinel command-line interface commands.

## Installation

The `sentinel` command is available after installing the package:

```bash
pip install sentinel-core[all]
```

Or in development mode:

```bash
pip install -e ".[all]"
```

## Global Options

All commands support these global options:

- `--help` - Show help message and exit
- `--version` - Show version and exit

## Commands

### `sentinel init`

Interactive setup wizard for Sentinel.

**Usage:**
```bash
sentinel init [OPTIONS]
```

**Options:**
- `--force, -f` - Overwrite existing .env file without prompting

**What it does:**
1. Checks if Docker is running
2. Collects configuration interactively:
   - Neo4j connection details
   - LLM provider (Ollama, OpenAI, or other)
   - API keys
   - Scraper preferences
3. Generates a `.env` file
4. Verifies all connections
5. Shows scraper status

**Example:**
```bash
# First-time setup
sentinel init

# Force overwrite existing config
sentinel init --force
```

**Interactive Prompts:**
- Neo4j URI (default: `bolt://localhost:7687`)
- Neo4j Username (default: `neo4j`)
- Neo4j Password (hidden input)
- LLM Provider choice (Ollama/OpenAI/Other)
- Model name (e.g., `llama3`, `gpt-4`)
- API keys (if needed)
- Firecrawl API key (optional)

---

### `sentinel watch`

Process a URL through the Sentinel pipeline.

**Usage:**
```bash
sentinel watch [OPTIONS] URL
```

**Arguments:**
- `URL` - The URL to process (required)

**Options:**
- `--verbose, -v` - Show detailed output including stats

**What it does:**
1. Initializes Sentinel components
2. Scrapes the URL
3. Extracts knowledge using AI
4. Stores entities and relationships in Neo4j
5. Updates document state

**Examples:**
```bash
# Process a single URL
sentinel watch https://stripe.com/pricing

# Verbose output
sentinel watch -v https://example.com

# Process multiple URLs (use a script)
for url in url1 url2 url3; do
  sentinel watch $url
done
```

**Output:**
- Success: Shows number of nodes and edges extracted
- Unchanged: Shows number of edges verified
- Error: Shows error message

---

### `sentinel ask`

Ask a natural language question about the knowledge graph.

**Usage:**
```bash
sentinel ask [OPTIONS] QUESTION
```

**Arguments:**
- `QUESTION` - The question to ask (required, use quotes)

**Options:**
- `--time, -t TEXT` - ISO timestamp for time-travel query

**What it does:**
1. Parses the natural language question
2. Queries the knowledge graph
3. Returns an answer with reasoning path

**Examples:**
```bash
# Simple question
sentinel ask "Who founded SpaceX?"

# Complex question
sentinel ask "What are the pricing tiers for Stripe?"

# Time-travel query
sentinel ask "What was the price yesterday?" --time "2024-01-15T12:00:00Z"
```

**Note:** This feature requires the query engine to be fully configured.

---

### `sentinel status`

Show Sentinel system status and health.

**Usage:**
```bash
sentinel status
```

**What it shows:**
1. **Database Connection**
   - Neo4j connectivity status
   - Number of nodes in graph
   - Number of edges in graph

2. **Scraper Status**
   - Available scrapers (Firecrawl, Local)
   - Active scraper
   - Configuration details

3. **LLM Configuration**
   - Model name
   - Provider (Ollama/OpenAI/etc.)
   - Base URL (for Ollama)

**Example:**
```bash
sentinel status
```

**Sample Output:**
```
Database Connection:
✅ Neo4j connected
  Nodes: 42
  Edges: 87

Scraper Status:
🔥 Firecrawl (Premium)
  Status: ✅ Available
  API Key: Configured

🌐 LocalScraper (Free)
  Status: ✅ Available

Active Scraper: Firecrawl

LLM Configuration:
  Model: ollama/llama3
  Ollama URL: http://localhost:11434
```

---

### `sentinel heal`

Run a healing cycle to update stale knowledge.

**Usage:**
```bash
sentinel heal [OPTIONS]
```

**Options:**
- `--days, -d INTEGER` - Threshold for stale nodes in days (default: 7)
- `--dry-run` - Show what would be healed without actually doing it

**What it does:**
1. Finds nodes that haven't been verified in N days
2. Re-processes each stale URL
3. Updates the knowledge graph
4. Reports statistics

**Examples:**
```bash
# Heal nodes older than 7 days
sentinel heal

# Heal nodes older than 30 days
sentinel heal --days 30

# See what would be healed (no changes)
sentinel heal --dry-run

# Aggressive healing (3 days)
sentinel heal -d 3
```

**Output:**
- Number of stale URLs found
- Processing progress
- Total processed count
- Duration

---

### `sentinel version`

Show Sentinel version information.

**Usage:**
```bash
sentinel version
```

**Output:**
```
Sentinel v0.1.0
Self-Healing Temporal Knowledge Graph
```

---

## Environment Variables

Sentinel reads configuration from a `.env` file or environment variables:

### Required

```bash
# Neo4j Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# LLM Configuration
OLLAMA_MODEL=ollama/llama3  # or gpt-4, claude-3-opus, etc.
```

### Optional

```bash
# Ollama (for local LLM)
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI (for cloud LLM)
OPENAI_API_KEY=sk-...

# Other LLM providers
LLM_API_KEY=...

# Premium Scraper
FIRECRAWL_API_KEY=fc-...
```

---

## Exit Codes

- `0` - Success
- `1` - Error (with error message printed)

---

## Tips & Tricks

### Batch Processing

Process multiple URLs from a file:

```bash
while read url; do
  sentinel watch "$url"
  sleep 2  # Be polite to servers
done < urls.txt
```

### Automated Healing

Set up a cron job for automatic healing:

```bash
# Run healing every day at 2 AM
0 2 * * * /path/to/venv/bin/sentinel heal --days 7
```

### Custom Configuration

Use different .env files for different projects:

```bash
# Development
cp .env.dev .env
sentinel watch https://dev.example.com

# Production
cp .env.prod .env
sentinel watch https://example.com
```

### Debugging

Enable verbose output for troubleshooting:

```bash
sentinel watch -v https://example.com 2>&1 | tee debug.log
```

---

## Getting Help

For more information:

```bash
# General help
sentinel --help

# Command-specific help
sentinel watch --help
sentinel heal --help
```

Or visit the [documentation](https://github.com/Om7035/Sentinel-The-Self-Healing-Knowledge-Graph/docs).
