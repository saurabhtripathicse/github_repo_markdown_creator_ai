#!/usr/bin/env python3
"""
Test script for generating documentation directly without using the FastAPI server.
This script demonstrates the markdown formatting capabilities.
"""

import os
import sys
import logging
from src.github_fetcher import GitHubFetcher
from src.ai_generator import AIGenerator
from src.doc_writer import DocWriter
from src.markdown_formatter import format_markdown_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_doc_generation')

def generate_documentation(repo_url):
    """
    Generate documentation for a GitHub repository
    
    Args:
        repo_url: URL of the GitHub repository
    
    Returns:
        List of generated file paths
    """
    try:
        logger.info(f"Documentation generation requested for: {repo_url}")
        
        # Parse GitHub URL
        github_fetcher = GitHubFetcher()
        try:
            owner, repo = github_fetcher.parse_url(repo_url)
            logger.info(f"Parsed GitHub URL: {owner}/{repo}")
        except ValueError as e:
            logger.error(f"Invalid GitHub URL: {repo_url}")
            return []
        
        # Fetch repository data
        try:
            logger.info(f"Fetching repository data for {owner}/{repo}")
            repo_data = github_fetcher.fetch_repository(owner, repo)
            logger.info(f"Successfully fetched repository data with {len(repo_data.get('root_files', []))} root files")
        except Exception as e:
            logger.error(f"Error fetching repository: {str(e)}")
            return []
        
        # Generate documentation
        try:
            logger.info("Generating documentation content")
            ai_generator = AIGenerator()
            docs_content = ai_generator.generate_docs_content(repo_data)
            logger.info(f"Generated {len(docs_content)} documentation files")
        except Exception as e:
            logger.error(f"Error generating documentation: {str(e)}")
            return []
        
        # Write documentation to files
        try:
            logger.info("Writing documentation to files")
            doc_writer = DocWriter()
            output_dir = f"docs/{owner}_{repo}"
            file_paths = doc_writer.write_docs(docs_content, output_dir)
            logger.info(f"Documentation written to {output_dir}")
            
            # Format markdown files
            try:
                logger.info("Formatting markdown files according to best practices")
                format_results = format_markdown_files(output_dir, recursive=True)
                formatted_count = sum(1 for success in format_results.values() if success)
                logger.info(f"Formatted {formatted_count}/{len(format_results)} markdown files successfully")
            except Exception as e:
                logger.warning(f"Error formatting markdown files: {str(e)}")
        except Exception as e:
            logger.error(f"Error writing documentation: {str(e)}")
            return []
        
        return file_paths
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return []

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_doc_generation.py <github_repo_url>")
        return 1
    
    repo_url = sys.argv[1]
    print(f"Generating documentation for {repo_url}...")
    
    file_paths = generate_documentation(repo_url)
    
    if file_paths:
        print("\nDocumentation generated successfully!")
        print("Generated files:")
        for file_path in file_paths:
            print(f"- {file_path}")
        return 0
    else:
        print("\nError generating documentation")
        return 1

if __name__ == "__main__":
    sys.exit(main())
