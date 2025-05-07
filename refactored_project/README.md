# GitHub Documentation Generator

A tool to automatically generate comprehensive documentation for GitHub repositories using AI.

## Overview

This project provides a simple command-line tool that:

1. Fetches repository content directly from GitHub's raw URLs
2. Analyzes the codebase structure and content
3. Generates comprehensive documentation using OpenAI's GPT-4o model
4. Outputs markdown files with project overview, module documentation, usage examples, and dependencies

## Features

- **Direct Raw Content Fetching**: Bypasses GitHub API JSON decoding issues
- **Enhanced AI Generator**: Produces high-quality documentation with GPT-4o
- **Simplified Architecture**: Single script with minimal dependencies
- **Comprehensive Documentation**: Generates multiple documentation files:
  - `OVERVIEW.md`: High-level project overview
  - `MODULES.md`: Documentation of modules and their relationships
  - `USAGE.md`: Usage examples and instructions
  - `DEPENDENCIES.md`: Project dependencies and requirements

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/github-doc-generator.git
   cd github-doc-generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   # Create a .env file
   touch .env
   
   # Add your GitHub token and OpenAI API key
   echo "GITHUB_TOKEN=your_github_token" >> .env
   echo "OPENAI_API_KEY=your_openai_api_key" >> .env
   ```

## Usage

Generate documentation for a GitHub repository:

```bash
python github_doc_generator.py https://github.com/owner/repo
```

Additional options:

```bash
# Specify output directory
python github_doc_generator.py https://github.com/owner/repo --output-dir docs

# Don't open documentation after generation
python github_doc_generator.py https://github.com/owner/repo --no-open
```

## Project Structure

```
github-doc-generator/
├── github_doc_generator.py  # Main script
├── ai_generator.py          # AI-powered documentation generation
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── output/                  # Generated documentation
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| GITHUB_TOKEN | GitHub Personal Access Token | Recommended |
| OPENAI_API_KEY | OpenAI API Key | Yes |

## Recent Improvements

The documentation generator has been significantly enhanced with:

1. **Direct Raw Content Fetching**:
   - Bypasses GitHub API JSON decoding issues
   - Fetches content directly from GitHub's raw URLs
   - Improves reliability and error handling

2. **Enhanced AI Generator**:
   - Upgraded to GPT-4o for higher quality documentation
   - Better code example extraction and formatting
   - Improved structure and organization of documentation

3. **Simplified Architecture**:
   - Consolidated functionality into a single script
   - Removed unnecessary dependencies
   - Streamlined documentation generation process

4. **Output Quality**:
   - More detailed and comprehensive documentation
   - Better formatted with consistent markdown structure
   - More useful code examples with complete context

## Requirements

- Python 3.8+
- OpenAI API key
- GitHub Personal Access Token (recommended)

## License

MIT
