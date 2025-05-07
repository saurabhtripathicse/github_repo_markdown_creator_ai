#!/usr/bin/env python3
"""
Improved GitHub Documentation Generator Script

This script provides a robust implementation for generating documentation
from GitHub repositories with improved error handling and direct raw content fetching.
"""

import os
import sys
import logging
import requests
import base64
import json
import time
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_doc_generator')

# Load environment variables
load_dotenv()

# Import the required modules
from src.github_fetcher import GitHubFetcher
from src.ai_generator import AIGenerator
from src.doc_writer import DocWriter
from src.markdown_formatter import format_markdown_files

def fetch_repository_with_raw_content(repo_url: str) -> Dict[str, Any]:
    """
    Fetch repository data with improved error handling using raw content URLs
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        Repository data dictionary
    """
    github_fetcher = GitHubFetcher()
    
    # Parse GitHub URL
    try:
        owner, repo = github_fetcher.parse_url(repo_url)
        logger.info(f"Parsed GitHub URL: {owner}/{repo}")
    except ValueError as e:
        logger.error(f"Invalid GitHub URL: {repo_url}")
        raise
    
    # Fetch repository data
    try:
        logger.info(f"Fetching repository data for {owner}/{repo} with enhanced features")
        repo_data = github_fetcher.fetch_repository(owner, repo)
        
        # Log enhanced repository data information
        logger.info(f"Successfully fetched repository data:")
        logger.info(f"- Root files: {len(repo_data.get('root_files', []))}")
        logger.info(f"- Source files: {len(repo_data.get('src_files', []))}")
        logger.info(f"- Example files: {len(repo_data.get('example_files', []))}")
        logger.info(f"- Documentation files: {len(repo_data.get('doc_files', []))}")
        logger.info(f"- Code samples from markdown: {len(repo_data.get('code_samples', []))}")
        logger.info(f"- Project structure: {repo_data.get('project_structure', 'generic')}")
        
        return repo_data
    except Exception as e:
        logger.error(f"Error fetching repository: {str(e)}")
        raise

def generate_documentation(repo_url: str) -> List[str]:
    """
    Generate documentation for a GitHub repository with improved error handling
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        List of generated documentation file paths
    """
    try:
        # Fetch repository data
        repo_data = fetch_repository_with_raw_content(repo_url)
        
        # Generate documentation
        logger.info("Generating documentation with enhanced AI Generator")
        ai_generator = AIGenerator()
        docs_content = ai_generator.generate_docs_content(repo_data)
        logger.info(f"Generated {len(docs_content)} documentation files")
        
        # Write documentation to files
        repo_name = repo_data.get("name", "repository")
        output_dir = f"output/{repo_name}"
        os.makedirs(output_dir, exist_ok=True)
        
        doc_writer = DocWriter()
        file_paths = []
        
        for filename, content in docs_content.items():
            file_path = os.path.join(output_dir, filename)
            doc_writer.write_file(file_path, content)
            file_paths.append(file_path)
            logger.info(f"Wrote documentation to {file_path}")
        
        # Format markdown files
        format_markdown_files(file_paths)
        
        return file_paths
    except Exception as e:
        logger.error(f"Error generating documentation: {str(e)}")
        return []

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_docs_improved.py <github_repo_url>")
        sys.exit(1)
        
    repo_url = sys.argv[1]
    print(f"Generating documentation for {repo_url}...")
    
    try:
        file_paths = generate_documentation(repo_url)
        if file_paths:
            print(f"\nSuccessfully generated documentation for {repo_url}")
            print("Documentation files:")
            for path in file_paths:
                print(f"- {path}")
        else:
            print(f"\nFailed to generate documentation for {repo_url}")
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)
