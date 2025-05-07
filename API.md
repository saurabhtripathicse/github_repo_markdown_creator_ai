# GitHub Documentation Generator - API Reference

This document provides detailed information about the REST API endpoints available in the GitHub Documentation Generator.

## Base URL

When running locally, the base URL for all API endpoints is:

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. However, you will need to provide your GitHub token and OpenAI API key in the server's environment variables for the service to function properly.

## API Endpoints

### Health Check

Check if the API server is running properly.

**Endpoint:** `GET /health`

**Request:** No parameters required

**Response:**
```json
{
  "ok": true
}
```

**Status Codes:**
- `200 OK` - Server is running properly

### Generate Documentation

Generate documentation for a GitHub repository.

**Endpoint:** `POST /generate-docs`

**Request Body:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "diagram": false,
  "web_search": true
}
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `repo_url` | string | Yes | - | URL of the GitHub repository to analyze |
| `diagram` | boolean | No | `false` | Whether to generate a C4 architecture diagram |
| `web_search` | boolean | No | `false` | Whether to enable web search for additional code examples |

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
  "message": "Successfully generated documentation for https://github.com/owner/repo"
}
```

**Status Codes:**
- `200 OK` - Documentation generated successfully
- `400 Bad Request` - Invalid GitHub URL
- `500 Internal Server Error` - Error during documentation generation

**Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/generate-docs",
    json={
        "repo_url": "https://github.com/openai/openai-agents-python",
        "diagram": True,
        "web_search": True
    }
)

print(response.json())
```

### Web Search

Search the web for code examples related to a query.

**Endpoint:** `POST /web-search`

**Request Body:**
```json
{
  "query": "fastapi code examples",
  "max_results": 5
}
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query for finding code examples |
| `max_results` | integer | No | `5` | Maximum number of search results to process |

**Response:**
```json
{
  "ok": true,
  "content": "# Web Search Results for: fastapi code examples\n\n## [FastAPI - The Examples Book](https://the-examples-book.com/tools/fastapi)\n\n### Code Snippet 1\n\n```python\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get(\"/\")\nasync def root():\n    return {\"message\": \"Hello World\"}\n```\n\n...",
  "message": "Successfully searched for: fastapi code examples"
}
```

**Status Codes:**
- `200 OK` - Web search completed successfully
- `500 Internal Server Error` - Error during web search

**Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/web-search",
    json={
        "query": "fastapi code examples",
        "max_results": 10
    }
)

print(response.json())
```

## Error Handling

The API returns standard HTTP status codes to indicate the success or failure of a request.

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

- `400 Bad Request` - The request was invalid or cannot be served
- `404 Not Found` - The requested resource does not exist
- `500 Internal Server Error` - An error occurred on the server

## Rate Limiting

The API itself does not implement rate limiting. However, the underlying GitHub API and OpenAI API have their own rate limits:

- GitHub API: 60 requests per hour (unauthenticated) or 5,000 requests per hour (with token)
- OpenAI API: Varies based on your OpenAI account tier

## API Models

### GenerateDocsRequest

```python
class GenerateDocsRequest(BaseModel):
    repo_url: str
    diagram: bool = False
    web_search: bool = False
```

### GenerateDocsResponse

```python
class GenerateDocsResponse(BaseModel):
    ok: bool
    files: List[str] = []
    message: str
```

### WebSearchRequest

```python
class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 5
```

### WebSearchResponse

```python
class WebSearchResponse(BaseModel):
    ok: bool
    content: str
    message: str
```

## Webhook Support

Currently, the API does not support webhooks. Future versions may include webhook functionality for asynchronous documentation generation.

## API Versioning

The current API does not implement versioning. All endpoints are considered v1 by default.

## CORS Support

The API includes CORS middleware that allows requests from any origin. This can be customized in the `main.py` file if needed.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## API Extension

To add new endpoints to the API, modify the `main.py` file and add new route handlers. The API follows the FastAPI pattern for defining routes and request/response models.
