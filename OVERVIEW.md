# GitHub Documentation Generator

## Overview

The GitHub Documentation Generator is an AI-powered application that automatically analyzes GitHub repositories and generates comprehensive documentation in Markdown format. It leverages the power of OpenAI's API to understand code structure, extract key information, and produce high-quality documentation that helps developers understand and use repositories more effectively.

## Problem Statement

Understanding unfamiliar code repositories can be challenging and time-consuming. Developers often face:

- Incomplete or outdated documentation
- Lack of clear usage examples
- Difficulty understanding the overall architecture
- Challenges identifying the purpose of different modules and components

The GitHub Documentation Generator addresses these issues by automatically generating structured, comprehensive documentation that provides clear insights into repository structure, functionality, and usage patterns.

## Key Features

- **Repository Analysis**: Fetch and analyze public GitHub repositories via URL
- **Multi-file Documentation Generation**:
  - OVERVIEW.md - Concise repository overview
  - MODULES.md - Documentation of modules and public interfaces
  - USAGE.md - Usage examples derived from tests and README
  - DEPENDENCIES.md - List of dependencies with explanations
  - ARCHITECTURE.md - Optional C4 architecture diagram
- **Web Search Integration**:
  - Search for additional code examples and context
  - Extract code snippets from web pages
  - Integrate web search results into generated documentation
- **AI-Powered Content Generation**:
  - OpenAI API integration for intelligent documentation
  - Context-aware descriptions of code components
  - Automatic extraction of usage examples
- **Multiple Access Methods**:
  - REST API for programmatic access
  - Command-line interface for quick documentation generation
  - Web interface (planned for future releases)

## Target Audience

- **Open-source contributors** looking to understand new projects quickly
- **Development teams** needing to maintain documentation for their projects
- **Software engineers** exploring third-party libraries and frameworks
- **Technical writers** seeking a foundation for comprehensive documentation
- **Project managers** who need high-level overviews of technical projects

## Technical Architecture

The GitHub Documentation Generator follows a multi-agent architecture using Google's Agent Development Kit (ADK) approach:

1. **Backend (Python/FastAPI)**:
   - API routes for handling repository operations
   - GitHub service for interacting with GitHub API
   - Documentation service for generating documentation
   - Multi-agent system with specialized agents
   - MongoDB for data storage

2. **Core Components**:
   - GitHub Fetcher: Retrieves repository data from GitHub
   - AI Generator: Processes code using OpenAI API
   - Documentation Writer: Formats and outputs Markdown files
   - Web Scraper: Enhances documentation with external examples
   - Diagrammer: Generates C4 architecture diagrams

## Current Status

The GitHub Documentation Generator is currently in active development. The core functionality for repository analysis, documentation generation, and web search integration is implemented and working. Future enhancements will include:

- Improved AI models for more accurate documentation
- Support for additional programming languages
- Enhanced web interface for easier interaction
- Integration with more version control platforms beyond GitHub
- Customizable documentation templates

## Getting Started

For installation instructions and usage examples, please refer to the [USAGE.md](USAGE.md) document.
