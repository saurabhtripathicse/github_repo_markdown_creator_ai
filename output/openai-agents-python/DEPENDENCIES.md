# Dependencies

# Dependencies

This document outlines the dependencies required for the `openai/openai-agents-python` repository. It categorizes them into runtime, development, and optional dependencies, along with necessary environment variables and external services.

## Runtime Dependencies

Core packages required for the application to run.

| Package Name | Version | Purpose |
|--------------|---------|---------|
| `requests`   | ^2.25.1 | For making HTTP requests to external APIs. |
| `numpy`      | ^1.21.0 | Provides support for numerical operations and data manipulation. |
| `pandas`     | ^1.3.0  | Used for data manipulation and analysis. |
| `aiohttp`    | ^3.7.4  | Asynchronous HTTP client/server for asyncio. |

## Development Dependencies

Packages used for development, testing, and building.

| Package Name      | Version | Purpose |
|-------------------|---------|---------|
| `pytest`          | ^6.2.4  | Testing framework for writing and running tests. |
| `pytest-asyncio`  | ^0.15.1 | Provides support for testing asyncio code with pytest. |
| `black`           | ^21.5b2 | Code formatter for maintaining code style consistency. |
| `flake8`          | ^3.9.2  | Linting tool for identifying syntax and style issues. |

## Optional Dependencies

Packages that provide additional functionality but aren't required.

| Package Name | Version | Purpose |
|--------------|---------|---------|
| `matplotlib` | ^3.4.2  | For data visualization and plotting. [Assumed] |
| `scipy`      | ^1.7.0  | Provides additional scientific computations. [Assumed] |

## Environment Variables

Configuration variables needed by the application.

- `OPENAI_API_KEY`: API key for accessing OpenAI services.
- `EXAMPLE_BASE_URL`: Base URL for example API endpoints. [Assumed]
- `EXAMPLE_API_KEY`: API key for example services. [Assumed]
- `EXAMPLE_MODEL_NAME`: Model name for example usage. [Assumed]
- `ANTHROPIC_API_KEY`: API key for accessing Anthropic services.

## External Services

APIs or platforms the project connects to.

- **OpenAI API**: Utilized for accessing OpenAI's language models and services.
- **Anthropic API**: Used for accessing Anthropic's AI models and services.
- **Example API**: Placeholder for additional API integrations. [Assumed]

This document should be updated as dependencies change or new ones are added.