# GitHub Documentation Generator - Modules

This document provides a detailed description of each module in the GitHub Documentation Generator project, explaining their purpose, functionality, and relationships.

## Core Modules Overview

The GitHub Documentation Generator is organized into several specialized modules, each responsible for a specific aspect of the documentation generation process:

| Module | File | Purpose |
|--------|------|---------|
| API Layer | `main.py` | Provides FastAPI endpoints for interacting with the application |
| GitHub Fetcher | `github_fetcher.py` | Retrieves repository data from GitHub API |
| AI Generator | `ai_generator.py` | Generates documentation using OpenAI API |
| Document Writer | `doc_writer.py` | Writes generated documentation to files |
| Web Scraper | `web_scraper.py` | Searches the web for relevant code examples |
| Diagrammer | `diagrammer.py` | Generates C4 architecture diagrams |

## Module Details

### API Layer (`main.py`)

The API Layer serves as the entry point for the web service, providing HTTP endpoints for generating documentation and performing web searches.

**Key Components:**

- FastAPI application configuration
- API endpoint definitions
- Request/response models
- Error handling and logging

**Public Interfaces:**

- `GET /health` - Health check endpoint
- `POST /generate-docs` - Generate documentation for a GitHub repository
- `POST /web-search` - Search the web for code examples

**Dependencies:**

- GitHub Fetcher
- AI Generator
- Document Writer
- Web Scraper
- Diagrammer

### GitHub Fetcher (`github_fetcher.py`)

The GitHub Fetcher module is responsible for interacting with the GitHub API to retrieve repository data, including files, directories, README content, and metadata.

**Key Components:**

- GitHub API client
- URL parsing and validation
- Rate limit handling
- Repository data extraction

**Public Interfaces:**

- `GitHubFetcher` class
  - `parse_url(url)` - Parse GitHub repository URL
  - `fetch_repository(owner, repo)` - Fetch repository data
  - `fetch_readme(owner, repo)` - Fetch README content
  - `fetch_repository_info(owner, repo)` - Fetch basic repository information

**Dependencies:**

- GitHub API
- Requests library

### AI Generator (`ai_generator.py`)

The AI Generator module leverages OpenAI's API to generate documentation content based on the repository data.

**Key Components:**

- OpenAI API client
- Prompt engineering
- Content generation
- Documentation structuring

**Public Interfaces:**

- `AIGenerator` class
  - `generate_docs_content(repo_data)` - Generate documentation content
  - `generate_overview(repo_data)` - Generate repository overview
  - `generate_modules_doc(repo_data)` - Generate modules documentation
  - `generate_usage_doc(repo_data)` - Generate usage documentation
  - `generate_dependencies_doc(repo_data)` - Generate dependencies documentation

**Dependencies:**

- OpenAI API
- Repository data from GitHub Fetcher

### Document Writer (`doc_writer.py`)

The Document Writer module handles writing the generated documentation content to Markdown files.

**Key Components:**

- File system operations
- Markdown formatting
- Output directory management

**Public Interfaces:**

- `DocWriter` class
  - `write_docs(docs_content, repo_name)` - Write documentation to files
  - `write_diagram(diagram_content, repo_name)` - Write diagram to file

**Dependencies:**

- Documentation content from AI Generator
- File system

### Web Scraper (`web_scraper.py`)

The Web Scraper module searches the web for relevant code examples and documentation to enhance the generated documentation.

**Key Components:**

- Web search functionality
- HTML parsing
- Code snippet extraction
- Markdown formatting

**Public Interfaces:**

- `WebScraper` class
  - `search_and_scrape(query, max_results)` - Search the web and scrape code snippets
  - `_search_web(query, max_results)` - Search the web using DuckDuckGo
  - `_scrape_code_snippets(url)` - Scrape code snippets from a webpage

**Dependencies:**

- DuckDuckGo Search API
- BeautifulSoup for HTML parsing
- Requests library

### Diagrammer (`diagrammer.py`)

The Diagrammer module generates C4 architecture diagrams based on the repository structure.

**Key Components:**

- C4 model generation
- Mermaid diagram syntax
- SVG rendering

**Public Interfaces:**

- `Diagrammer` class
  - `generate_diagram(repo_data, output_dir)` - Generate C4 architecture diagram
  - `_analyze_structure(repo_data)` - Analyze repository structure
  - `_generate_c4_syntax(structure)` - Generate C4 model syntax

**Dependencies:**

- Repository data from GitHub Fetcher
- Mermaid CLI (Node.js)

## Command-line Interface (`generate_docs.py`)

While not a core module, the command-line interface provides a convenient way to use the GitHub Documentation Generator without interacting with the API directly.

**Key Components:**

- Argument parsing
- Server management
- Documentation generation workflow

**Public Interfaces:**

- Command-line arguments
  - Repository URL
  - Diagram generation flag
  - Web search flag
  - Search-only mode
  - No-open flag

**Dependencies:**

- All core modules
- Uvicorn for server management

## Module Relationships

The modules in the GitHub Documentation Generator work together in a pipeline:

1. **Input**: The process begins with either:
   - API request to `/generate-docs`
   - Command-line invocation of `generate_docs.py`

2. **Repository Data Acquisition**:
   - `GitHubFetcher` retrieves repository data from GitHub

3. **Documentation Generation**:
   - `AIGenerator` processes repository data
   - `WebScraper` enhances documentation with external examples (if enabled)
   - `Diagrammer` generates architecture diagram (if enabled)

4. **Output**:
   - `DocWriter` writes documentation files to the output directory
   - API returns file paths or content
   - Command-line interface optionally opens the documentation

## Extension Points

The modular architecture of the GitHub Documentation Generator allows for several extension points:

1. **New Documentation Types**:
   - Add new generation methods to `AIGenerator`
   - Add new writing methods to `DocWriter`

2. **Additional Data Sources**:
   - Extend `GitHubFetcher` to support other version control systems
   - Add new data acquisition modules

3. **Enhanced AI Capabilities**:
   - Modify prompt templates in `AIGenerator`
   - Integrate additional AI models

4. **Custom Diagrams**:
   - Extend `Diagrammer` to support additional diagram types
   - Implement alternative visualization approaches
