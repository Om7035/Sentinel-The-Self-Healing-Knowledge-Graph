"""
Sentinel CLI - Command-line interface for the Sentinel Knowledge Graph

This CLI provides an intuitive interface for:
- Setting up Sentinel (sentinel init)
- Processing URLs (sentinel watch)
- Querying knowledge (sentinel ask)
- Checking system status (sentinel status)
- Running healing cycles (sentinel heal)
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from dotenv import load_dotenv, set_key

# Note: We use lazy imports for sentinel_core components to avoid
# initialization issues at module load time

app = typer.Typer(
    name="sentinel",
    help="🛡️ Sentinel - Self-Healing Temporal Knowledge Graph",
    add_completion=False,
)
console = Console()


def check_docker_running() -> bool:
    """Check if Docker is running."""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_neo4j_connection(uri: str, user: str, password: str) -> bool:
    """Check if Neo4j is accessible."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        driver.close()
        return True
    except Exception:
        return False


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing .env file")
):
    """
    🚀 Interactive setup wizard for Sentinel.
    
    This command will:
    - Check Docker status
    - Collect API keys
    - Generate .env file
    - Verify connections
    """
    console.print(Panel.fit(
        "[bold cyan]🛡️ Sentinel Setup Wizard[/bold cyan]\n"
        "Let's get you started in less than 5 minutes!",
        border_style="cyan"
    ))
    
    env_file = Path(".env")
    
    # Check if .env exists
    if env_file.exists() and not force:
        console.print("\n[yellow]⚠️  .env file already exists![/yellow]")
        overwrite = typer.confirm("Do you want to overwrite it?")
        if not overwrite:
            console.print("[red]Setup cancelled.[/red]")
            raise typer.Exit(1)
    
    # Step 1: Check Docker
    console.print("\n[bold]Step 1: Checking Docker...[/bold]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Checking Docker status...", total=None)
        docker_running = check_docker_running()
        progress.update(task, completed=True)
    
    if docker_running:
        console.print("[green]✅ Docker is running[/green]")
    else:
        console.print("[yellow]⚠️  Docker is not running or not installed[/yellow]")
        console.print("   You'll need Docker for Neo4j. Install from: https://docker.com")
    
    # Step 2: Collect configuration
    console.print("\n[bold]Step 2: Configuration[/bold]")
    
    config = {}
    
    # Neo4j settings
    console.print("\n[cyan]Neo4j Configuration:[/cyan]")
    config["NEO4J_URI"] = typer.prompt(
        "Neo4j URI",
        default="bolt://localhost:7687"
    )
    config["NEO4J_USER"] = typer.prompt("Neo4j Username", default="neo4j")
    config["NEO4J_PASSWORD"] = typer.prompt("Neo4j Password", hide_input=True)
    
    # LLM settings
    console.print("\n[cyan]LLM Configuration:[/cyan]")
    console.print("Choose your LLM provider:")
    console.print("  1. Ollama (Local, Free)")
    console.print("  2. OpenAI (Cloud, Paid)")
    console.print("  3. Other (via LiteLLM)")
    
    llm_choice = typer.prompt("Enter choice", default="1")
    
    if llm_choice == "1":
        config["OLLAMA_MODEL"] = typer.prompt("Ollama Model", default="llama3")
        config["OLLAMA_BASE_URL"] = typer.prompt("Ollama URL", default="http://localhost:11434")
    elif llm_choice == "2":
        config["OPENAI_API_KEY"] = typer.prompt("OpenAI API Key", hide_input=True)
        config["OLLAMA_MODEL"] = "gpt-4"
    else:
        config["OLLAMA_MODEL"] = typer.prompt("LiteLLM Model Name (e.g., claude-3-opus)")
        config["LLM_API_KEY"] = typer.prompt("API Key", hide_input=True, default="")
    
    # Scraper settings
    console.print("\n[cyan]Scraper Configuration:[/cyan]")
    use_firecrawl = typer.confirm("Do you have a Firecrawl API key? (optional)", default=False)
    
    if use_firecrawl:
        config["FIRECRAWL_API_KEY"] = typer.prompt("Firecrawl API Key", hide_input=True)
    else:
        console.print("[dim]Using local scraper (free fallback)[/dim]")
    
    # Step 3: Write .env file
    console.print("\n[bold]Step 3: Writing configuration...[/bold]")
    
    with open(env_file, "w") as f:
        f.write("# Sentinel Configuration\n")
        f.write("# Generated by: sentinel init\n\n")
        
        f.write("# Neo4j Database\n")
        f.write(f"NEO4J_URI={config['NEO4J_URI']}\n")
        f.write(f"NEO4J_USER={config['NEO4J_USER']}\n")
        f.write(f"NEO4J_PASSWORD={config['NEO4J_PASSWORD']}\n\n")
        
        f.write("# LLM Configuration\n")
        f.write(f"OLLAMA_MODEL={config.get('OLLAMA_MODEL', 'llama3')}\n")
        if "OLLAMA_BASE_URL" in config:
            f.write(f"OLLAMA_BASE_URL={config['OLLAMA_BASE_URL']}\n")
        if "OPENAI_API_KEY" in config:
            f.write(f"OPENAI_API_KEY={config['OPENAI_API_KEY']}\n")
        if "LLM_API_KEY" in config:
            f.write(f"LLM_API_KEY={config['LLM_API_KEY']}\n")
        f.write("\n")
        
        if "FIRECRAWL_API_KEY" in config:
            f.write("# Scraper Configuration\n")
            f.write(f"FIRECRAWL_API_KEY={config['FIRECRAWL_API_KEY']}\n")
    
    console.print("[green]✅ Configuration saved to .env[/green]")
    
    # Step 4: Verify connections
    console.print("\n[bold]Step 4: Verifying connections...[/bold]")
    
    # Load the new .env
    load_dotenv(env_file, override=True)
    
    # Check Neo4j
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Testing Neo4j connection...", total=None)
        neo4j_ok = check_neo4j_connection(
            config["NEO4J_URI"],
            config["NEO4J_USER"],
            config["NEO4J_PASSWORD"]
        )
        progress.update(task, completed=True)
    
    if neo4j_ok:
        console.print("[green]✅ Neo4j connection successful[/green]")
    else:
        console.print("[red]❌ Could not connect to Neo4j[/red]")
        console.print("   Make sure Neo4j is running:")
        console.print("   docker run -p 7687:7687 -p 7474:7474 neo4j:latest")
    
    # Check scraper
    console.print("\n[cyan]Scraper Status:[/cyan]")
    from sentinel_core.scraper import print_scraper_status
    print_scraper_status()
    
    # Final message
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        "[bold green]🎉 Setup Complete![/bold green]\n\n"
        "Next steps:\n"
        "  1. Start Neo4j if not running\n"
        "  2. Try: [cyan]sentinel watch https://example.com[/cyan]\n"
        "  3. Try: [cyan]sentinel ask \"What is this about?\"[/cyan]\n\n"
        "For help: [cyan]sentinel --help[/cyan]",
        border_style="green"
    ))


