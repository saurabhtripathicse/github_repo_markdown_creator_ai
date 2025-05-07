# GitHub Documentation Generator

A FastAPI application that automatically analyzes GitHub repositories and generates comprehensive documentation in Markdown format.

## Features

- Analyze public GitHub repositories via URL
- Generate multiple detailed Markdown documentation files:
  - OVERVIEW.md - Concise repository overview
  - MODULES.md - Documentation of modules and public interfaces
  - USAGE.md - Usage examples derived from tests and README
  - DEPENDENCIES.md - List of dependencies with explanations
- **NEW: Web search integration for enhanced documentation**
  - Search for additional code examples and context
  - Extract code snippets from web pages
  - Integrate web search results into generated documentation
- **NEW: GPT-4o model integration for superior documentation quality**
  - Higher quality, more detailed documentation
  - Longer, more comprehensive code examples (10-30 lines)
  - Better structured content with consistent markdown headers
  - Improved handling of missing information with [Assumed] tags
- **IMPROVED: Refined prompt templates for better documentation**
  - Structured, non-redundant, and actionable documentation
  - Developer-focused content with clear import paths and examples
  - Tabular format for structured data like dependencies
  - Enhanced error handling and common pitfalls sections
- **NEW: Enhanced code example extraction**
  - Smarter detection of example directories and files
  - Extraction of examples from subdirectories and notebooks
  - Support for more file types (.py, .js, .ts, .jsx, .tsx, .md, .ipynb)
  - Source file citation for all code examples
  - Prioritization of real repository examples over generated ones
- Optional C4 architecture diagram generation
- REST API for easy integration
- Command-line interface for quick documentation generation

## Getting Started

### Prerequisites

- Python 3.8+
- GitHub Personal Access Token (for higher API rate limits)
- OpenAI API Key (for documentation generation)
- Node.js (for diagram generation)

### Installation

1. Clone the repository

```bash
git clone [https://github.com/yourusername/github-doc-scanner.git](https://github.com/yourusername/github-doc-scanner.git)
cd github-doc-scanner
```

1. Install dependencies

```bash
pip install -r requirements.txt
pip install duckduckgo-search beautifulsoup4  # For web search functionality
npm install -g @mermaid-js/mermaid-cli  # For diagram generation
```

1. Set up environment variables

```bash
cp .env.example .env

# Edit .env with your GitHub token and OpenAI API key

```

## Usage

### Command-line Interface

The easiest way to generate documentation is using the command-line script:

```bash

## Generate documentation for the default demo repository (OpenAI Agents Python)

python generate_docs.py

## Generate documentation for a custom GitHub repository

python generate_docs.py [https://github.com/username/repository](https://github.com/username/repository)

## Generate documentation with a C4 architecture diagram

python generate_docs.py --diagram [https://github.com/username/repository](https://github.com/username/repository)

## Generate documentation with web search enabled

python generate_docs.py --web-search [https://github.com/username/repository](https://github.com/username/repository)

## Generate documentation without opening it automatically

python generate_docs.py --no-open [https://github.com/username/repository](https://github.com/username/repository)
```

### Quick Test Script

You can also use the quick test script:

```bash

## Generate documentation for the default demo repository

./quick_test.sh

## Generate documentation for a custom GitHub repository (Getting Started)

./quick_test.sh [https://github.com/username/repository](https://github.com/username/repository)
```

### Starting the FastAPI Server

To start the FastAPI server manually:

```bash
uvicorn src.main:app --reload
```

The server will be running at [http://localhost:8000](http://localhost:8000)

### API Usage

#### Generate Documentation

**Endpoint:** `POST /generate-docs`

**Request:**

```json
{
  "repo_url": "[https://github.com/username/repository",](https://github.com/username/repository",)
  "diagram": false,
  "web_search": true
}
```

**Response:**

```json
{
  "ok": true,
  "files": [
    "docs/docs_username_repository/OVERVIEW.md",
    "docs/docs_username_repository/MODULES.md",
    "docs/docs_username_repository/USAGE.md",
    "docs/docs_username_repository/DEPENDENCIES.md"
  ],
  "message": "Documentation generated successfully"
}
```

#### Web Search

**Endpoint:** `POST /web-search`

**Request:**

```json
{
  "query": "fastapi code examples",
  "max_results": 5
}
```

**Response:**

```json
{
  "ok": true,
  "content": "# Web Search Results for: fastapi code examples\n\n...",
  "message": "Successfully searched for: fastapi code examples"
}
```

## Documentation Quality

The documentation generator uses carefully crafted prompt templates and OpenAI's GPT-4o model to produce high-quality documentation:

### Documentation Principles

1. **Structured Documentation**:
   - Clear sections with ### markdown headers
   - Consistent formatting across all files
   - Logical organization of information

2. **Developer-Focused Content**:
   - Emphasis on practical usage patterns
   - Clear import paths and configuration options
   - Comprehensive code examples (10-30 lines)

3. **Non-Redundant Information**:
   - Avoiding repetition of setup code
   - Referencing related information across files
   - Focusing on unique aspects of each section

4. **Actionable Guidance**:
   - Concrete examples for common tasks
   - Error handling and troubleshooting
   - Configuration and customization options

5. **Clarity and Precision**:
   - Direct, factual language
   - Using [Assumed] tags for inferred information
   - Clear indication of missing information

For more details on the prompt templates and documentation structure, see [PROJECT_DOCS.md](PROJECT_DOCS.md).

## Project Structure

```bash
github-doc-scanner/
├── docs/                    # Generated documentation output
├── src/                     # Source code
│   ├── main.py              # FastAPI application
│   ├── github_fetcher.py    # GitHub API interaction
│   ├── ai_generator.py      # AI-powered documentation generation
│   ├── doc_writer.py        # Documentation writer
│   ├── diagrammer.py        # C4 diagram generation
│   └── web_scraper.py       # Web search and scraping functionality
├── tests/                   # Test files
├── .env.example             # Example environment variables
├── requirements.txt         # Python dependencies
├── generate_docs.py         # CLI script for documentation generation
└── quick_test.sh            # Quick test script
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| GITHUB_TOKEN | GitHub Personal Access Token | Yes |
| OPENAI_API_KEY | OpenAI API Key | Yes |
| HOST | Host for the FastAPI server | No (default: 127.0.0.1) |
| PORT | Port for the FastAPI server | No (default: 8000) |

## Recent Improvements

The documentation generator has been significantly enhanced with:

1. **Model Upgrade**:
   - Upgraded from GPT-3.5-turbo-16k to GPT-4o for higher quality documentation
   - Increased max_tokens from 2000 to 3000 for more comprehensive output

2. **Prompt Refinements**:
   - Completely rewritten system prompts for all documentation types
   - Added specific section structure with markdown headers
   - Included guidance for code snippet length and formatting
   - Added instructions for handling missing information with [Assumed] tags

3. **Output Quality**:
   - More detailed and comprehensive documentation
   - Better formatted with consistent markdown structure
   - More useful code examples with complete context
   - Improved tabular presentation of structured data

## Contributing

Contributions are welcome! Areas for improvement include:

1. **Prompt Engineering**:
   - Refining prompt templates for better output
   - Creating specialized prompts for different repository types

2. **Code Analysis**:
   - Improving extraction of code structure and dependencies
   - Better identification of public interfaces

3. **Web Search Integration**:
   - Enhancing relevance of search queries
   - Improving extraction of code snippets from web pages

4. **Output Formatting**:
   - Adding support for additional output formats (PDF, HTML)
   - Improving formatting and styling of documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.
