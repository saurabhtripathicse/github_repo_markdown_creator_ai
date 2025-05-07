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
    global RATE_LIMITED
    
    # If we're in a rate-limited state, don't make any GitHub API requests
    if RATE_LIMITED:
        logger.warning(f"Skipping GitHub raw content fetch for {path} due to rate limiting")
        return ""
    
    # Skip directories which will always fail with raw content URLs
    if path.endswith(("/", "/.github", "/.vscode", "/docs")) or "/" in path and not any(path.endswith(ext) for ext in [".py", ".js", ".md", ".txt", ".json", ".toml", ".yml", ".yaml", ".c", ".cpp", ".h", ".java", ".go", ".rs", ".rb", ".php"]):
        return ""
        
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    
    try:
        response = requests.get(raw_url)
        
        # Check if we hit rate limiting
        if response.status_code == 429:
            logger.error(f"Rate limit exceeded while fetching {raw_url}")
            RATE_LIMITED = True
            return ""
            
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        # Only log warnings for files that should exist, not directories
        if not path.endswith("/") and "." in path.split("/")[-1]:
            logger.warning(f"Failed to fetch raw content from {raw_url}: {str(e)}")
        
        # Try alternate branch if main fails
        if branch == "main" and not RATE_LIMITED:
            try:
                alternate_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{path}"
                response = requests.get(alternate_url)
                
                # Check if we hit rate limiting
                if response.status_code == 429:
                    logger.error(f"Rate limit exceeded while fetching {alternate_url}")
                    RATE_LIMITED = True
                    return ""
                    
                response.raise_for_status()
                return response.text
            except requests.RequestException:
                if not path.endswith("/") and "." in path.split("/")[-1]:
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
    global RATE_LIMITED
    
    # If we're in a rate-limited state, don't make any GitHub API requests
    if RATE_LIMITED:
        logger.warning(f"Skipping GitHub repo tree fetch for {owner}/{repo} due to rate limiting")
        return []
    
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    
    try:
        response = requests.get(url, headers=headers)
        
        # Check if we hit rate limiting
        if response.status_code == 429:
            logger.error(f"Rate limit exceeded while fetching repo tree from {url}")
            RATE_LIMITED = True
            return []
            
        response.raise_for_status()
        data = response.json()
        return data.get("tree", [])
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch repo tree: {str(e)}")
        
        # Try alternate branch if main fails
        if branch == "main" and not RATE_LIMITED:
            try:
                alternate_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
                response = requests.get(alternate_url, headers=headers)
                
                # Check if we hit rate limiting
                if response.status_code == 429:
                    logger.error(f"Rate limit exceeded while fetching repo tree from {alternate_url}")
                    RATE_LIMITED = True
                    return []
                    
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

def generate_docs(repo_url: str, output_dir: str = "output", open_docs: bool = True, skip_github: bool = False) -> None:
    """
    Generate documentation for a GitHub repository
    
    Args:
        repo_url: GitHub repository URL
        output_dir: Output directory
        open_docs: Whether to open documentation after generation
        skip_github: Whether to skip GitHub API extraction
    """
    global RATE_LIMITED
    
    # Parse GitHub URL
    try:
        owner, repo = parse_github_url(repo_url)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Create output directory
    repo_output_dir = os.path.join(output_dir, repo)
    os.makedirs(repo_output_dir, exist_ok=True)
    
    # Check for cached data
    cache_file = os.path.join(repo_output_dir, "repo_data_cache.json")
    repo_data = None
    
    if skip_github or RATE_LIMITED:
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    repo_data = json.load(f)
                logger.info(f"Loaded cached repository data for {owner}/{repo}")
            except Exception as e:
                logger.warning(f"Failed to load cached repository data: {str(e)}")
        
        if not repo_data:
            if RATE_LIMITED:
                logger.error(f"GitHub API rate limit exceeded and no cached data available for {owner}/{repo}")
                print(f"\nERROR: GitHub API rate limit exceeded and no cached data available for {owner}/{repo}")
                print("Please try again later when the rate limit resets.")
                sys.exit(1)
    
    # Fetch repository data if not loaded from cache
    if not repo_data:
        repo_data = fetch_repo_data(owner, repo)
        
        # Cache the repository data for future use
        try:
            with open(cache_file, "w") as f:
                json.dump(repo_data, f)
            logger.info(f"Cached repository data for {owner}/{repo}")
        except Exception as e:
            logger.warning(f"Failed to cache repository data: {str(e)}")
    
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
    if RATE_LIMITED:
        print("NOTE: Documentation was generated with limited GitHub data due to rate limiting.")
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

