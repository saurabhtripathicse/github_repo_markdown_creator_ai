#!/usr/bin/env python3
"""
Direct GitHub Documentation Generator

This script generates documentation for GitHub repositories by directly
fetching raw content from GitHub's raw content URLs, bypassing the GitHub API
for file content retrieval to avoid JSON decoding issues.
"""

import os
import sys
import logging
import requests
import re
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('direct_github_docs')

# Load environment variables
load_dotenv()

# Constants
MAX_FILE_SIZE = 100000  # Maximum file size to process (100 KB)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Import AI Generator after setting up environment
from src.ai_generator import AIGenerator
from src.doc_writer import DocWriter
from src.markdown_formatter import format_markdown_files

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
        if parsed.netloc not in ["github.com", "www.github.com"]:
            raise ValueError(f"Not a GitHub URL: {url}")
        
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            return path_parts[0], path_parts[1]
    
    # Handle owner/repo format
    elif "/" in url and not url.startswith("/"):
        parts = url.split("/")
        if len(parts) == 2:
            return parts[0], parts[1]
    
    raise ValueError(f"Invalid GitHub URL format: {url}. Expected format: 'https://github.com/owner/repo' or 'owner/repo'")

def fetch_raw_content(owner: str, repo: str, path: str, branch: str = "main") -> str:
    """
    Fetch raw file content directly from GitHub's raw content URL
    
    Args:
        owner: Repository owner
        repo: Repository name
        path: File path
        branch: Branch name
        
    Returns:
        Raw file content as string
    """
    # Construct raw content URL
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    logger.info(f"Fetching raw content from: {raw_url}")
    
    try:
        # Make direct request to raw content URL
        headers = {"Accept": "text/plain"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
            
        response = requests.get(raw_url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.warning(f"Error fetching raw content for {path}: {str(e)}")
        return ""

def fetch_repository_info(owner: str, repo: str) -> Dict[str, Any]:
    """
    Fetch basic repository information from GitHub API
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Returns:
        Repository information dictionary
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    logger.info(f"Fetching repository info from: {url}")
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching repository info: {str(e)}")
        return {
            "name": repo,
            "full_name": f"{owner}/{repo}",
            "description": "",
            "default_branch": "main"
        }

def fetch_repository_tree(owner: str, repo: str, branch: str = "main") -> List[Dict[str, Any]]:
    """
    Fetch repository file tree using GitHub API
    
    Args:
        owner: Repository owner
        repo: Repository name
        branch: Branch name
        
    Returns:
        List of file paths in the repository
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    logger.info(f"Fetching repository tree from: {url}")
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract file paths from tree
        files = []
        for item in data.get("tree", []):
            if item.get("type") == "blob":  # Only include files, not directories
                files.append({
                    "path": item.get("path", ""),
                    "type": "file",
                    "size": item.get("size", 0)
                })
        
        return files
    except Exception as e:
        logger.error(f"Error fetching repository tree: {str(e)}")
        return []

def fetch_readme(owner: str, repo: str, branch: str = "main") -> str:
    """
    Fetch README content directly using raw content URL
    
    Args:
        owner: Repository owner
        repo: Repository name
        branch: Branch name
        
    Returns:
        README content as string
    """
    # Try common README filenames
    readme_paths = [
        "README.md",
        "README.rst",
        "README.txt",
        "README",
        "readme.md"
    ]
    
    for path in readme_paths:
        content = fetch_raw_content(owner, repo, path, branch)
        if content:
            logger.info(f"Found README at {path}")
            return content
    
    logger.warning(f"No README found for {owner}/{repo}")
    return ""

def is_source_file(path: str) -> bool:
    """
    Check if a file is a source code file
    
    Args:
        path: File path
        
    Returns:
        True if the file is a source code file
    """
    source_extensions = [
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.rb', '.go',
        '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.swift', '.kt',
        '.rs', '.scala', '.sh', '.bash', '.pl', '.pm', '.r'
    ]
    
    return any(path.lower().endswith(ext) for ext in source_extensions)

def is_example_file(path: str) -> bool:
    """
    Check if a file is an example file
    
    Args:
        path: File path
        
    Returns:
        True if the file is an example file
    """
    example_patterns = [
        r'example[s]?[/\\]',
        r'sample[s]?[/\\]',
        r'demo[s]?[/\\]',
        r'tutorial[s]?[/\\]',
        r'test[s]?[/\\]',
        r'example[s]?\.',
        r'sample[s]?\.',
        r'demo[s]?\.'
    ]
    
    path_lower = path.lower()
    
    # Check if path matches example patterns
    if any(re.search(pattern, path_lower) for pattern in example_patterns):
        return True
    
    # Check if file is in an example directory
    path_parts = path_lower.split("/")
    example_dirs = ['examples', 'sample', 'demo', 'tutorial', 'test']
    if any(part in example_dirs for part in path_parts):
        return True
    
    # Check if file is a common example file type
    if is_source_file(path) and ('example' in path_lower or 'sample' in path_lower or 'demo' in path_lower):
        return True
    
    return False

def is_doc_file(path: str) -> bool:
    """
    Check if a file is a documentation file
    
    Args:
        path: File path
        
    Returns:
        True if the file is a documentation file
    """
    doc_extensions = ['.md', '.rst', '.txt', '.adoc', '.asciidoc', '.wiki']
    doc_patterns = [
        r'doc[s]?[/\\]',
        r'documentation[/\\]',
        r'wiki[/\\]',
        r'guide[s]?[/\\]',
        r'manual[s]?[/\\]'
    ]
    
    path_lower = path.lower()
    
    # Check if path has documentation extension
    if any(path_lower.endswith(ext) for ext in doc_extensions):
        return True
    
    # Check if path matches documentation patterns
    if any(re.search(pattern, path_lower) for pattern in doc_patterns):
        return True
    
    # Check if file is in a documentation directory
    path_parts = path_lower.split("/")
    doc_dirs = ['docs', 'documentation', 'wiki', 'guides', 'manuals']
    if any(part in doc_dirs for part in path_parts):
        return True
    
    return False

def fetch_repository_data(owner: str, repo: str) -> Dict[str, Any]:
    """
    Fetch repository data directly using raw content URLs
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Returns:
        Repository data dictionary
    """
    # Get repository information
    repo_info = fetch_repository_info(owner, repo)
    branch = repo_info.get("default_branch", "main")
    
    # Get repository file tree
    tree = fetch_repository_tree(owner, repo, branch)
    
    # Get README content
    readme = fetch_readme(owner, repo, branch)
    
    # Categorize files
    root_files = []
    src_files = []
    example_files = []
    doc_files = []
    
    # Process files in tree
    for item in tree:
        path = item.get("path", "")
        
        # Skip large files
        if item.get("size", 0) > MAX_FILE_SIZE:
            logger.info(f"Skipping large file: {path} ({item.get('size', 0)} bytes)")
            continue
        
        # Categorize file
        if "/" not in path:  # Root file
            content = fetch_raw_content(owner, repo, path, branch)
            if content:
                root_files.append({
                    "name": path,
                    "path": path,
                    "content": content,
                    "size": len(content)
                })
        
        if is_source_file(path):
            content = fetch_raw_content(owner, repo, path, branch)
            if content:
                src_files.append({
                    "name": os.path.basename(path),
                    "path": path,
                    "content": content,
                    "size": len(content)
                })
        
        if is_example_file(path):
            content = fetch_raw_content(owner, repo, path, branch)
            if content:
                example_files.append({
                    "name": os.path.basename(path),
                    "path": path,
                    "content": content,
                    "size": len(content)
                })
        
        if is_doc_file(path):
            content = fetch_raw_content(owner, repo, path, branch)
            if content:
                doc_files.append({
                    "name": os.path.basename(path),
                    "path": path,
                    "content": content,
                    "size": len(content)
                })
    
    # Detect project structure
    project_structure = "generic"
    if any(f["name"] == "pyproject.toml" for f in root_files) or any(f["name"] == "setup.py" for f in root_files):
        project_structure = "python"
    elif any(f["name"] == "package.json" for f in root_files):
        project_structure = "javascript"
    elif any(f["name"] == "pom.xml" for f in root_files) or any(f["name"] == "build.gradle" for f in root_files):
        project_structure = "java"
    elif any(f["name"] == "Cargo.toml" for f in root_files):
        project_structure = "rust"
    elif any(f["name"] == "go.mod" for f in root_files):
        project_structure = "go"
    
    # Extract code samples from markdown files
    code_samples = []
    for doc in doc_files:
        if doc["name"].endswith((".md", ".markdown")):
            # Simple regex to extract code blocks from markdown
            matches = re.findall(r'```(\w*)\n(.*?)\n```', doc["content"], re.DOTALL)
            for lang, code in matches:
                if code.strip():
                    code_samples.append({
                        "language": lang if lang else "text",
                        "code": code.strip(),
                        "source": doc["path"]
                    })
    
    # Assemble repository data
    repo_data = {
        "name": repo_info.get("name", repo),
        "owner": owner,  # Add the owner field
        "full_name": repo_info.get("full_name", f"{owner}/{repo}"),
        "description": repo_info.get("description", ""),
        "readme": {
            "name": "README.md",
            "path": "README.md",
            "content": readme,
            "size": len(readme),
            "format": "markdown"
        },
        "root_files": root_files,
        "src_files": src_files,
        "example_files": example_files,
        "doc_files": doc_files,
        "code_samples": code_samples,
        "project_structure": project_structure
    }
    
    return repo_data

def generate_documentation(repo_url: str) -> List[str]:
    """
    Generate documentation for a GitHub repository
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        List of generated documentation file paths
    """
    try:
        # Parse GitHub URL
        owner, repo = parse_github_url(repo_url)
        logger.info(f"Parsed GitHub URL: {owner}/{repo}")
        
        # Fetch repository data
        logger.info(f"Fetching repository data for {owner}/{repo}")
        repo_data = fetch_repository_data(owner, repo)
        
        # Log repository data information
        logger.info(f"Successfully fetched repository data:")
        logger.info(f"- Root files: {len(repo_data.get('root_files', []))}")
        logger.info(f"- Source files: {len(repo_data.get('src_files', []))}")
        logger.info(f"- Example files: {len(repo_data.get('example_files', []))}")
        logger.info(f"- Documentation files: {len(repo_data.get('doc_files', []))}")
        logger.info(f"- Code samples from markdown: {len(repo_data.get('code_samples', []))}")
        logger.info(f"- Project structure: {repo_data.get('project_structure', 'generic')}")
        
        # Generate documentation
        logger.info("Generating documentation with AI Generator")
        ai_generator = AIGenerator()
        docs_content = ai_generator.generate_docs_content(repo_data)
        logger.info(f"Generated {len(docs_content)} documentation files")
        
        # Write documentation to files
        repo_name = repo_data.get("name", "repository")
        output_dir = f"output/{repo_name}"
        os.makedirs(output_dir, exist_ok=True)
        
        file_paths = []
        
        for filename, content in docs_content.items():
            file_path = os.path.join(output_dir, filename)
            # Write file directly
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            file_paths.append(file_path)
            logger.info(f"Wrote documentation to {file_path}")
        
        # Format markdown files
        format_markdown_files(file_paths)
        
        return file_paths
    except Exception as e:
        logger.error(f"Error generating documentation: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python direct_github_docs.py <github_repo_url>")
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
