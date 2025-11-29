'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import dynamic from 'next/dynamic';

// Dynamically import ForceGraph3D to avoid SSR issues
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), {
  ssr: false,
});

interface Node {
  id: string;
  name: string;
  val: number;
  x?: number;
  y?: number;
  z?: number;
  fx?: number | null;
  fy?: number | null;
  fz?: number | null;
}

interface Link {
  source: string;
  target: string;
  relation: string;
  confidence: number;
  source_url: string;
}

interface GraphData {
  nodes: Node[];
  links: Link[];
  metadata: {
    timestamp: string;
    node_count: number;
    link_count: number;
  };
}

export default function Home() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timestamp, setTimestamp] = useState<Date>(new Date());
  const [minDate, setMinDate] = useState<Date>(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
  const [maxDate] = useState<Date>(new Date());
  const [status, setStatus] = useState<{ state: string; message: string; last_update: string } | null>(null);
  const [urlInput, setUrlInput] = useState<string>('');
  const [isIngesting, setIsIngesting] = useState<boolean>(false);
  const [ingestError, setIngestError] = useState<string | null>(null);
  const [queryInput, setQueryInput] = useState<string>('');
  const [queryAnswer, setQueryAnswer] = useState<string | null>(null);
  const [highlightedPath, setHighlightedPath] = useState<string[]>([]);
  const [isQuerying, setIsQuerying] = useState<boolean>(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const fgRef = useRef<any>();

  // Fetch graph data
  const fetchGraphData = async (date: Date) => {
    setLoading(true);
    setError(null);

    try {
      const timestampParam = date.toISOString();
      const response = await fetch(
        `http://localhost:8000/api/graph-snapshot?timestamp=${timestampParam}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: GraphData = await response.json();
      setGraphData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch graph data');
      console.error('Error fetching graph data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch system status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/status');
        if (response.ok) {
          const data = await response.json();
          setStatus(data);
          // If active, refresh graph data occasionally
          if (data.state !== 'Idle' && data.state !== 'Error') {
            fetchGraphData(timestamp);
          }
        }
      } catch (err) {
        console.error('Failed to fetch status:', err);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 2000); // Poll every 2 seconds
    return () => clearInterval(interval);
  }, [timestamp]);

  // Initial load
  useEffect(() => {
    fetchGraphData(timestamp);
  }, []);

  // Handle timestamp change
  const handleTimestampChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = new Date(parseInt(e.target.value));
    setTimestamp(newDate);
    fetchGraphData(newDate);
  };

  // Handle URL submission for ingestion
  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setIsIngesting(true);
    setIngestError(null);

    try {
      const response = await fetch('http://localhost:8000/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: urlInput.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to ingest URL');
      }

      const data = await response.json();
      alert(`✅ Success! Extracted ${data.triples_count} facts from ${urlInput}`);
      setUrlInput('');

      // Refresh graph data
      fetchGraphData(timestamp);
    } catch (err) {
      setIngestError(err instanceof Error ? err.message : 'Failed to ingest URL');
      console.error('Error ingesting URL:', err);
    } finally {
      setIsIngesting(false);
    }
  };

  // Handle natural language query (Phase 5)
  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryInput.trim()) return;

    setIsQuerying(true);
    setQueryAnswer(null);
    setHighlightedPath([]);

    try {
      const response = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: queryInput.trim(),
          timestamp: timestamp.toISOString()
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to execute query');
      }

      const data = await response.json();
      setQueryAnswer(data.answer);
      setHighlightedPath(data.path || []);

      // Focus on the path in the graph
      if (fgRef.current && data.path && data.path.length > 0 && graphData) {
        const firstNode = graphData.nodes.find((n: any) => n.id === data.path[0]);
        if (firstNode && (firstNode as any).x !== undefined) {
          fgRef.current.cameraPosition(
            { x: (firstNode as any).x, y: (firstNode as any).y, z: (firstNode as any).z + 200 },
            firstNode,
            1000
          );
        }
      }
    } catch (err) {
      setQueryAnswer(err instanceof Error ? `Error: ${err.message}` : 'Failed to execute query');
      console.error('Error executing query:', err);
    } finally {
      setIsQuerying(false);
    }
  };

  // Format date for display
  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Memoize neighbors for efficient lookup
  const neighbors = useMemo(() => {
    if (!graphData) return new Map();
    const map = new Map();
    graphData.links.forEach((link: any) => {
      const sourceId = link.source.id || link.source;
      const targetId = link.target.id || link.target;

      if (!map.has(sourceId)) map.set(sourceId, []);
      if (!map.has(targetId)) map.set(targetId, []);

      map.get(sourceId).push(targetId);
      map.get(targetId).push(sourceId);
    });
    return map;
  }, [graphData]);

  // Track drag state
  const dragOffsets = useRef<Map<string, { x: number, y: number, z: number }>>(new Map());

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 overflow-hidden">
      {/* Header */}
      <header className="flex-none bg-black/30 backdrop-blur-md border-b border-purple-500/30 z-30 relative">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600">
                🛡️ Sentinel Knowledge Graph
              </h1>
              <p className="text-purple-200 mt-1">
                Self-Healing Temporal Knowledge Graph Visualization
              </p>
            </div>

            {/* URL Input Form */}
            <form onSubmit={handleUrlSubmit} className="flex gap-2">
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="Enter URL to analyze (e.g., stripe.com/pricing)"
                className="px-4 py-2 w-96 bg-slate-800/50 border border-purple-500/30 rounded-lg text-purple-100 placeholder-purple-300/50 focus:outline-none focus:border-purple-500"
                disabled={isIngesting}
              />
              <button
                type="submit"
                disabled={isIngesting || !urlInput.trim()}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {isIngesting ? '⏳ Analyzing...' : '🔍 Analyze'}
              </button>
            </form>
          </div>

          {/* Error Display */}
          {ingestError && (
            <div className="mt-3 p-3 bg-red-900/30 border border-red-500/30 rounded-lg text-red-200 text-sm">
              ❌ {ingestError}
            </div>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 relative overflow-hidden">
        {/* Main Graph Visualization - Full Screen */}
        <div className="absolute inset-0 bg-black/20 z-0">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm z-10">
              <div className="text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500 mx-auto"></div>
                <p className="text-purple-300 mt-4">Loading graph...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm z-10">
              <div className="bg-red-900/50 border border-red-500 rounded-lg p-6 max-w-md">
                <h3 className="text-red-300 font-bold text-lg mb-2">Error</h3>
                <p className="text-red-200">{error}</p>
                <button
                  onClick={() => fetchGraphData(timestamp)}
                  className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {graphData && !loading && (
            <ForceGraph3D
              ref={fgRef}
              graphData={graphData}
              nodeLabel="name"
              nodeAutoColorBy="id"
              nodeVal={(node: any) => node.val * 3}
              linkLabel={(link: any) => link.relation}
              linkWidth={(link: any) => highlightedPath.includes(link.source.id || link.source) && highlightedPath.includes(link.target.id || link.target) ? 4 : 2}
              linkColor={(link: any) => highlightedPath.includes(link.source.id || link.source) && highlightedPath.includes(link.target.id || link.target) ? '#ff00ff' : 'rgba(255,255,255,0.2)'}
              linkDirectionalArrowLength={3.5}
              linkDirectionalArrowRelPos={1}
              linkCurvature={0.25}
              linkDirectionalParticles={2}
              linkDirectionalParticleSpeed={0.005}
              backgroundColor="rgba(0,0,0,0)"
              nodeResolution={16}
              nodeOpacity={0.9}
              enableNodeDrag={true}
              onNodeDrag={(node: any) => {
                // Cluster Dragging Logic
                // 1. If this is the first drag frame (offsets empty), calculate offsets
                if (dragOffsets.current.size === 0) {
                  const neighborIds = neighbors.get(node.id) || [];
                  neighborIds.forEach((neighborId: string) => {
                    const neighbor = graphData.nodes.find((n: any) => n.id === neighborId);
                    if (neighbor) {
                      dragOffsets.current.set(neighborId, {
                        x: neighbor.x - node.x,
                        y: neighbor.y - node.y,
                        z: neighbor.z - node.z
                      });
                    }
                  });
                }

                // 2. Update neighbor positions based on dragged node position + offset
                dragOffsets.current.forEach((offset, neighborId) => {
                  const neighbor = graphData.nodes.find((n: any) => n.id === neighborId);
                  if (neighbor) {
                    neighbor.fx = node.x + offset.x;
                    neighbor.fy = node.y + offset.y;
                    neighbor.fz = node.z + offset.z;
                  }
                });
              }}
              onNodeDragEnd={(node: any) => {
                // 1. Release the dragged node
                node.fx = null;
                node.fy = null;
                node.fz = null;

                // 2. Release all neighbors
                dragOffsets.current.forEach((_, neighborId) => {
                  const neighbor = graphData.nodes.find((n: any) => n.id === neighborId);
                  if (neighbor) {
                    neighbor.fx = null;
                    neighbor.fy = null;
                    neighbor.fz = null;
                  }
                });

                // 3. Clear offsets
                dragOffsets.current.clear();
              }}
              warmupTicks={100}
              cooldownTicks={100}
              onNodeClick={(node: any) => {
                if (fgRef.current) {
                  fgRef.current.cameraPosition(
                    { x: node.x, y: node.y, z: node.z + 200 },
                    node,
                    1000
                  );
                }
              }}
            />
          )}
        </div>

        {/* Controls */}
        <div className="absolute top-4 right-4 z-30 flex gap-2">
          <button
            onClick={() => {
              if (fgRef.current) {
                fgRef.current.cameraPosition({ x: 0, y: 0, z: 500 }, { x: 0, y: 0, z: 0 }, 1000);
              }
            }}
            className="p-2 bg-slate-800/80 text-purple-300 rounded-lg border border-purple-500/30 hover:bg-slate-700 transition-all"
            title="Reset View"
          >
            🔄 Reset
          </button>
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 bg-slate-800/80 text-purple-300 rounded-lg border border-purple-500/30 hover:bg-slate-700 transition-all"
          >
            {isSidebarOpen ? '👉 Hide Sidebar' : '👈 Show Sidebar'}
          </button>
        </div>

        {/* Floating Sidebar */}
        <div
          className={`absolute top-0 right-0 bottom-0 w-96 bg-black/60 backdrop-blur-xl border-l border-purple-500/30 p-6 overflow-y-auto z-20 transition-transform duration-300 ease-in-out ${isSidebarOpen ? 'translate-x-0' : 'translate-x-full'
            }`}
        >
          {/* Query Interface (Phase 5) */}
          <div className="bg-slate-900/80 rounded-xl p-4 border border-purple-500/30 shadow-lg shadow-purple-900/20 mb-6">
            <h2 className="text-lg font-bold text-purple-300 mb-3 flex items-center gap-2">
              <span>💬</span> Ask Sentinel
            </h2>
            <form onSubmit={handleQuery} className="flex flex-col gap-3">
              <input
                type="text"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                placeholder="e.g., Who founded SpaceX?"
                className="px-3 py-2 bg-slate-800/50 border border-purple-500/30 rounded-lg text-purple-100 placeholder-purple-300/30 focus:outline-none focus:border-purple-500 text-sm"
                disabled={isQuerying}
              />
              <button
                type="submit"
                disabled={isQuerying || !queryInput.trim()}
                className="px-4 py-2 bg-purple-600/80 hover:bg-purple-600 text-white text-sm font-semibold rounded-lg transition-all disabled:opacity-50"
              >
                {isQuerying ? 'Thinking...' : 'Ask Question'}
              </button>
            </form>

            {queryAnswer && (
              <div className="mt-4 p-3 bg-purple-900/20 border border-purple-500/20 rounded-lg">
                <p className="text-purple-100 text-sm leading-relaxed">{queryAnswer}</p>
              </div>
            )}
          </div>

          {/* Live Status Panel */}
          <div className="mb-8">
            <h2 className="text-xl font-bold text-purple-300 mb-4 flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${status?.state === 'Idle' ? 'bg-green-400' : 'bg-yellow-400'}`}></span>
                <span className={`relative inline-flex rounded-full h-3 w-3 ${status?.state === 'Idle' ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
              </span>
              System Status
            </h2>
            <div className={`rounded-lg p-4 border ${status?.state === 'Error' ? 'bg-red-900/30 border-red-500/30' : 'bg-slate-800/50 border-purple-500/30'}`}>
              <div className="text-sm font-bold text-white mb-1">
                {status?.state || 'Connecting...'}
              </div>
              <div className="text-xs text-purple-200">
                {status?.message || 'Establishing connection to Sentinel core...'}
              </div>
            </div>
          </div>

          <h2 className="text-xl font-bold text-purple-300 mb-4">
            📊 Graph Statistics
          </h2>

          {graphData && (
            <div className="space-y-4">
              <div className="bg-purple-900/30 rounded-lg p-4 border border-purple-500/30">
                <div className="text-purple-200 text-sm">Nodes (Entities)</div>
                <div className="text-3xl font-bold text-purple-400">
                  {graphData.metadata.node_count}
                </div>
              </div>

              <div className="bg-pink-900/30 rounded-lg p-4 border border-pink-500/30">
                <div className="text-pink-200 text-sm">Links (Facts)</div>
                <div className="text-3xl font-bold text-pink-400">
                  {graphData.metadata.link_count}
                </div>
              </div>

              <div className="bg-blue-900/30 rounded-lg p-4 border border-blue-500/30">
                <div className="text-blue-200 text-sm">Timestamp</div>
                <div className="text-sm font-mono text-blue-400" suppressHydrationWarning>
                  {formatDate(timestamp)}
                </div>
              </div>
            </div>
          )}

          <div className="mt-8">
            <h3 className="text-lg font-bold text-purple-300 mb-3">
              🧠 About This Graph
            </h3>
            <div className="text-sm text-purple-200 space-y-3 bg-slate-900/40 p-4 rounded-lg border border-purple-500/20">
              <p>
                <strong className="text-purple-400">What is this?</strong><br />
                This is a visual map of knowledge extracted by AI.
              </p>
              <p>
                <strong className="text-purple-400">Nodes (Dots)</strong><br />
                Represent people, companies, places, or concepts found in the text.
              </p>
              <p>
                <strong className="text-purple-400">Links (Lines)</strong><br />
                Represent facts connecting them (e.g., "Elon Musk" —FOUNDED→ "SpaceX").
              </p>
              <p className="text-xs italic opacity-70">
                Drag to rotate. Scroll to zoom. Use the slider below to time-travel.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Time Slider (Footer) */}
      <div className="flex-none bg-black/50 backdrop-blur-md border-t border-purple-500/30 p-4 z-30 relative">
        <div className="container mx-auto">
          <div className="flex items-center gap-4">
            <div className="text-purple-300 text-sm font-mono whitespace-nowrap" suppressHydrationWarning>
              {formatDate(minDate)}
            </div>
            <input
              type="range"
              min={minDate.getTime()}
              max={maxDate.getTime()}
              value={timestamp.getTime()}
              onChange={handleTimestampChange}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
            />
            <div className="text-purple-300 text-sm font-mono whitespace-nowrap" suppressHydrationWarning>
              {formatDate(maxDate)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
