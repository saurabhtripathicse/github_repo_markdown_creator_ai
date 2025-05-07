# GitHub Documentation Generator - Project Documentation

## Overview

The GitHub Documentation Generator is an AI-powered application that analyzes GitHub repositories and automatically generates comprehensive documentation. It leverages OpenAI's API to understand code structure, extract key information, and produce high-quality documentation that helps developers understand and use repositories more effectively.

## Architecture

The project follows a multi-agent architecture using Google's Agent Development Kit (ADK) approach:

### Backend Components

1. **API Layer** (`main.py`):
   - FastAPI application definition
   - API endpoints for documentation generation and web search
   - Request/response models
   - Error handling

2. **Core Services**:
   - `github_fetcher.py`: GitHub API interaction, repository data extraction
   - `ai_generator.py`: OpenAI integration for documentation generation
   - `doc_writer.py`: File output handling
   - `diagrammer.py`: C4 architecture diagram generation
   - `web_scraper.py`: Web search and code snippet extraction

3. **Multi-Agent System**:
   - Repository Fetcher Agent: Retrieves repository contents
   - Code Analysis Agent: Analyzes code structure and dependencies
   - Documentation Generation Agent: Creates documentation files
   - Integration Agent: Combines all outputs

4. **Storage Layer**:
   - MongoDB for data persistence
   - File system for generated documentation

## Documentation Generation Process

The documentation generation process follows these steps:

1. **Repository Fetching**:
   - Parse GitHub URL to extract owner and repository name
   - Fetch repository metadata, files, and README
   - Extract code structure and dependencies
   - Identify and extract code examples from example directories, subdirectories, and notebooks
   - Support multiple file types (.py, .js, .ts, .jsx, .tsx, .md, .ipynb)

2. **AI-Powered Analysis**:
   - Process repository data using OpenAI GPT-4o API
   - Extract key components, features, and usage patterns
   - Prioritize real code examples from the repository with source citations
   - Generate structured documentation content

3. **Web Search Enhancement** (optional):
   - Search for additional code examples and context
   - Extract code snippets from web pages
   - Integrate web search results into documentation

4. **Documentation Writing**:
   - Generate multiple documentation files:
     - OVERVIEW.md: Repository overview
     - MODULES.md: Module documentation
     - USAGE.md: Usage instructions
     - DEPENDENCIES.md: Dependency information
   - Write files to output directory

5. **Diagram Generation** (optional):
   - Create C4 architecture diagram based on repository structure
   - Generate SVG output

## OpenAI Model Configuration

The system uses OpenAI's GPT-4o model for documentation generation, with the following configuration:

```python
response = client.chat.completions.create(
    model="gpt-4o",  # Advanced model for higher quality documentation
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=temperature,
    max_tokens=3000  # Increased token limit for comprehensive documentation
)
```

This configuration allows for more detailed and comprehensive documentation generation compared to previous models.

## Prompt Templates

The system uses carefully crafted prompt templates to generate high-quality documentation. These templates have been refined to produce structured, non-redundant, and actionable documentation.

### OVERVIEW.md Prompt

```python
system_prompt = (
    "You are a senior AI technical writer generating a detailed, well-structured `OVERVIEW.md` file for a GitHub repository. "
    "The output should be informative and easy to read by both developers and LLM agents.\n\n"

    "Write in clear, neutral tone. Avoid filler adjectives. Use markdown headers (###) for each section.\n\n"

    "Follow this structure:\n"
    "### Purpose\n"
    "What problem this repo solves, based on README and metadata.\n\n"

    "### Key Features\n"
    "Bullet list of major capabilities (min 5, max 10). Extract from README, code, or web snippets.\n\n"

    "### Repository Structure\n"
    "List of major folders and files with one-line purpose (e.g., src/, tests/, pyproject.toml).\n\n"

    "### Use Cases\n"
    "Mention 2–3 specific use scenarios (e.g., chatbot orchestration, agent workflows, SDK integration).\n\n"

    "### Requirements\n"
    "Mention supported environments, languages, frameworks, and version constraints.\n\n"

    "### Status\n"
    "Whether the project is production-ready, experimental, or WIP.\n\n"

    "✅ Use ~2000–3000 tokens. Integrate relevant content from README and web search results.\n"
    "✅ Use real examples from the repository files and README.\n"
    "✅ Include code snippets (10-30 lines) where appropriate to illustrate key concepts.\n"
    "✅ Use fallback assumptions if data is missing, marked with [Assumed].\n"
    "✅ Write clear markdown headers and use triple-backtick code blocks.\n"
)
```

