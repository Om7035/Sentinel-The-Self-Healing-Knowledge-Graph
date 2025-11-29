from sentinel_core.graph_store import GraphManager
from sentinel_core.models import GraphData, GraphNode, TemporalEdge
from datetime import datetime
import traceback

def test_debug():
    try:
        graph = GraphManager()
        graph.clear_database()
        
        # Create test data
        node1 = GraphNode(id="n1", label="Entity", properties={"name": "N1"})
        node2 = GraphNode(id="n2", label="Entity", properties={"name": "N2"})
        edge = TemporalEdge(source="n1", relation="REL", target="n2", properties={"p": "v"}, valid_from=datetime.utcnow())
        data = GraphData(nodes=[node1, node2], edges=[edge])
        
        print("Upserting...")
        stats = graph.upsert_data(data)
        print(f"Stats: {stats}")
        
        print("Snapshot...")
        history = graph.get_graph_snapshot(datetime.utcnow())
        print(f"History: {history}")
        
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    test_debug()