@app.command()
def watch(
    url: str = typer.Argument(..., help="URL to process"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output")
):
    """
    👁️ Process a URL through the Sentinel pipeline.
    
    This will:
    - Scrape the URL
    - Extract knowledge using AI
    - Store it in the graph database
    """
    load_dotenv()
    
    console.print(Panel.fit(
        f"[bold cyan]Processing URL[/bold cyan]\n{url}",
        border_style="cyan"
    ))
    
    async def process():
        # Lazy imports
        from sentinel_core import GraphManager, GraphExtractor, Sentinel
        from sentinel_core.scraper import get_scraper
        
        try:
            # Initialize components
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Initializing Sentinel...", total=None)
                
                graph_manager = GraphManager()
                scraper = get_scraper()
                extractor = GraphExtractor(
                    model_name=os.getenv("OLLAMA_MODEL", "ollama/llama3")
                )
                sentinel = Sentinel(graph_manager, scraper, extractor)
                
                progress.update(task, completed=True)
            
            console.print(f"[dim]Using scraper: {scraper.get_name()}[/dim]")
            
            # Process URL
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Processing {url}...", total=None)
                result = await sentinel.process_url(url)
                progress.update(task, completed=True)
            
            # Display results
            if result["status"] == "success":
                console.print("\n[bold green]✅ Success![/bold green]")
                console.print(f"  Extracted [cyan]{result.get('extracted_nodes', 0)}[/cyan] nodes")
                console.print(f"  Extracted [cyan]{result.get('extracted_edges', 0)}[/cyan] edges")
                console.print(f"  Content hash: [dim]{result.get('hash', 'N/A')[:16]}...[/dim]")
            elif result["status"] == "unchanged_verified":
                console.print("\n[yellow]ℹ️  Content unchanged[/yellow]")
                console.print(f"  Verified [cyan]{result.get('edges_updated', 0)}[/cyan] existing edges")
            else:
                console.print(f"\n[red]❌ Error: {result.get('error', 'Unknown error')}[/red]")
            
            if verbose and "stats" in result:
                console.print(f"\n[dim]Stats: {result['stats']}[/dim]")
            
            graph_manager.close()
            
        except Exception as e:
            console.print(f"\n[red]❌ Error: {str(e)}[/red]")
            if verbose:
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
            raise typer.Exit(1)
    
    asyncio.run(process())


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask the knowledge graph"),
    timestamp: Optional[str] = typer.Option(None, "--time", "-t", help="ISO timestamp for time-travel query")
):
    """
    💬 Ask a question about the knowledge graph.
    
    Uses natural language to query the temporal knowledge graph.
    """
    load_dotenv()
    
    console.print(Panel.fit(
        f"[bold cyan]Question[/bold cyan]\n{question}",
        border_style="cyan"
    ))
    
    try:
        # This would integrate with the query engine
        # For now, we'll show a placeholder
        console.print("\n[yellow]⚠️  Query engine integration coming soon![/yellow]")
        console.print("[dim]This will use the QueryEngine from sentinel_platform/api/query_engine.py[/dim]")
        
        # TODO: Implement actual query
        # from sentinel_platform.api.query_engine import QueryEngine
        # graph_manager = GraphManager()
        # query_engine = QueryEngine(graph_manager)
        # result = query_engine.execute_query_with_path(question, timestamp)
        # console.print(f"\n[bold]Answer:[/bold] {result['answer']}")
        
    except Exception as e:
        console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """
    📊 Show Sentinel system status.
    
    Displays:
    - Database connection
    - Scraper availability
    - Graph statistics
    """
    load_dotenv()
    
    # Lazy imports
    from sentinel_core import GraphManager
    from sentinel_core.scraper import print_scraper_status
    
    console.print(Panel.fit(
        "[bold cyan]🛡️ Sentinel System Status[/bold cyan]",
        border_style="cyan"
    ))
    
    # Check Neo4j
    console.print("\n[bold]Database Connection:[/bold]")
    try:
        graph_manager = GraphManager()
        graph_manager.verify_connectivity()
        console.print("[green]✅ Neo4j connected[/green]")
        
        # Get stats
        snapshot = graph_manager.get_graph_snapshot()
        console.print(f"  Nodes: [cyan]{snapshot['metadata']['node_count']}[/cyan]")
        console.print(f"  Edges: [cyan]{snapshot['metadata']['link_count']}[/cyan]")
        
        graph_manager.close()
    except Exception as e:
        console.print(f"[red]❌ Neo4j connection failed: {str(e)}[/red]")
    
    # Check scraper
    console.print("\n[bold]Scraper Status:[/bold]")
    print_scraper_status()
    
    # Check LLM
    console.print("\n[bold]LLM Configuration:[/bold]")
    model = os.getenv("OLLAMA_MODEL", "Not configured")
    console.print(f"  Model: [cyan]{model}[/cyan]")
    
    if "ollama" in model.lower():
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        console.print(f"  Ollama URL: [cyan]{base_url}[/cyan]")