### USAGE.md Prompt

```python
system_prompt = (
    "You are a senior AI technical writer generating a USAGE.md file for a GitHub project.\n\n"

    "Use markdown with `###` headers and triple-backtick code blocks. The goal is to help developers run and understand the project quickly.\n\n"

    "Include the following sections (skip if insufficient data):\n\n"

    "### Installation\n"
    "Steps via `pip`, GitHub clone, or Docker. Mention requirements or virtualenv setup.\n\n"

    "### Quick Start\n"
    "A working 10–30 line script showing how to import and run the core feature. ALWAYS use real examples from the repository (especially from 'examples/' or 'demos/' directories). Include full import paths.\n\n"

    "### Configuration & Authentication\n"
    "Environment variables, API keys, or config files (from .env or dotenv). Use table format if needed.\n\n"

    "### Core Usage Patterns\n"
    "Common API calls, flows, or class usage. PRIORITIZE real examples from the repository code. For each example, cite the source file path. Include complete code snippets with imports.\n\n"

    "### Error Handling\n"
    "List at least 2 possible issues (e.g., auth errors, rate limits) and how to fix.\n\n"

    "### Advanced Usage\n"
    "Optional plugins, tool calling, SDK extensions, or uncommon features.\n\n"

    "### Common Pitfalls\n"
    "Mention things users often misconfigure or miss (e.g., `OPENAI_API_KEY` not loaded).\n\n"

    "✅ ALWAYS cite the source file path for each code example (e.g., 'From examples/demo.py').\n"
    "✅ Only use code that exists in the repo or web search. Don't invent or modify examples unless necessary.\n"
    "✅ Mark inferred values with `[Assumed]`. Include import paths (`from x import y`).\n"
    "✅ Ensure code examples are complete and runnable with proper imports and context.\n"
    "✅ Output size: 2000–3000 tokens.\n"
)
```

### MODULES.md Prompt

```python
system_prompt = (
    "You are a senior AI technical writer generating a MODULES.md file describing the repo's modules and interfaces.\n\n"

    "Use markdown formatting with `###` for each major section.\n\n"

    "### Module Overview\n"
    "Describe the architectural layout and what modules exist.\n\n"

    "### Core Modules\n"
    "For each file in `src/` or root:\n"
    "- Filename and path\n"
    "- High-level summary\n"
    "- Public classes/functions\n"
    "- Example import path\n"
    "- 10–20 line usage snippet (use ACTUAL examples from the repository when available)\n\n"

    "### Extension Points\n"
    "Which classes/functions can be extended or overridden by developers.\n\n"

    "### Utility Modules\n"
    "Reusable components (logging, file I/O, helper functions).\n\n"

    "### Module Relationships\n"
    "Mention if there is coupling between modules or clear separation of concerns.\n\n"

    "✅ Don't document private methods (`_func`).\n"
    "✅ ALWAYS cite the source file for each code example (e.g., 'From examples/demo.py').\n"
    "✅ Prioritize REAL examples from the repository over created examples.\n"
    "✅ Infer structure based on class names, usage patterns, or imports.\n"
    "✅ Use `[Assumed]` for unclear parts.\n"
    "✅ Ensure code examples are complete with proper imports and context.\n"
    "✅ Use at least 2000 tokens of output.\n"
)
```

### DEPENDENCIES.md Prompt

```python
system_prompt = (
    "You are a senior AI technical writer generating a DEPENDENCIES.md file for a GitHub repository.\n\n"

    "Use markdown tables. Group dependencies based on type and provide useful metadata.\n\n"

    "### Runtime Dependencies\n"
    "| Package | Description | Required | Version |\n"
    "|---------|-------------|----------|----------|\n\n"

    "### Development Dependencies\n"
    "| Package | Description | Required | Version |\n\n"

    "### Optional Dependencies\n"
    "| Package | Purpose | Optional? |\n\n"

    "### Environment Variables\n"
    "| Variable | Purpose | Required | Example |\n\n"

    "### External Services\n"
    "List APIs or platforms the project connects to (e.g., OpenAI, Redis, MongoDB). Include doc URLs if available.\n\n"

    "✅ Infer purpose from pyproject.toml, requirements.txt, imports, or web snippets.\n"
    "✅ Use `[Assumed]` if the purpose isn't clearly stated.\n"
    "✅ Don't duplicate or hallucinate packages.\n"
    "✅ Try to include version constraints if available.\n"
)
```

## Documentation Output

The GitHub Documentation Generator produces the following output files:

1. **OVERVIEW.md**:
   - Repository purpose and key features
   - High-level architecture
   - Use cases and requirements
   - Project status and maturity

2. **USAGE.md**:
   - Installation instructions
   - Quick start guide with full working examples from the repository
   - Configuration and authentication details
   - Core usage patterns with real code snippets and source citations
   - Common pitfalls to avoid
   - Error handling with try-except examples
   - Advanced usage options

3. **MODULES.md**:
   - Module overview and relationships
   - Core modules documentation with import paths
   - Public classes and methods
   - Usage examples for each major class
   - Extension points for customization

4. **DEPENDENCIES.md**:
   - Runtime dependencies in tabular format
   - Development dependencies
   - Optional dependencies
   - Environment variables with examples
   - External services and APIs

## Recent Improvements

### OpenAI Model Upgrade

The documentation generator has been upgraded to use the GPT-4o model instead of the previously used gpt-3.5-turbo-16k model. This upgrade provides several benefits:

- Higher quality, more detailed documentation
- Better understanding of code structure and relationships
- More comprehensive code examples
- Improved handling of complex repositories

The `max_tokens` parameter has also been increased from 2000 to 3000 to allow for more comprehensive documentation generation.

### Enhanced Code Example Extraction

The GitHub fetcher module has been enhanced to better identify and extract code examples from repositories:

- Expanded patterns for identifying important directories (src, test, examples, docs)
- Support for more file types (.py, .js, .ts, .jsx, .tsx, .md, .ipynb)
- Increased number of files fetched from example directories
- Added capability to search subdirectories within example folders
- Implemented fallback mechanisms to find examples in other locations
- Added support for finding examples in notebooks directories

These improvements ensure that the documentation includes more relevant, real-world code examples from the repository.

### Improved Documentation Structure

- Better formatted with consistent markdown headers
- More detailed and comprehensive documentation
- Improved tabular presentation of structured data
- More useful code examples with complete context

### Developer Experience

The documentation generator now provides:

- More actionable documentation with copy-paste friendly examples
- Better error handling guidance
- Clearer configuration instructions
- More specific use case examples

## Future Enhancements

Planned enhancements for the documentation generator include:

1. **Cross-Referencing**:
   - Add links between documentation files for better navigation
   - Create an index or table of contents

2. **Contextual Examples**:
   - Further tailor examples to the specific repository's domain
   - Generate more domain-specific usage patterns

3. **Automatic Skipping**:
   - Skip generating certain files entirely if they would be too minimal
   - Merge content into other files when appropriate

4. **Dependency Analysis**:
   - Improve detection of optional vs. required dependencies
   - Better categorization of development vs. runtime dependencies

5. **Versioning Information**:
   - Better extraction of version compatibility information
   - Documentation of breaking changes between versions

## Usage

To generate documentation for a GitHub repository:

```bash
python generate_docs.py [https://github.com/username/repository](https://github.com/username/repository) --web-search
```

For more information, see the [USAGE.md](USAGE.md) file.

## Contributing

Contributions to improve the documentation generator are welcome. Areas for improvement include:

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

## Acknowledgments

- OpenAI for providing the API used for documentation generation
- Google's Agent Development Kit (ADK) for the multi-agent architecture
- The open-source community for inspiration and feedback
