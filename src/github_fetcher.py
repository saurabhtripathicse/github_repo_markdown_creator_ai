"""
GitHub Fetcher Module

This module handles all interactions with the GitHub API, including
parsing URLs, fetching repository contents, and managing rate limits.
"""

import os
import re
import base64
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_fetcher')

# Load environment variables
load_dotenv()

# Constants
MAX_FILE_SIZE = 500 * 1024  # 500 KB (increased from 100 KB)
GITHUB_API_BASE = "https://api.github.com"
RATE_LIMIT_WAIT_TIME = 60  # seconds to wait when rate limited
BINARY_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.pdf', '.zip', '.tar', '.gz', '.exe', '.bin']

class GitHubFetcher:
    """Service for interacting with GitHub API"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub fetcher
        
        Args:
            token: GitHub Personal Access Token for authentication (optional)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.raw",
            "User-Agent": "GitHub-Doc-Scanner"
        }
        
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        
        self.rate_limit_remaining = 60  # Default unauthenticated limit
        self.rate_limit_reset = 0
    
    def parse_url(self, url: str) -> Tuple[str, str]:
        """
        Parse GitHub URL to extract owner and repository name
        
        Args:
            url: GitHub URL
            
        Returns:
            Tuple of (owner, repo_name)
            
        Raises:
            ValueError: If URL is not a valid GitHub repository URL
        """
        # Handle URLs like https://github.com/owner/repo
        if url.startswith(("http://", "https://")):
            parts = url.strip("/").split("/")
            if "github.com" in parts and len(parts) >= 5:
                return parts[-2], parts[-1]
        # Handle format like owner/repo
        elif "/" in url and len(url.split("/")) == 2:
            return url.split("/")
        
        raise ValueError(f"Invalid GitHub URL format: {url}. Expected format: 'https://github.com/owner/repo' or 'owner/repo'")
    
    def _make_request(self, endpoint: str) -> requests.Response:
        """
        Make a request to the GitHub API with rate limit handling
        
        Args:
            endpoint: API endpoint (without base URL)
            
        Returns:
            Response object
            
        Raises:
            requests.HTTPError: If request fails after retries
        """
        url = f"{GITHUB_API_BASE}/{endpoint.lstrip('/')}"
        
        # Check if we're near rate limit
        if self.rate_limit_remaining < 5:
            current_time = time.time()
            if current_time < self.rate_limit_reset:
                wait_time = self.rate_limit_reset - current_time + 1
                logger.info(f"Rate limit nearly exhausted. Waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)
        
        # Make the request
        logger.info(f"Making request to: {url}")
        response = requests.get(url, headers=self.headers)
        
        # Update rate limit info
        self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 60))
        self.rate_limit_reset = int(response.headers.get("X-RateLimit-Reset", 0))
        
        # Handle rate limiting
        if response.status_code == 403 and "rate limit" in response.text.lower():
            if not self.token:
                raise ValueError("GitHub API rate limit exceeded. Add GITHUB_TOKEN to your environment variables for higher limits.")
            
            reset_time = self.rate_limit_reset
            wait_time = reset_time - time.time() + 1
            
            if wait_time > 0:
                logger.info(f"Rate limit exceeded. Waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)
                # Retry the request
                return self._make_request(endpoint)
        
        # Raise exception for other errors
        response.raise_for_status()
        
        return response
    
    def fetch_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fetch basic repository information
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with repository information
        """
        logger.info(f"Fetching repository info for {owner}/{repo}")
        response = self._make_request(f"repos/{owner}/{repo}")
        
        try:
            repo_info = response.json()
            return {
                "name": repo_info.get("name", ""),
                "full_name": repo_info.get("full_name", ""),
                "description": repo_info.get("description", ""),
                "default_branch": repo_info.get("default_branch", "main"),
                "stars": repo_info.get("stargazers_count", 0),
                "forks": repo_info.get("forks_count", 0),
                "language": repo_info.get("language", ""),
                "topics": repo_info.get("topics", []),
                "homepage": repo_info.get("homepage", ""),
                "created_at": repo_info.get("created_at", ""),
                "updated_at": repo_info.get("updated_at", ""),
                "license": repo_info.get("license", {}).get("name", "")
            }
        except json.JSONDecodeError:
            logger.error(f"Failed to parse repository info response: {response.text[:200]}")
            return {
                "name": repo,
                "full_name": f"{owner}/{repo}",
                "description": "",
                "default_branch": "main"
            }
    
    def fetch_readme(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fetch README file from repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with README content and metadata
            
        Raises:
            requests.HTTPError: If README cannot be fetched
        """
        logger.info(f"Fetching README for {owner}/{repo}")
        try:
            response = self._make_request(f"repos/{owner}/{repo}/readme")
            
            if response.headers.get("Content-Type") == "application/vnd.github.raw":
                content = response.text
            else:
                # Fall back to decoding base64 content
                try:
                    data = response.json()
                    content = base64.b64decode(data.get("content", "")).decode("utf-8")
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON from response: {response.text[:100]}...")
                    content = ""
                except Exception as e:
                    logger.warning(f"Error decoding README content: {str(e)}")
                    content = ""
            
            # Extract README format
            readme_format = "markdown"  # Default
            if "README.md" in response.url:
                readme_format = "markdown"
            elif "README.rst" in response.url:
                readme_format = "rst"
            elif "README.txt" in response.url:
                readme_format = "text"
            
            return {
                "name": "README.md",
                "path": "README.md",
                "content": content[:MAX_FILE_SIZE] if len(content) > MAX_FILE_SIZE else content,
                "truncated": len(content) > MAX_FILE_SIZE,
                "size": len(content),
                "format": readme_format
            }
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                # README not found, return empty content
                logger.warning(f"README not found for {owner}/{repo}")
                return {
                    "name": "README.md",
                    "path": "README.md",
                    "content": "",
                    "truncated": False,
                    "size": 0,
                    "format": "markdown"
                }
            logger.error(f"Error fetching README: {str(e)}")
            raise
    
    def fetch_directory(self, owner: str, repo: str, path: str = "", branch: str = None) -> List[Dict[str, Any]]:
        """
        Fetch directory contents from repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Directory path (optional)
            branch: Branch name (optional)
            
        Returns:
            List of directory contents with metadata
            
        Raises:
            requests.HTTPError: If directory cannot be fetched
        """
        endpoint = f"repos/{owner}/{repo}/contents/{path}"
        if branch:
            endpoint += f"?ref={branch}"
            
        logger.info(f"Fetching directory contents: {endpoint}")
        response = self._make_request(endpoint)
        
        try:
            contents = response.json()
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON from response: {response.text[:100]}...")
            return []
        
        # Ensure contents is a list
        if not isinstance(contents, list):
            logger.warning(f"Expected list of contents, got: {type(contents)}")
            return []
        
        return [{
            "name": item.get("name", ""),
            "path": item.get("path", ""),
            "type": item.get("type", ""),
            "size": item.get("size", 0),
            "download_url": item.get("download_url", ""),
            "url": item.get("url", "")
        } for item in contents]
    
    def fetch_file_content(self, owner: str, repo: str, path: str, branch: str = None) -> Dict[str, Any]:
        """
        Fetch file content from repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            branch: Branch name (optional)
            
        Returns:
            Dictionary with file content and metadata
            
        Raises:
            requests.HTTPError: If file cannot be fetched
        """
        endpoint = f"repos/{owner}/{repo}/contents/{path}"
        if branch:
            endpoint += f"?ref={branch}"
            
        logger.info(f"Fetching file content: {endpoint}")
        
        # Skip binary files
        if any(path.lower().endswith(ext) for ext in BINARY_EXTENSIONS):
            logger.info(f"Skipping binary file: {path}")
            return {
                "name": path.split("/")[-1],
                "path": path,
                "content": "",
                "truncated": False,
                "size": 0,
                "binary": True
            }
        
        try:
            response = self._make_request(endpoint)
            
            if response.headers.get("Content-Type") == "application/vnd.github.raw":
                content = response.text
            else:
                # Fall back to decoding base64 content
                try:
                    data = response.json()
                    if isinstance(data, dict) and "content" in data:
                        content = base64.b64decode(data["content"]).decode("utf-8")
                    else:
                        return {
                            "name": path.split("/")[-1],
                            "path": path,
                            "content": "",
                            "truncated": False,
                            "size": 0,
                            "binary": False
                        }
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON from response: {response.text[:100]}...")
                    return {
                        "name": path.split("/")[-1],
                        "path": path,
                        "content": "",
                        "truncated": False,
                        "size": 0,
                        "binary": False
                    }
                except Exception as e:
                    logger.warning(f"Error decoding file content: {str(e)}")
                    return {
                        "name": path.split("/")[-1],
                        "path": path,
                        "content": "",
                        "truncated": False,
                        "size": 0,
                        "binary": False
                    }
            
            # Check if file is likely binary
            is_binary = self._is_binary_content(content)
            
            return {
                "name": path.split("/")[-1],
                "path": path,
                "content": "" if is_binary else (content[:MAX_FILE_SIZE] if len(content) > MAX_FILE_SIZE else content),
                "truncated": len(content) > MAX_FILE_SIZE,
                "size": len(content),
                "binary": is_binary
            }
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"File not found: {path}")
                return {
                    "name": path.split("/")[-1],
                    "path": path,
                    "content": "",
                    "truncated": False,
                    "size": 0,
                    "binary": False
                }
            logger.error(f"Error fetching file content: {str(e)}")
            raise
    
    def _is_binary_content(self, content: str) -> bool:
        """
        Check if content is likely binary
        
        Args:
            content: File content
            
        Returns:
            True if content is likely binary
        """
        # Check for null bytes or high concentration of non-printable characters
        if not content:
            return False
            
        # Sample the first 1000 characters
        sample = content[:1000]
        non_printable = sum(1 for c in sample if ord(c) < 32 and c not in '\n\r\t')
        
        # If more than 10% are non-printable, consider it binary
        return non_printable > len(sample) * 0.1
    
    def fetch_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fetch repository contents
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with repository contents
            
        Raises:
            requests.HTTPError: If repository cannot be fetched
        """
        logger.info(f"Fetching repository: {owner}/{repo}")
        
        # Get repository info
        repo_info = self.fetch_repository_info(owner, repo)
        default_branch = repo_info.get("default_branch", "main")
        
        # Get README
        readme = self.fetch_readme(owner, repo)
        
        # Get root directory contents
        root_contents = self.fetch_directory(owner, repo, branch=default_branch)
        
        # Identify important directories with expanded patterns
        src_dir = next((item for item in root_contents if item["name"].lower() in ["src", "source", "lib", "app", "core"] and item["type"] == "dir"), None)
        test_dir = next((item for item in root_contents if item["name"].lower() in ["test", "tests", "testing", "unit_tests"] and item["type"] == "dir"), None)
        examples_dir = next((item for item in root_contents if item["name"].lower() in ["examples", "example", "samples", "demos", "demo", "tutorial", "tutorials", "quickstart"] and item["type"] == "dir"), None)
        docs_dir = next((item for item in root_contents if item["name"].lower() in ["docs", "documentation", "doc", "guide", "guides"] and item["type"] == "dir"), None)
        
        # Get requirements file with expanded file patterns
        requirements_file = next((item for item in root_contents if item["name"] in ["requirements.txt", "setup.py", "pyproject.toml", "package.json", "Pipfile", "Pipfile.lock", "environment.yml", "conda.yml"] and item["type"] == "file"), None)
        requirements = None
        if requirements_file:
            requirements = self.fetch_file_content(owner, repo, requirements_file["path"], branch=default_branch)
        
        # Get root Python files with expanded file types
        root_files = []
        for item in root_contents:
            if item["type"] == "file" and (item["name"].endswith((".py", ".js", ".ts", ".jsx", ".tsx")) or item["name"] in ["README.md", "LICENSE", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md"]):
                file_content = self.fetch_file_content(owner, repo, item["path"], branch=default_branch)
                if not file_content.get("binary", False):
                    root_files.append(file_content)
        
        # Get source files
        src_files = []
        if src_dir:
            try:
                src_contents = self.fetch_directory(owner, repo, src_dir["path"], branch=default_branch)
                for item in src_contents[:15]:  # Increased from 10 to 15 items
                    if item["type"] == "file" and item["name"].endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                        file_content = self.fetch_file_content(owner, repo, item["path"], branch=default_branch)
                        if not file_content.get("binary", False):
                            src_files.append(file_content)
            except Exception as e:
                logger.warning(f"Error fetching source files: {str(e)}")
        
        # Get test files
        test_files = []
        if test_dir:
            try:
                test_contents = self.fetch_directory(owner, repo, test_dir["path"], branch=default_branch)
                for item in test_contents[:5]:  # Limit to first 5 items
                    if item["type"] == "file" and item["name"].endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                        file_content = self.fetch_file_content(owner, repo, item["path"], branch=default_branch)
                        if not file_content.get("binary", False):
                            test_files.append(file_content)
            except Exception as e:
                logger.warning(f"Error fetching test files: {str(e)}")
        
        # Get example files - enhanced to fetch more examples and search subdirectories
        example_files = []
        if examples_dir:
            try:
                example_contents = self.fetch_directory(owner, repo, examples_dir["path"], branch=default_branch)
                # Process example files
                for item in example_contents[:10]:  # Increased from 5 to 10
                    if item["type"] == "file" and item["name"].endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".ipynb")):
                        file_content = self.fetch_file_content(owner, repo, item["path"], branch=default_branch)
                        if not file_content.get("binary", False):
                            example_files.append(file_content)
                    # Also check subdirectories for examples
                    elif item["type"] == "dir":
                        try:
                            subdir_contents = self.fetch_directory(owner, repo, item["path"], branch=default_branch)
                            for subitem in subdir_contents[:5]:
                                if subitem["type"] == "file" and subitem["name"].endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".ipynb")):
                                    file_content = self.fetch_file_content(owner, repo, subitem["path"], branch=default_branch)
                                    if not file_content.get("binary", False):
                                        example_files.append(file_content)
                        except Exception as e:
                            logger.warning(f"Error fetching example subdirectory: {str(e)}")
            except Exception as e:
                logger.warning(f"Error fetching example files: {str(e)}")
        
        # If no examples directory found, look for examples in other common locations
        if not examples_dir or len(example_files) == 0:
            # Check for examples in docs directory
            if docs_dir:
                try:
                    docs_contents = self.fetch_directory(owner, repo, docs_dir["path"], branch=default_branch)
                    for item in docs_contents:
                        if item["type"] == "dir" and item["name"].lower() in ["examples", "samples", "demos", "tutorial", "tutorials", "quickstart"]:
                            subdir_contents = self.fetch_directory(owner, repo, item["path"], branch=default_branch)
                            for subitem in subdir_contents[:5]:
                                if subitem["type"] == "file" and subitem["name"].endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".ipynb")):
                                    file_content = self.fetch_file_content(owner, repo, subitem["path"], branch=default_branch)
                                    if not file_content.get("binary", False):
                                        example_files.append(file_content)
                except Exception as e:
                    logger.warning(f"Error searching for examples in docs: {str(e)}")
            
            # Look for notebooks directory
            notebooks_dir = next((item for item in root_contents if item["name"].lower() in ["notebooks", "notebook", "jupyter", "colab"] and item["type"] == "dir"), None)
            if notebooks_dir:
                try:
                    notebook_contents = self.fetch_directory(owner, repo, notebooks_dir["path"], branch=default_branch)
                    for item in notebook_contents[:5]:
                        if item["type"] == "file" and item["name"].endswith((".ipynb", ".md")):
                            file_content = self.fetch_file_content(owner, repo, item["path"], branch=default_branch)
                            if not file_content.get("binary", False):
                                example_files.append(file_content)
                except Exception as e:
                    logger.warning(f"Error fetching notebook files: {str(e)}")
        
        # Get documentation files
        doc_files = []
        if docs_dir:
            try:
                doc_contents = self.fetch_directory(owner, repo, docs_dir["path"], branch=default_branch)
                for item in doc_contents[:8]:  # Increased from 5 to 8
                    if item["type"] == "file" and item["name"].endswith((".md", ".rst", ".txt", ".html")):
                        file_content = self.fetch_file_content(owner, repo, item["path"], branch=default_branch)
                        if not file_content.get("binary", False):
                            doc_files.append(file_content)
            except Exception as e:
                logger.warning(f"Error fetching documentation files: {str(e)}")
        
        # Combine all data
        return {
            "owner": owner,
            "name": repo,
            "full_name": f"{owner}/{repo}",
            "description": repo_info.get("description", ""),
            "default_branch": default_branch,
            "stars": repo_info.get("stars", 0),
            "forks": repo_info.get("forks", 0),
            "language": repo_info.get("language", ""),
            "topics": repo_info.get("topics", []),
            "homepage": repo_info.get("homepage", ""),
            "license": repo_info.get("license", ""),
            "readme": readme,
            "requirements": requirements,
            "root_files": root_files,
            "src_files": src_files,
            "test_files": test_files,
            "example_files": example_files,
            "doc_files": doc_files
        }