def check_github_rate_limit() -> bool:
    """
    Check GitHub API rate limit status
    
    Returns:
        True if rate limit is sufficient, False otherwise
    """
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    try:
        response = requests.get("https://api.github.com/rate_limit", headers=headers)
        response.raise_for_status()
        rate_data = response.json()
        
        # Get core rate limit info
        core_limit = rate_data.get("resources", {}).get("core", {})
        remaining = core_limit.get("remaining", 0)
        limit = core_limit.get("limit", 0)
        reset_time = core_limit.get("reset", 0)
        
        # Calculate time until reset in AM/PM format
        reset_datetime_ampm = time.strftime('%Y-%m-%d %I:%M:%S %p', time.localtime(reset_time))
        
        # Calculate time remaining until reset
        current_time = time.time()
        time_remaining_seconds = max(0, reset_time - current_time)
        hours, remainder = divmod(time_remaining_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_remaining_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        # Log rate limit information
        logger.info(f"GitHub API Rate Limit: {remaining}/{limit} requests remaining")
        logger.info(f"Rate limit resets at: {reset_datetime_ampm} (in {time_remaining_str})")
        
        # Check if we have enough requests remaining (at least 50)
        if remaining < 50:
            logger.error(f"GitHub API rate limit too low: {remaining}/{limit} requests remaining")
            logger.error(f"Rate limit will reset at {reset_datetime_ampm} (in {time_remaining_str})")
            print(f"\nERROR: GitHub API rate limit too low ({remaining}/{limit} requests remaining)")
            print(f"You can retry in {time_remaining_str} when the rate limit resets.")
            print("Use --force to proceed anyway (not recommended).")
            return False
        
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to check GitHub rate limit: {str(e)}")
        return False

# Global variable to track if we're in a rate-limited state
RATE_LIMITED = False

def main():
    """Main entry point"""
    global RATE_LIMITED
    
    parser = argparse.ArgumentParser(description="Generate documentation for GitHub repositories")
    parser.add_argument("repo_url", help="GitHub repository URL (e.g., https://github.com/owner/repo or owner/repo)")
    parser.add_argument("--output-dir", "-o", default="output", help="Output directory")
    parser.add_argument("--no-open", action="store_true", help="Don't open documentation after generation")
    parser.add_argument("--force", "-f", action="store_true", help="Force generation even if rate limit is low")
    parser.add_argument("--skip-github", "-s", action="store_true", help="Skip GitHub API extraction and use cached data if available")
    args = parser.parse_args()
    
    # Check for required environment variables
    if not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN environment variable is not set. API rate limits may apply.")
    
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY environment variable is not set")
        sys.exit(1)
    
    # Check GitHub rate limit
    rate_limit_ok = check_github_rate_limit()
    if not rate_limit_ok:
        if args.force:
            logger.warning("Proceeding with --force flag, but GitHub API extraction will be limited")
            RATE_LIMITED = True
        else:
            logger.error("GitHub API rate limit is too low. Use --force to generate documentation anyway.")
            sys.exit(1)
    
    # Generate documentation
    generate_docs(args.repo_url, args.output_dir, not args.no_open, skip_github=args.skip_github)

if __name__ == "__main__":
    main()