@app.command()
def heal(
    days: int = typer.Option(7, "--days", "-d", help="Threshold for stale nodes (days)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be healed without doing it")
):
    """
    🔧 Run a healing cycle to update stale knowledge.
    
    Finds nodes that haven't been verified recently and re-processes them.
    """
    load_dotenv()
    
    console.print(Panel.fit(
        f"[bold cyan]Healing Cycle[/bold cyan]\n"
        f"Threshold: {days} days",
        border_style="cyan"
    ))
    
    async def run_heal():
        # Lazy imports
        from sentinel_core import GraphManager, GraphExtractor, Sentinel
        from sentinel_core.scraper import get_scraper
        
        try:
            # Initialize
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Initializing...", total=None)
                
                graph_manager = GraphManager()
                scraper = get_scraper()
                extractor = GraphExtractor(
                    model_name=os.getenv("OLLAMA_MODEL", "ollama/llama3")
                )
                sentinel = Sentinel(graph_manager, scraper, extractor)
                
                progress.update(task, completed=True)
            
            # Find stale nodes
            console.print("\n[bold]Finding stale nodes...[/bold]")
            stale_urls = graph_manager.find_stale_nodes(days_threshold=days)
            
            if not stale_urls:
                console.print("[green]✅ No stale nodes found! Graph is healthy.[/green]")
                graph_manager.close()
                return
            
            console.print(f"[yellow]Found {len(stale_urls)} stale URLs[/yellow]")
            
            if dry_run:
                console.print("\n[bold]Stale URLs (dry run):[/bold]")
                for url in stale_urls[:10]:  # Show first 10
                    console.print(f"  • {url}")
                if len(stale_urls) > 10:
                    console.print(f"  ... and {len(stale_urls) - 10} more")
                graph_manager.close()
                return
            
            # Run healing
            console.print("\n[bold]Running healing cycle...[/bold]")
            result = await sentinel.run_healing_cycle(days_threshold=days)
            
            console.print(f"\n[green]✅ Healing complete![/green]")
            console.print(f"  Processed: [cyan]{result['processed_count']}[/cyan] URLs")
            console.print(f"  Duration: [cyan]{result['duration_seconds']:.1f}s[/cyan]")
            
            graph_manager.close()
            
        except Exception as e:
            console.print(f"\n[red]❌ Error: {str(e)}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(run_heal())


@app.command()
def version():
    """Show Sentinel version."""
    console.print("[cyan]Sentinel v0.1.0[/cyan]")
    console.print("[dim]Self-Healing Temporal Knowledge Graph[/dim]")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
