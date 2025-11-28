# 🛡️ Sentinel: The Self-Healing Knowledge Graph

## 🧐 What is this?
Imagine a **Wikipedia that reads itself and updates automatically**. That's Sentinel.

It is an intelligent system that:
1.  **Reads** websites (like news, wikis, or docs).
2.  **Understands** the connections between people, places, and things using AI.
3.  **Visualizes** these connections in a 3D network.
4.  **Keeps itself updated** by revisiting pages to check for new information.

## 🎮 How to Use It

### 1. The Dashboard (What you see)
-   **The 3D Graph**: This is your "Brain". Each dot (Node) is a person, company, or concept. The lines (Links) are how they are connected.
    -   *Left Click + Drag*: Rotate
    -   *Right Click + Drag*: Move
    -   *Scroll*: Zoom
-   **Time Slider (Bottom)**: Drag this to travel back in time! See what the AI knew yesterday vs. today.
-   **Sidebar (Right)**: Shows live statistics and what the AI is currently doing (scraping, updating).

### 2. Feeding the Brain
To teach Sentinel new things, you need to "feed" it URLs.
1.  Open the `seed_graph.py` file.
2.  Add a link (e.g., `https://en.wikipedia.org/wiki/SpaceX`).
3.  Run `python seed_graph.py`.
4.  Watch the graph grow!

## 💡 Why is this useful?
-   **For Researchers**: Instantly map out complex topics.
-   **For Analysts**: Track how relationships change over time (e.g., "Who is the CEO of X?").
-   **For Developers**: A foundation for building smarter AI apps that don't hallucinate.

## 🏗️ Under the Hood
-   **AI**: Llama 3.2 (running locally on your machine).
-   **Database**: Neo4j (Graph DB).
-   **Scraper**: Firecrawl.
-   **Frontend**: Next.js & Three.js.

---
*Built with ❤️ by the Sentinel Team*
