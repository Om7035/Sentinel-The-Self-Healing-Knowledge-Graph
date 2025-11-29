# 🧠 Sentinel Knowledge Graph - Complete Architecture Guide

## 📖 What is Sentinel? (Explained Simply)

Imagine you're trying to understand how the world works by collecting facts from websites. You read that "Elon Musk founded SpaceX" from one website, and "SpaceX was founded in 2002" from another. Sentinel is like a smart librarian that:

1. **Reads websites** automatically (using Firecrawl)
2. **Extracts facts** from the text (using AI/LLM)
3. **Stores them as connections** between things (like a web of knowledge)
4. **Lets you visualize** these connections as an interactive 3D graph
5. **Keeps everything fresh** by checking if facts are still true
6. **Remembers history** - you can see how knowledge changed over time

Think of it like a **living, self-healing brain** that learns from the internet and never forgets!

---

## 🏗️ How Sentinel Works (Step-by-Step)

### Phase 1: Data Collection 🔍
```
Website URL → Firecrawl → Clean HTML/Text
                ↓
         "Elon Musk founded SpaceX in 2002"
```

**What happens:**
- You give Sentinel a website URL
- Firecrawl (a web scraper) visits the website and extracts clean text
- It removes ads, navigation, and other noise
- Returns just the useful content

### Phase 2: Knowledge Extraction 🧠
```
Clean Text → LLM (AI Model) → Extract Facts
                ↓
    [Entity: "Elon Musk"] 
    [Relation: "FOUNDED"]
    [Entity: "SpaceX"]
    [Confidence: 0.95]
```

**What happens:**
- The extracted text goes to an AI model (running locally via Ollama)
- The AI identifies important entities (people, companies, places)
- It finds relationships between them
- It assigns confidence scores (how sure it is)

### Phase 3: Storage & Temporal Tracking ⏰
```
Facts → Graph Database (Neo4j)
           ↓
    Stores with timestamps:
    - valid_from: When fact became true
    - valid_to: When fact became false (or NULL if still true)
    - last_verified: When we last confirmed it
    - confidence: How confident we are
```

**What happens:**
- Facts are stored as nodes (entities) and edges (relationships)
- Each fact has a timestamp showing when it was true
- This allows "time travel" - see the graph at any point in history
- Prevents duplicate storage through content hashing

### Phase 4: Self-Healing 🔄
```
Every 6 hours:
1. Find stale facts (not verified in 7+ days)
2. Re-scrape the original website
3. Extract new facts
4. Compare with old facts
5. Update or invalidate as needed
```

**What happens:**
- Sentinel automatically checks if old facts are still true
- If a website changed, it updates the knowledge graph
- If a fact is no longer true, it marks it as invalid
- The graph stays accurate and up-to-date

### Phase 5: Visualization & Querying 👁️
```
User Interface (3D Graph)
    ↓
Drag nodes around
    ↓
Ask questions: "Who founded SpaceX?"
    ↓
AI finds the answer by traversing the graph
    ↓
Shows the path: Elon Musk → FOUNDED → SpaceX
```

**What happens:**
- You see the knowledge as an interactive 3D graph
- Nodes are entities (people, companies, etc.)
- Lines are relationships (founded, worked at, etc.)
- You can drag nodes to rearrange
- You can ask natural language questions

---

## 🔧 Technical Architecture

