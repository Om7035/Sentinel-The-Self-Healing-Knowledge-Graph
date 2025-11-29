# Contributing to Sentinel

Thank you for your interest in contributing to Sentinel! We welcome contributions from the community to help make this the best self-healing knowledge graph system.

## 🚀 Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/Sentinel-The-Self-Healing-Knowledge-Graph.git
    cd Sentinel-The-Self-Healing-Knowledge-Graph
    ```
3.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
4.  **Install dependencies** in editable mode:
    ```bash
    pip install -e ".[all]"
    ```
5.  **Set up pre-commit hooks** (optional but recommended):
    ```bash
    pip install pre-commit
    pre-commit install
    ```

## 🛠️ Development Workflow

1.  **Create a branch** for your feature or fix:
    ```bash
    git checkout -b feature/amazing-feature
    ```
2.  **Make your changes**. Please follow the coding style (we use `black` and `isort`).
3.  **Run tests** to ensure nothing is broken:
    ```bash
    pytest tests/
    ```
4.  **Commit your changes** with a descriptive message:
    ```bash
    git commit -m "feat: add amazing feature"
    ```
5.  **Push to your fork**:
    ```bash
    git push origin feature/amazing-feature
    ```
6.  **Open a Pull Request** against the `main` branch of the original repository.

## 🧪 Testing

We use `pytest` for testing. Please ensure all tests pass before submitting a PR.

-   **Run all tests**: `pytest`
-   **Run specific test**: `pytest tests/test_core.py`
-   **Run integration tests**: `pytest tests/test_phase_5_integration.py` (Requires Neo4j and Ollama)

## 📝 Coding Standards

-   **Python Version**: 3.11+
-   **Style**: We follow PEP 8. Use `black` for formatting.
-   **Type Hinting**: Please use type hints for all function arguments and return values.
-   **Documentation**: Add docstrings to all modules, classes, and functions.

## 🐛 Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub. Include:
-   A clear title and description.
-   Steps to reproduce the issue.
-   Expected vs. actual behavior.
-   Your environment details (OS, Python version, etc.).

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.
