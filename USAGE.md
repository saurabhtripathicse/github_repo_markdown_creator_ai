# GitHub Documentation Generator - Usage Guide

This document provides detailed instructions for installing, configuring, and using the GitHub Documentation Generator.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Command-line Usage](#command-line-usage)
- [API Usage](#api-usage)
- [Web Search Integration](#web-search-integration)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before using the GitHub Documentation Generator, ensure you have the following:

- Python 3.8 or higher
- GitHub Personal Access Token (for higher API rate limits)
- OpenAI API Key (for documentation generation)
- Node.js (for diagram generation, optional)
- Internet connection (for GitHub API and web search functionality)

## Installation

### 1. Clone the Repository

```bash
git clone [https://github.com/yourusername/github-doc-scanner.git](https://github.com/yourusername/github-doc-scanner.git)
cd github-doc-scanner
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt

## For web search functionality (optional)

pip install duckduckgo-search beautifulsoup4
```

### 3. Install Node.js Dependencies (Optional, for Diagram Generation)

```bash
npm install -g @mermaid-js/mermaid-cli
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root directory with the following content:

```text

GITHUB_TOKEN=your_github_personal_access_token
OPENAI_API_KEY=your_openai_api_key
```

Alternatively, you can copy the example file and modify it:

```bash
cp .env.example .env

## Edit .env with your preferred text editor

```

## Configuration

The GitHub Documentation Generator can be configured through environment variables or command-line arguments.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | None |
| `OPENAI_API_KEY` | OpenAI API Key | None |
| `OUTPUT_DIR` | Directory for generated documentation | `docs/` |
| `WEB_SEARCH_ENABLED` | Enable web search integration | `false` |
| `MAX_SEARCH_RESULTS` | Maximum number of search results to process | `5` |

## Command-line Usage

The GitHub Documentation Generator can be used from the command line with various options.

### Basic Usage

Generate documentation for a GitHub repository:

```bash

## Generate documentation for a specific repository

python generate_docs.py [https://github.com/username/repository](https://github.com/username/repository)

## Generate documentation for the default demo repository

python generate_docs.py
```

### Options

```bash

## Generate documentation with a C4 architecture diagram

python generate_docs.py --diagram [https://github.com/username/repository](https://github.com/username/repository)

## Generate documentation with web search enabled

python generate_docs.py --web-search [https://github.com/username/repository](https://github.com/username/repository)

## Generate documentation without opening it automatically

python generate_docs.py --no-open [https://github.com/username/repository](https://github.com/username/repository)

## Perform only a web search with a specific query

python generate_docs.py --search-only "fastapi code examples" --max-results 10
```

### Quick Test Script

For convenience, you can use the quick test script:

```bash

## Generate documentation for the default demo repository (Prerequisites)

./quick_test.sh

## Generate documentation for a custom GitHub repository

./quick_test.sh [https://github.com/username/repository](https://github.com/username/repository)
```

## API Usage

The GitHub Documentation Generator provides a REST API for programmatic access.

### Starting the API Server

```bash
uvicorn src.main:app --reload
```

The server will be running at [http://localhost:8000](http://localhost:8000)

### API Endpoints

#### Generate Documentation

**Endpoint:** `POST /generate-docs`

**Request Body:**

```json
{
  "repo_url": "[https://github.com/owner/repo",](https://github.com/owner/repo",)
  "diagram": false,
  "web_search": true
}
```

**Parameters:**

- `repo_url`: URL of the GitHub repository to analyze
- `diagram`: (Optional) Whether to generate a C4 architecture diagram (default: false)
- `web_search`: (Optional) Whether to enable web search for additional code examples (default: false)

**Response:**

```json
{
  "ok": true,
  "files": [
    "/path/to/docs/owner_repo/OVERVIEW.md",
    "/path/to/docs/owner_repo/MODULES.md",
    "/path/to/docs/owner_repo/USAGE.md",
    "/path/to/docs/owner_repo/DEPENDENCIES.md"
  ],
  "message": "Successfully generated documentation for [https://github.com/owner/repo"](https://github.com/owner/repo")
}
```

#### Web Search and Scrape Code

**Endpoint:** `POST /web-search`

**Request Body:**

```json
{
  "query": "fastapi code examples",
  "max_results": 5
}
```

**Parameters:**

- `query`: Search query for finding code examples
- `max_results`: (Optional) Maximum number of search results to process (default: 5)

**Response:**

```json
{
  "ok": true,
  "content": "# Web Search Results for: fastapi code examples\n\n## [FastAPI - The Examples Book](https://the-examples-book.com/tools/fastapi)\n\n### Code Snippet 1\n\n```python\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get(\"/\")\nasync def root():\n    return {\"message\": \"Hello World\"}\n```\n\n...",
  "message": "Successfully searched for: fastapi code examples"
}
```text

### API Client Example

Here's an example of how to use the API with Python requests:

```python
import requests
import json

## Generate documentation

response = requests.post(
    "[http://localhost:8000/generate-docs",](http://localhost:8000/generate-docs",)
    json={
        "repo_url": "[https://github.com/openai/openai-agents-python",](https://github.com/openai/openai-agents-python",)
        "diagram": True,
        "web_search": True
    }
)

## Print the response

print(json.dumps(response.json(), indent=2))
```sql

## Web Search Integration

The web search integration enhances documentation by finding and incorporating relevant code examples from the internet.

### Enabling Web Search

Web search can be enabled in several ways:

1. **Command-line**: Use the `--web-search` flag
   ```bash
   python generate_docs.py --web-search [https://github.com/username/repository](https://github.com/username/repository)
   ```text

2. **API**: Set the `web_search` parameter to `true`
   ```json
   {
     "repo_url": "[https://github.com/owner/repo",](https://github.com/owner/repo",)
     "web_search": true
   }
   ```text

3. **Environment**: Set `WEB_SEARCH_ENABLED=true` in your `.env` file

### Customizing Search Queries

The system automatically generates search queries based on the repository metadata, but you can also perform custom searches:

```bash
python generate_docs.py --search-only "repository_name best practices" --max-results 10
```

## Advanced Configuration

### Customizing Documentation Output

You can customize the documentation output by modifying the templates in the source code:

1. Edit the prompt templates in `src/ai_generator.py`
2. Adjust the output format in `src/doc_writer.py`

### Rate Limiting Considerations

- Without authentication, GitHub API has a limit of 60 requests per hour
- With a GitHub token, the limit increases to 5,000 requests per hour
- To avoid rate limiting, add your GitHub token to the `.env` file

## Troubleshooting

### Common Issues

1. **GitHub API Rate Limiting**
   - **Symptom**: Error message about rate limits
   - **Solution**: Add a GitHub token to your `.env` file

2. **OpenAI API Authentication**
   - **Symptom**: Error about invalid API key
   - **Solution**: Check your OpenAI API key in the `.env` file

3. **Web Search Failures**
   - **Symptom**: No search results or errors during web search
   - **Solution**: Check your internet connection and try a different search query

### Getting Help

If you encounter issues not covered here, please:

1. Check the GitHub repository issues page
2. Consult the project documentation
3. Create a new issue with detailed information about your problem
