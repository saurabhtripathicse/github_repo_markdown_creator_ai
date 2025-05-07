#!/usr/bin/env python3
"""
Enhanced Flask Documentation Generator

This script generates comprehensive documentation specifically for Flask repositories
with more detailed usage examples and increased token limits.
"""

import os
import sys
import logging
import requests
import re
import time
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhanced_flask_docs')

# Load environment variables
load_dotenv()

# Constants
MAX_FILE_SIZE = 100000  # Maximum file size to process (100 KB)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

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
    example_dirs = ['examples', 'sample', 'demo', 'tutorial', 'test', 'quickstart']
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
                # Determine language from file extension
                ext = os.path.splitext(path)[1].lower()
                language = "python" if ext == ".py" else \
                           "javascript" if ext in [".js", ".jsx"] else \
                           "typescript" if ext in [".ts", ".tsx"] else \
                           "java" if ext == ".java" else \
                           "ruby" if ext == ".rb" else \
                           "go" if ext == ".go" else \
                           "text"
                
                example_files.append({
                    "name": os.path.basename(path),
                    "path": path,
                    "content": content,
                    "size": len(content),
                    "language": language
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
        "owner": owner,
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

def generate_enhanced_usage_doc(repo_data: Dict[str, Any]) -> str:
    """
    Generate enhanced usage documentation with more code examples
    
    Args:
        repo_data: Repository data
        
    Returns:
        Generated usage documentation
    """
    logger.info(f"Generating enhanced usage documentation for {repo_data['owner']}/{repo_data['name']}")
    
    # Prepare system prompt
    system_prompt = """
    You are a senior AI technical writer generating a comprehensive USAGE.md file for Flask.
    Your task is to create detailed, practical usage examples and instructions for Flask.
    
    Use markdown with proper formatting:
    - Use a single `#` for the document title
    - Use `##`, `###` for section headers (don't skip levels)
    - Add blank lines before and after headings, lists, code blocks, and tables
    - Use triple-backtick code blocks with language specified
    - Avoid trailing whitespace and punctuation in headings
    
    Include the following sections:
    
    ### Installation
    Step-by-step installation instructions with different options (pip, pipenv, poetry).
    
    ### Basic Usage
    Simple examples to get started quickly, including:
    - Creating a basic Flask application
    - Routing and URL building
    - Handling HTTP methods (GET, POST)
    - Rendering templates
    - Working with static files
    
    ### Advanced Usage
    More complex examples and use cases, including:
    - Blueprints for application structure
    - Flask extensions and how to use them
    - Working with databases (SQLAlchemy)
    - Authentication and authorization
    - RESTful API development
    - Error handling and logging
    - Testing Flask applications
    
    ### Configuration
    Available configuration options and how to use them, including:
    - Configuration from files
    - Environment variables
    - Instance folders
    - Application factories
    
    ### Deployment
    Options for deploying Flask applications, including:
    - Development server
    - Production deployment options (Gunicorn, uWSGI)
    - Containerization with Docker
    - Cloud deployment (Heroku, AWS, etc.)
    
    ### Troubleshooting
    Common issues and their solutions.
    
    Focus on practical, runnable examples. Use actual code from the repository when available.
    Be comprehensive and include detailed code examples with proper imports and context.
    Make sure the examples are complete and can be run directly by users.
    """
    
    # Prepare user prompt
    user_prompt = f"Repository: {repo_data['owner']}/{repo_data['name']}\n\n"
    
    # Add repository description
    if repo_data.get("description"):
        user_prompt += f"Description: {repo_data['description']}\n\n"
    
    # Add README content
    if repo_data.get("readme") and repo_data["readme"].get("content"):
        readme_content = repo_data["readme"]["content"]
        user_prompt += f"README Content:\n\n{readme_content}\n\n"
    
    # Extract code examples from repository
    code_examples = []
    
    # Look for example files
    if repo_data.get("example_files"):
        for example in repo_data["example_files"]:
            if example.get("content"):
                code_examples.append({
                    "name": example.get("name", ""),
                    "source": example.get("path", ""),
                    "code": example.get("content", ""),
                    "language": example.get("language", "python")
                })
    
    # Look for examples in README
    if repo_data.get("readme") and repo_data["readme"].get("content"):
        readme_content = repo_data["readme"]["content"]
        # Extract code blocks from markdown
        code_blocks = re.findall(r'```([a-zA-Z0-9]*)?\n([\s\S]*?)```', readme_content)
        for i, (language, code) in enumerate(code_blocks):
            if code.strip():
                code_examples.append({
                    "name": f"Example from README #{i+1}",
                    "source": "README.md",
                    "code": code.strip(),
                    "language": language if language else "python"
                })
    
    # Look for examples in documentation files
    if repo_data.get("doc_files"):
        for doc in repo_data["doc_files"]:
            if "quickstart" in doc.get("path", "").lower() or "tutorial" in doc.get("path", "").lower():
                if doc.get("content"):
                    # Extract code blocks from markdown or rst
                    code_blocks = re.findall(r'```([a-zA-Z0-9]*)?\n([\s\S]*?)```', doc.get("content", ""))
                    for i, (language, code) in enumerate(code_blocks):
                        if code.strip():
                            code_examples.append({
                                "name": f"Example from {doc.get('name', '')} #{i+1}",
                                "source": doc.get("path", ""),
                                "code": code.strip(),
                                "language": language if language else "python"
                            })
    
    # Extract import statements from examples to help with import paths
    import_statements = []
    for example in code_examples:
        if example.get("code"):
            # Extract import lines using regex
            imports = re.findall(r'^(?:from|import)\s+[a-zA-Z0-9_\.]+(?:\s+import\s+[a-zA-Z0-9_\.,\s]+)?', 
                                example["code"], re.MULTILINE)
            for imp in imports:
                if imp not in import_statements:
                    import_statements.append(imp)
    
    if import_statements:
        user_prompt += "Import Statements Found in Examples:\n\n"
        for imp in import_statements:
            user_prompt += f"```python\n{imp}\n```\n\n"
    
    # Add code examples
    if code_examples:
        user_prompt += "Code Examples:\n\n"
        for i, example in enumerate(code_examples[:15]):  # Include more examples (up to 15)
            user_prompt += f"Example {i+1} from {example['source']}: {example['name']}\n\n"
            user_prompt += f"```{example.get('language', 'python')}\n"
            user_prompt += example["code"]
            user_prompt += "\n```\n\n"
    
    # Add source files that might be useful for examples
    if repo_data.get("src_files"):
        user_prompt += "Key Source Files:\n\n"
        for file in repo_data["src_files"][:10]:  # Limit to first 10 files
            if "app.py" in file["path"] or "routes.py" in file["path"] or "views.py" in file["path"]:
                user_prompt += f"File: {file['path']}\n\n"
                user_prompt += "```python\n"
                user_prompt += file["content"][:3000]  # Include more content
                user_prompt += "\n```\n\n"
    
    # Generate usage documentation
    try:
        # Use GPT-4 with higher token limit
        response = client.chat.completions.create(
            model="gpt-4o",  # Using GPT-4o for better quality
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=4000  # Increased token limit for more comprehensive documentation
        )
        
        usage_doc = response.choices[0].message.content.strip()
        return f"# Usage Guide\n\n{usage_doc}"
    except Exception as e:
        logger.error(f"Error generating enhanced usage documentation: {str(e)}")
        return f"# Error Generating Usage Documentation\n\nAn error occurred while generating the usage documentation: {str(e)}"

def generate_flask_documentation(repo_url: str) -> None:
    """
    Generate enhanced Flask documentation
    
    Args:
        repo_url: GitHub repository URL
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
        
        # Generate enhanced usage documentation
        logger.info("Generating enhanced usage documentation")
        usage_doc = generate_enhanced_usage_doc(repo_data)
        
        # Write documentation to file
        output_dir = f"output/{repo_data.get('name', 'flask')}"
        os.makedirs(output_dir, exist_ok=True)
        
        usage_file_path = os.path.join(output_dir, "USAGE.md")
        with open(usage_file_path, 'w', encoding='utf-8') as f:
            f.write(usage_doc)
        
        logger.info(f"Wrote enhanced usage documentation to {usage_file_path}")
        print(f"\nSuccessfully generated enhanced usage documentation for {repo_url}")
        print(f"Documentation file: {usage_file_path}")
        
    except Exception as e:
        logger.error(f"Error generating Flask documentation: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python enhanced_flask_docs.py <github_repo_url>")
        sys.exit(1)
        
    repo_url = sys.argv[1]
    print(f"Generating enhanced Flask documentation for {repo_url}...")
    
    generate_flask_documentation(repo_url)