### Complete System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Sentinel UI (Next.js + React + Three.js)                   │   │
│  │  ┌────────────────────────────────────────────────────────┐ │   │
│  │  │  3D Graph Visualization (Neurons & Synapses)          │ │   │
│  │  │  - Draggable nodes                                     │ │   │
│  │  │  - Connected relationships                            │ │   │
│  │  │  - Time-travel slider                                 │ │   │
│  │  │  - Natural language query box                         │ │   │
│  │  └────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              ↕ (HTTP/REST)
┌─────────────────────────────────────────────────────────────────────┐
│                    SENTINEL SERVICE (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  API Endpoints                                               │   │
│  │  • POST /api/ingest - Add new URL                           │   │
│  │  • POST /api/query - Ask questions                          │   │
│  │  • GET /api/graph-snapshot - Get graph at time T            │   │
│  │  • GET /api/stats - Get statistics                          │   │
│  │  • GET /api/health - Check system status                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                    SENTINEL CORE (Python Library)                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  1. SentinelScraper (Firecrawl Integration)                 │   │
│  │     - Visits websites                                        │   │
│  │     - Extracts clean text                                    │   │
│  │     - Hashes content for deduplication                       │   │
│  │                                                              │   │
│  │  2. InfoExtractor (LLM-Powered)                             │   │
│  │     - Uses Ollama (local AI model)                           │   │
│  │     - Extracts entities and relationships                    │   │
│  │     - Assigns confidence scores                             │   │
│  │                                                              │   │
│  │  3. GraphManager (Neo4j Adapter)                            │   │
│  │     - Stores facts with timestamps                          │   │
│  │     - Manages temporal validity                             │   │
│  │     - Supports time-travel queries                          │   │
│  │                                                              │   │
│  │  4. Sentinel Orchestrator                                   │   │
│  │     - Coordinates all components                            │   │
│  │     - Runs healing cycles                                   │   │
│  │     - Manages the entire workflow                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Firecrawl API   │  │  Ollama (Local)  │  │  Neo4j Database  │  │
│  │  (Web Scraper)   │  │  (AI/LLM Model)  │  │  (Graph Storage) │  │
│  │                  │  │                  │  │                  │  │
│  │  Extracts text   │  │  Extracts facts  │  │  Stores facts    │  │
│  │  from websites   │  │  from text       │  │  with timestamps │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Component Details

### 1. **Firecrawl** (Web Scraper)
- **What it does:** Visits websites and extracts clean, readable text
- **Why it's needed:** Websites have lots of noise (ads, navigation, etc.)
- **How it works:** 
  - Takes a URL as input
  - Renders the page like a browser
  - Extracts main content
  - Returns clean markdown/text
- **Example:**
  ```
  Input: https://en.wikipedia.org/wiki/SpaceX
  Output: "SpaceX is an American aerospace manufacturer and space 
           transportation services company founded in 2002 by Elon Musk..."
  ```

### 2. **Ollama** (Local AI Model)
- **What it does:** Runs an AI model locally on your computer
- **Why it's needed:** Extract structured facts from unstructured text
- **How it works:**
  - Takes clean text as input
  - Uses a language model (like Llama 3.1)
  - Identifies entities: "Elon Musk", "SpaceX", "2002"
  - Identifies relationships: "FOUNDED", "LOCATED_IN"
  - Returns structured triples
- **Example:**
  ```
  Input: "Elon Musk founded SpaceX in 2002"
  Output: 
  - Entity 1: "Elon Musk" (Person)
  - Relation: "FOUNDED"
  - Entity 2: "SpaceX" (Company)
  - Confidence: 0.95
  ```

### 3. **Neo4j** (Graph Database)
- **What it does:** Stores facts as a network of connected nodes
- **Why it's needed:** Relationships are as important as facts
- **How it works:**
  - Nodes = Entities (people, companies, places)
  - Edges = Relationships (founded, worked at, located in)
  - Each edge has metadata (timestamp, confidence, source)
- **Example:**
  ```
  Node 1: {id: "elon_musk", name: "Elon Musk", type: "Person"}
  Edge: {from: "elon_musk", to: "spacex", relation: "FOUNDED", 
         valid_from: "2002-01-01", confidence: 0.95}
  Node 2: {id: "spacex", name: "SpaceX", type: "Company"}
  ```

### 4. **FastAPI** (REST API)
- **What it does:** Exposes Sentinel functionality via HTTP endpoints
- **Why it's needed:** Allows the UI and external apps to use Sentinel
- **Endpoints:**
  - `POST /api/ingest` - Add a new URL to analyze
  - `POST /api/query` - Ask natural language questions
  - `GET /api/graph-snapshot` - Get graph at a specific time
  - `GET /api/stats` - Get statistics
  - `GET /api/health` - Check if system is running

### 5. **Next.js UI** (Frontend)
- **What it does:** Provides an interactive 3D visualization
- **Why it's needed:** Makes the knowledge graph easy to explore
- **Features:**
  - 3D force-directed graph (nodes repel/attract like magnets)
  - Draggable nodes (drag to rearrange)
  - Time-travel slider (see graph at any point in history)
  - Query interface (ask questions in natural language)
  - Real-time updates (graph updates as new data arrives)

---

## 📊 Data Flow Example

Let's trace what happens when you submit a URL:

```
1. USER SUBMITS URL
   ↓
   URL: "https://en.wikipedia.org/wiki/Tesla,_Inc."

2. FIRECRAWL SCRAPES
   ↓
   Text: "Tesla, Inc. is an American electric vehicle and clean energy 
          company founded by Martin Eberhard and Marc Tarpenning in 2003.
          Elon Musk joined as chairman in 2004..."

3. OLLAMA EXTRACTS FACTS
   ↓
   Facts:
   - Tesla FOUNDED_BY Martin Eberhard (confidence: 0.98)
   - Tesla FOUNDED_BY Marc Tarpenning (confidence: 0.98)
   - Elon Musk CHAIRMAN_OF Tesla (confidence: 0.95)
   - Tesla INDUSTRY "Electric Vehicles" (confidence: 0.92)

4. NEO4J STORES FACTS
   ↓
   Nodes: Tesla, Martin Eberhard, Marc Tarpenning, Elon Musk
   Edges: FOUNDED_BY, CHAIRMAN_OF, INDUSTRY
   Timestamps: valid_from: 2024-11-29T10:30:00Z

5. UI DISPLAYS GRAPH
   ↓
   You see a 3D graph with nodes for each entity and lines showing
   relationships. You can drag nodes around and see connections.

6. SELF-HEALING (Every 6 hours)
   ↓
   Sentinel re-scrapes the Wikipedia page
   Checks if facts are still true
   Updates last_verified timestamp
   If facts changed, updates the graph
```

---

## 🔄 Self-Healing Process

```
┌─────────────────────────────────────────────────────────────┐
│  SELF-HEALING CYCLE (Runs Every 6 Hours)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. FIND STALE DATA                                         │
│     Find facts not verified in > 7 days                     │
│     ↓                                                       │
│  2. RE-SCRAPE WEBSITES                                      │
│     Use Firecrawl to visit original URLs again              │
│     ↓                                                       │
│  3. RE-EXTRACT FACTS                                        │
│     Use Ollama to extract facts from new content            │
│     ↓                                                       │
│  4. COMPARE HASHES                                          │
│     SHA-256 hash of content                                 │
│     If hash matches: Just update last_verified             │
│     If hash differs: Content changed, update facts          │
│     ↓                                                       │
│  5. UPDATE GRAPH                                            │
│     Mark old facts as invalid (valid_to = now)             │
│     Add new facts with new timestamps                       │
│     ↓                                                       │
│  6. REPORT RESULTS                                          │
│     "Healed 15 stale URLs, found 3 changed facts"          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⏰ Temporal Validity (Time Travel)

Every fact in Sentinel has timestamps:

```
Fact: "Elon Musk is CEO of Tesla"

Timeline:
2008 ─────────────────────────────────────────────────────
     ↑ valid_from: 2008-06-03
     Elon Musk becomes CEO

2022 ─────────────────────────────────────────────────────
     ↑ valid_to: 2022-08-09
     Elon Musk steps down as CEO

2024 ─────────────────────────────────────────────────────
     ↑ last_verified: 2024-11-29
     Still marked as invalid

When you ask "Show me the graph in 2015":
→ Shows Elon Musk as CEO of Tesla (because valid_from < 2015 < valid_to)

When you ask "Show me the graph in 2023":
→ Does NOT show Elon Musk as CEO (because valid_to < 2023)
```

---

## 🚀 Key Features Explained

### 1. **Idempotent Ingestion**
- **Problem:** If you ingest the same URL twice, you get duplicate data
- **Solution:** Hash the content (SHA-256)
  - First time: Store the fact
  - Second time: Same hash → Skip (no duplicate)
  - Third time: Different content → Update the fact

### 2. **Temporal Validity**
- **Problem:** Facts change over time, but we want to remember history
- **Solution:** Store `valid_from` and `valid_to` timestamps
  - See the graph at any point in history
  - Know when facts became true/false

### 3. **Self-Healing**
- **Problem:** Websites change, facts become outdated
- **Solution:** Automatically re-check facts every 6 hours
  - Detect changes
  - Update the graph
  - Keep knowledge fresh

### 4. **Confidence Scoring**
- **Problem:** AI isn't always 100% sure about extracted facts
- **Solution:** Assign confidence scores (0-1)
  - 0.95 = Very confident
  - 0.70 = Somewhat confident
  - 0.50 = Uncertain

---

## 💾 Storage & Deduplication

```
Content Hashing Example:

Website 1: "Tesla was founded in 2003"
Hash: 3a7f9e2c1b4d8f6a9e2c1b4d8f6a9e2c

Website 2: "Tesla was founded in 2003"
Hash: 3a7f9e2c1b4d8f6a9e2c1b4d8f6a9e2c (SAME!)

Action: Don't store duplicate, just update last_verified

Website 3: "Tesla was founded in 2004"
Hash: 7f9e2c1b4d8f6a9e2c1b4d8f6a9e2c3a (DIFFERENT!)

Action: Mark old fact as invalid, store new fact
```

---

## 🎯 Use Cases

1. **Research & Knowledge Synthesis**
   - Automatically extract facts from multiple sources
   - See connections between entities
   - Time-travel to understand how knowledge evolved

2. **Competitive Intelligence**
   - Monitor company websites
   - Track leadership changes
   - Detect new partnerships or acquisitions

3. **Fact Checking**
   - Store facts with sources and timestamps
   - Verify if claims are still true
   - Track when facts changed

4. **Knowledge Management**
   - Build a company knowledge base
   - Connect related information
   - Keep it automatically updated

---

## 🔐 Security & Privacy

- **Local AI:** Ollama runs locally (no data sent to external AI services)
- **Open Source:** Code is transparent and auditable
- **Temporal Audit Trail:** Every change is timestamped and traceable
- **Source Tracking:** Every fact includes the source URL

---

## 📈 Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Scrape URL | 2-5 sec | Depends on page size |
| Extract Facts | 1-3 sec | Depends on text length |
| Store in Neo4j | <100ms | Very fast graph writes |
| Query Graph | <500ms | Even complex queries are fast |
| Time-Travel Query | <1 sec | Temporal filtering adds overhead |
| Self-Healing Cycle | ~5 min | For 100 URLs |

---

## 🎓 Learning Path

1. **Start Here:** Read this document
2. **Try the UI:** Run the system and explore the 3D graph
3. **Ask Questions:** Use the query interface
4. **Time Travel:** Drag the time slider to see history
5. **Dive Deeper:** Read the code in `sentinel_core/`
6. **Extend:** Build custom extractors or visualizations
