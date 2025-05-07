#!/usr/bin/env python3
"""
GitHub Documentation Generator

This script generates comprehensive documentation for GitHub repositories by directly
fetching content from GitHub's raw URLs and using AI to analyze the codebase.
"""

import os
import sys
import logging
import requests
import re
import time
import argparse
import subprocess
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_doc_generator')

# Load environment variables
load_dotenv()

# Constants
MAX_FILE_SIZE = 100000  # Maximum file size to process (100 KB)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Import AI Generator
from ai_generator import AIGenerator

def parse_github_url(url: str) -> tuple:
    """
    Parse GitHub repository URL to extract owner and repo name
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo)
    """
    # Handle URLs like https://github.com/owner/repo
    if url.startswith(("http://", "https://")):
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            return path_parts[0], path_parts[1]
    
    # Handle shorthand notation like owner/repo
    elif "/" in url and not url.startswith("/"):
        parts = url.split("/")
        if len(parts) == 2:
            return parts[0], parts[1]
    
    raise ValueError(f"Invalid GitHub repository URL: {url}")

def fetch_raw_content(owner: str, repo: str, path: str, branch: str = "main") -> str:
    """
    Fetch raw file content from GitHub
    
    Args:
        owner: Repository owner
        repo: Repository name
        path: File path
        branch: Branch name
        
    Returns:
        Raw file content
    """
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    
    try:
        response = requests.get(raw_url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch raw content from {raw_url}: {str(e)}")
        
        # Try alternate branch if main fails
        if branch == "main":
            try:
                alternate_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{path}"
                response = requests.get(alternate_url)
                response.raise_for_status()
                return response.text
            except requests.RequestException:
                logger.warning(f"Failed to fetch from alternate branch (master)")
        
        return ""

def fetch_repo_tree(owner: str, repo: str, branch: str = "main") -> List[Dict[str, Any]]:
    """
    Fetch repository tree from GitHub API
    
    Args:
        owner: Repository owner
        repo: Repository name
        branch: Branch name
        
    Returns:
        List of repository tree items
    """
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("tree", [])
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch repo tree: {str(e)}")
        
        # Try alternate branch if main fails
        if branch == "main":
            try:
                alternate_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
                response = requests.get(alternate_url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("tree", [])
            except requests.RequestException:
                logger.warning(f"Failed to fetch from alternate branch (master)")
        
        return []

def fetch_repo_data(owner: str, repo: str) -> Dict[str, Any]:
    """
    Fetch repository data from GitHub
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Returns:
        Repository data
    """
    repo_data = {
        "owner": owner,
        "name": repo,
        "description": "",
        "readme": None,
        "root_files": [],
        "src_files": [],
        "example_files": [],
        "doc_files": [],
        "repo_tree": []
    }
    
    # Fetch repository tree
    tree = fetch_repo_tree(owner, repo)
    repo_data["repo_tree"] = tree
    
    # Fetch repository info
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    try:
        response = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
        response.raise_for_status()
        repo_info = response.json()
        repo_data["description"] = repo_info.get("description", "")
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch repository info: {str(e)}")
    
    # Process repository tree
    for item in tree:
        path = item.get("path", "")
        size = item.get("size", 0)
        
        # Skip large files
        if size > MAX_FILE_SIZE:
            logger.info(f"Skipping large file: {path} ({size} bytes)")
            continue
        
        # Skip binary files
        if path.endswith((".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".ttf", ".eot", ".otf", ".mp4", ".webm", ".ogg", ".mp3", ".wav", ".flac", ".zip", ".tar", ".gz", ".rar", ".7z", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx")):
            continue
        
        # Fetch file content
        content = fetch_raw_content(owner, repo, path)
        
        # Categorize file
        file_data = {
            "path": path,
            "name": os.path.basename(path),
            "content": content
        }
        
        # Check if file is in root directory
        if "/" not in path:
            repo_data["root_files"].append(file_data)
            
            # Check if file is README
            if path.lower() == "readme.md":
                repo_data["readme"] = file_data
        
        # Check if file is source code
        if path.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".cs", ".fs", ".clj", ".ex", ".exs")):
            repo_data["src_files"].append(file_data)
        
        # Check if file is example
        if "example" in path.lower() or "demo" in path.lower() or "sample" in path.lower() or "tutorial" in path.lower():
            repo_data["example_files"].append(file_data)
        
        # Check if file is documentation
        if path.endswith((".md", ".rst", ".txt")) or "doc" in path.lower():
            repo_data["doc_files"].append(file_data)
    
    logger.info("Successfully fetched repository data:")
    logger.info(f"- Root files: {len(repo_data['root_files'])}")
    logger.info(f"- Source files: {len(repo_data['src_files'])}")
    logger.info(f"- Example files: {len(repo_data['example_files'])}")
    logger.info(f"- Documentation files: {len(repo_data['doc_files'])}")
    
    return repo_data

def generate_docs(repo_url: str, output_dir: str = "output", open_docs: bool = True) -> None:
    """
    Generate documentation for a GitHub repository
    
    Args:
        repo_url: GitHub repository URL
        output_dir: Output directory
        open_docs: Whether to open documentation after generation
    """
    # Parse GitHub URL
    try:
        owner, repo = parse_github_url(repo_url)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Create output directory
    repo_output_dir = os.path.join(output_dir, repo)
    os.makedirs(repo_output_dir, exist_ok=True)
    
    # Fetch repository data
    repo_data = fetch_repo_data(owner, repo)
    
    # Generate documentation
    logger.info("Generating documentation with AI Generator")
    ai_generator = AIGenerator()
    docs_content = ai_generator.generate_docs_content(repo_data)
    
    # Write documentation to files
    for filename, content in docs_content.items():
        output_path = os.path.join(repo_output_dir, filename)
        with open(output_path, "w") as f:
            f.write(content)
        logger.info(f"Wrote documentation to {output_path}")
    
    # Print success message
    print(f"\nSuccessfully generated documentation for {repo_url}")
    print("Documentation files:")
    for filename in docs_content.keys():
        print(f"- {os.path.join(repo_output_dir, filename)}")
    
    # Open documentation if requested
    if open_docs and docs_content:
        first_doc = os.path.join(repo_output_dir, next(iter(docs_content.keys())))
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", first_doc])
            elif sys.platform == "win32":  # Windows
                os.startfile(first_doc)
            else:  # Linux
                subprocess.run(["xdg-open", first_doc])
        except Exception as e:
            logger.warning(f"Failed to open documentation: {str(e)}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate documentation for GitHub repositories")
    parser.add_argument("repo_url", help="GitHub repository URL (e.g., https://github.com/owner/repo or owner/repo)")
    parser.add_argument("--output-dir", "-o", default="output", help="Output directory")
    parser.add_argument("--no-open", action="store_true", help="Don't open documentation after generation")
    args = parser.parse_args()
    
    # Check for required environment variables
    if not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN environment variable is not set. API rate limits may apply.")
    
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY environment variable is not set")
        sys.exit(1)
    
    # Generate documentation
    generate_docs(args.repo_url, args.output_dir, not args.no_open)

if __name__ == "__main__":
    main()
