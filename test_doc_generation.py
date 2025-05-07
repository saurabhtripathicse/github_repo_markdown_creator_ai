#!/usr/bin/env python3
"""
Enhanced Documentation Generator Test Script

This script tests the enhanced GitHub Documentation Generator features including:
- Recursive repository fetching
- Code sample extraction
- Project structure analysis
- Documentation generation with the enhanced AI Generator

It can be used directly without the FastAPI server.
"""

import os
import sys
import logging
import traceback
from dotenv import load_dotenv
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

# Load environment variables
load_dotenv()

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
        
        # Fetch repository data with enhanced features
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
        except Exception as e:
            logger.error(f"Error fetching repository: {str(e)}")
            traceback.print_exc()
            return []
        
        # Generate documentation using enhanced AI Generator
        try:
            logger.info("Generating documentation content with enhanced features")
            
            # Process code samples and analyze project structure
            logger.info(f"Repository has {len(repo_data.get('example_files', []))} example files")
            logger.info(f"Repository has {len(repo_data.get('code_samples', []))} code samples from markdown")
            logger.info(f"Detected project structure: {repo_data.get('project_structure', 'generic')}")
            
            # Generate documentation content
            ai_generator = AIGenerator()
            docs_content = ai_generator.generate_docs_content(repo_data)
            logger.info(f"Generated {len(docs_content)} documentation files")
        except Exception as e:
            logger.error(f"Error generating documentation: {str(e)}")
            traceback.print_exc()
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
