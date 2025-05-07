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

# Patterns for identifying example files and directories
EXAMPLE_PATTERNS = [
    r'example', r'sample', r'demo', r'tutorial', 
    r'quickstart', r'getting[-_]?started'
]
EXAMPLE_DIRECTORIES = ['examples', 'samples', 'demos', 'tutorials']

# Patterns for identifying documentation files
DOC_PATTERNS = [r'doc', r'guide', r'tutorial', r'howto', r'faq', r'reference']
DOC_DIRECTORIES = ['docs', 'documentation', 'wiki', 'guides']

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
    
    def _make_request(self, endpoint: str, retries: int = 3, backoff_factor: float = 1.5, raw_content: bool = False) -> requests.Response:
        """
        Make a request to the GitHub API with rate limit handling and retries
        
        Args:
            endpoint: API endpoint (without base URL)
            retries: Number of retries for failed requests
            backoff_factor: Exponential backoff factor for retries
            
        Returns:
            Response object
            
        Raises:
            requests.HTTPError: If request fails after retries
        """
        # Use raw content URL if specified
        if raw_content and 'contents/' in endpoint and '?ref=' in endpoint:
            # Extract owner, repo, path and ref from endpoint
            parts = endpoint.split('/')
            owner_idx = parts.index('repos') + 1 if 'repos' in parts else 0
            if owner_idx > 0 and len(parts) > owner_idx + 2:
                owner = parts[owner_idx]
                repo = parts[owner_idx + 1]
                path_start = endpoint.find('contents/') + 9
                path_end = endpoint.find('?ref=')
                if path_start > 0 and path_end > path_start:
                    path = endpoint[path_start:path_end]
                    ref = endpoint[path_end + 5:]
                    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
                    logger.info(f"Using raw content URL: {url}")
                else:
                    url = f"{GITHUB_API_BASE}/{endpoint.lstrip('/')}"  
            else:
                url = f"{GITHUB_API_BASE}/{endpoint.lstrip('/')}"  
        else:
            url = f"{GITHUB_API_BASE}/{endpoint.lstrip('/')}"
        
        # Check if we're near rate limit
        if self.rate_limit_remaining < 5:
            current_time = time.time()
            if current_time < self.rate_limit_reset:
                wait_time = self.rate_limit_reset - current_time + 1
                logger.info(f"Rate limit nearly exhausted. Waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)
        
        # Implement retry logic with exponential backoff
        retry_count = 0
        while retry_count <= retries:
            try:
                # Make the request
                logger.info(f"Making request to: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)
                
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
                        retry_count += 1
                        continue
                
                # Check for successful response
                response.raise_for_status()
                return response
                
            except (requests.RequestException, ConnectionError, TimeoutError) as e:
                retry_count += 1
                if retry_count > retries:
                    logger.error(f"Failed after {retries} retries: {str(e)}")
                    raise
                
                # Exponential backoff
                wait_time = backoff_factor ** retry_count
                logger.warning(f"Request failed: {str(e)}. Retrying in {wait_time:.1f} seconds... (Attempt {retry_count}/{retries})")
                time.sleep(wait_time)
                # Continue to next retry iteration
        
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
    
    def fetch_raw_content(self, owner: str, repo: str, path: str, branch: str = None) -> str:
        """
        Fetch raw file content directly from GitHub's raw content URL
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            branch: Branch name (optional)
            
        Returns:
            Raw file content as string
        """
        if not branch:
            # Get default branch if not specified
            repo_info = self.fetch_repository_info(owner, repo)
            branch = repo_info.get("default_branch", "main")
            
        # Construct raw content URL
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
        logger.info(f"Fetching raw content from: {raw_url}")
        
        try:
            # Make direct request to raw content URL
            headers = {"Accept": "text/plain"}
            if self.token:
                headers["Authorization"] = f"token {self.token}"
                
            response = requests.get(raw_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Error fetching raw content for {path}: {str(e)}")
            return ""
    
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
            # Try to fetch raw content directly first using our dedicated method
            content = self.fetch_raw_content(owner, repo, path, branch)
            
            # If we got content, return it
            if content:
                if len(content) > MAX_FILE_SIZE:
                    content = content[:MAX_FILE_SIZE] + "\n[Content truncated due to size]"
                return {
                    "name": path.split("/")[-1],
                    "path": path,
                    "content": content,
                    "truncated": len(content) > MAX_FILE_SIZE,
                    "size": len(content),
                    "binary": self._is_binary_content(content[:1000])
                }
                
            # If raw content fetch failed, fall back to API request
            logger.warning(f"Raw content fetch failed for {path}. Falling back to API.")
            response = self._make_request(endpoint)
            
            # Process the API response
            if response.headers.get("Content-Type") == "application/vnd.github.raw":
                content = response.text
            else:
                # Fall back to decoding base64 content
                try:
                    # First check if we can parse the JSON response
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse JSON from response for {path}. Status code: {response.status_code}")
                        # Try to get content directly as text if JSON parsing fails
                        if response.status_code == 200:
                            content = response.text
                            if len(content) > MAX_FILE_SIZE:
                                content = content[:MAX_FILE_SIZE] + "\n[Content truncated due to size]" 
                            return {
                                "name": path.split("/")[-1],
                                "path": path,
                                "content": content,
                                "truncated": len(content) > MAX_FILE_SIZE,
                                "size": len(content),
                                "binary": self._is_binary_content(content[:1000])
                            }
                        else:
                            return {
                                "name": path.split("/")[-1],
                                "path": path,
                                "content": "",
                                "truncated": False,
                                "size": 0,
                                "binary": False
                            }
                    
                    # Process the JSON data if parsing succeeded
                    if isinstance(data, dict) and "content" in data:
                        try:
                            content = base64.b64decode(data["content"]).decode("utf-8")
                        except Exception as e:
                            logger.warning(f"Error decoding base64 content for {path}: {str(e)}")
                            content = f"[Error decoding content: {str(e)}]"
                    else:
                        logger.warning(f"No content field in response for {path}")
                        return {
                            "name": path.split("/")[-1],
                            "path": path,
                            "content": "",
                            "truncated": False,
                            "size": 0,
                            "binary": False
                        }
                except Exception as e:
                    logger.warning(f"Error processing content for {path}: {str(e)}")
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
    
    def fetch_repository_tree(self, owner: str, repo: str, branch: str = "main") -> List[Dict[str, Any]]:
        """
        Fetch the entire repository tree recursively using Git Trees API
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            
        Returns:
            List of tree items (files and directories)
        """
        try:
            logger.info(f"Fetching repository tree for {owner}/{repo} (branch: {branch})")
            
            # Get the reference to the branch
            try:
                ref_response = self._make_request(f"repos/{owner}/{repo}/git/refs/heads/{branch}")
                ref_data = ref_response.json()
                commit_sha = ref_data["object"]["sha"]
            except Exception as e:
                logger.warning(f"Error fetching branch reference: {str(e)}. Trying default branch.")
                # Try with master if main fails
                try:
                    alt_branch = "master" if branch == "main" else "main"
                    ref_response = self._make_request(f"repos/{owner}/{repo}/git/refs/heads/{alt_branch}")
                    ref_data = ref_response.json()
                    commit_sha = ref_data["object"]["sha"]
                    logger.info(f"Using alternative branch: {alt_branch}")
                except Exception:
                    # Last resort: get the default branch from repo info
                    repo_info = self.fetch_repository_info(owner, repo)
                    default_branch = repo_info.get("default_branch", "main")
                    ref_response = self._make_request(f"repos/{owner}/{repo}/git/refs/heads/{default_branch}")
                    ref_data = ref_response.json()
                    commit_sha = ref_data["object"]["sha"]
                    logger.info(f"Using repository default branch: {default_branch}")
            
            # Get the tree with recursive=1
            tree_response = self._make_request(f"repos/{owner}/{repo}/git/trees/{commit_sha}?recursive=1")
            tree_data = tree_response.json()
            
            if tree_data.get("truncated", False):
                logger.warning("Repository tree was truncated due to size limitations")
            
            return tree_data.get("tree", [])
            
        except Exception as e:
            logger.error(f"Error fetching repository tree: {str(e)}")
            return []
    
    def extract_code_from_markdown(self, markdown_content: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from markdown content
        
        Args:
            markdown_content: Markdown content to extract code blocks from
            
        Returns:
            List of dictionaries with language and code
        """
        # Match code blocks with language specification: ```python
        code_block_pattern = r'```([a-zA-Z0-9_+\-]+)?\n([\s\S]*?)\n```'
        
        code_samples = []
        for match in re.finditer(code_block_pattern, markdown_content):
            language = match.group(1) or "text"
            code = match.group(2)
            
            # Skip very short code blocks (likely not examples)
            if len(code.strip()) < 10:
                continue
                
            code_samples.append({
                "language": language,
                "code": code,
                "source": "markdown"
            })
        
        return code_samples
    
    def identify_example_files(self, tree_data: List[Dict[str, Any]], owner: str, repo: str, branch: str) -> List[Dict[str, Any]]:
        """
        Identify example files from repository tree data
        
        Args:
            tree_data: Repository tree data
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            
        Returns:
            List of example files with content
        """
        logger.info(f"Identifying example files for {owner}/{repo}")
        example_files = []
        example_paths = []
        
        # First pass: identify example files by path
        for item in tree_data:
            if item["type"] != "blob":  # Skip non-file items
                continue
                
            path = item["path"].lower()
            
            # Check if path matches example patterns
            if any(re.search(pattern, path, re.IGNORECASE) for pattern in EXAMPLE_PATTERNS):
                example_paths.append(item["path"])
                
            # Check if file is in an example directory
            path_parts = path.split("/")
            if any(part in EXAMPLE_DIRECTORIES for part in path_parts):
                example_paths.append(item["path"])
            
            # Check if file is a common example file type
            if path.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.rb', '.go')):
                if 'example' in path or 'sample' in path or 'demo' in path:
                    example_paths.append(item["path"])
        
        # Second pass: fetch content for identified example files
        for path in example_paths:
            # Skip binary files
            if any(path.endswith(ext) for ext in BINARY_EXTENSIONS):
                continue
                
            try:
                file_response = self._make_request(f"repos/{owner}/{repo}/contents/{path}?ref={branch}")
                
                if file_response.headers.get("Content-Type") == "application/vnd.github.raw":
                    content = file_response.text
                else:
                    # Fall back to decoding base64 content
                    try:
                        data = file_response.json()
                        if data.get("size", 0) > MAX_FILE_SIZE:
                            content = f"[File too large to include: {data.get('size')} bytes]"
                        else:
                            content = base64.b64decode(data.get("content", "")).decode("utf-8")
                    except Exception as e:
                        logger.warning(f"Error decoding content for {path}: {str(e)}")
                        content = ""
                
                # Skip if content is binary
                if self._is_binary_content(content):
                    continue
                
                # Determine file language from extension
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
                    "type": "file",
                    "size": len(content),
                    "content": content,
                    "language": language
                })
                
            except Exception as e:
                logger.warning(f"Error fetching example file {path}: {str(e)}")
        
        return example_files
    
    def identify_documentation_files(self, tree_data: List[Dict[str, Any]], owner: str, repo: str, branch: str) -> List[Dict[str, Any]]:
        """
        Identify documentation files from repository tree data
        
        Args:
            tree_data: Repository tree data
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            
        Returns:
            List of documentation files with content
        """
        logger.info(f"Identifying documentation files for {owner}/{repo}")
        doc_files = []
        doc_paths = []
        
        # First pass: identify documentation files by path
        for item in tree_data:
            if item["type"] != "blob":  # Skip non-file items
                continue
                
            path = item["path"].lower()
            
            # Skip binary files
            if any(path.endswith(ext) for ext in BINARY_EXTENSIONS):
                continue
            
            # Check if file is a markdown file
            if path.endswith('.md') and not path.endswith('README.md'):
                doc_paths.append(item["path"])
                continue
            
            # Check if path matches documentation patterns
            if any(re.search(pattern, path, re.IGNORECASE) for pattern in DOC_PATTERNS):
                doc_paths.append(item["path"])
                continue
                
            # Check if file is in a documentation directory
            path_parts = path.split("/")
            if any(part in DOC_DIRECTORIES for part in path_parts):
                doc_paths.append(item["path"])
                continue
        
        # Second pass: fetch content for identified documentation files
        for path in doc_paths:
            try:
                file_response = self._make_request(f"repos/{owner}/{repo}/contents/{path}?ref={branch}")
                
                if file_response.headers.get("Content-Type") == "application/vnd.github.raw":
                    content = file_response.text
                else:
                    # Fall back to decoding base64 content
                    try:
                        data = file_response.json()
                        if data.get("size", 0) > MAX_FILE_SIZE:
                            content = f"[File too large to include: {data.get('size')} bytes]"
                        else:
                            content = base64.b64decode(data.get("content", "")).decode("utf-8")
                    except Exception as e:
                        logger.warning(f"Error decoding content for {path}: {str(e)}")
                        content = ""
                
                # Skip if content is binary
                if self._is_binary_content(content):
                    continue
                
                doc_files.append({
                    "name": os.path.basename(path),
                    "path": path,
                    "type": "file",
                    "size": len(content),
                    "content": content
                })
                
            except Exception as e:
                logger.warning(f"Error fetching documentation file {path}: {str(e)}")
        
        return doc_files
    
    def fetch_root_files(self, owner: str, repo: str, branch: str = "main") -> List[Dict[str, Any]]:
        """
        Fetch files from the root directory of the repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            
        Returns:
            List of root files with content
        """
        logger.info(f"Fetching root files for {owner}/{repo}")
        root_files = []
        
        try:
            # Use the repository tree to identify root files
            tree_data = self.fetch_repository_tree(owner, repo, branch)
            root_paths = [item["path"] for item in tree_data if "/" not in item["path"] and item["type"] == "blob"]
            
            # Skip binary files and large files
            root_paths = [path for path in root_paths if not any(path.endswith(ext) for ext in BINARY_EXTENSIONS)]
            
            # Fetch content for each root file
            for path in root_paths:
                try:
                    file_response = self._make_request(f"repos/{owner}/{repo}/contents/{path}?ref={branch}")
                    
                    if file_response.headers.get("Content-Type") == "application/vnd.github.raw":
                        content = file_response.text
                    else:
                        # Fall back to decoding base64 content
                        try:
                            data = file_response.json()
                            if data.get("size", 0) > MAX_FILE_SIZE:
                                content = f"[File too large to include: {data.get('size')} bytes]"
                            else:
                                content = base64.b64decode(data.get("content", "")).decode("utf-8")
                        except Exception as e:
                            logger.warning(f"Error decoding content for {path}: {str(e)}")
                            content = ""
                    
                    # Skip if content is binary
                    if self._is_binary_content(content):
                        continue
                    
                    root_files.append({
                        "name": os.path.basename(path),
                        "path": path,
                        "type": "file",
                        "size": len(content),
                        "content": content
                    })
                    
                except Exception as e:
                    logger.warning(f"Error fetching root file {path}: {str(e)}")
            
            return root_files
            
        except Exception as e:
            logger.error(f"Error fetching root files: {str(e)}")
            return []
    
    def fetch_src_files(self, owner: str, repo: str, branch: str = "main") -> List[Dict[str, Any]]:
        """
        Fetch source files from the repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            
        Returns:
            List of source files with content
        """
        logger.info(f"Fetching source files for {owner}/{repo}")
        src_files = []
        
        try:
            # Use the repository tree to identify source files
            tree_data = self.fetch_repository_tree(owner, repo, branch)
            
            # Look for common source directories
            src_dirs = ["src", "lib", "app", "core"]
            src_paths = []
            
            for item in tree_data:
                if item["type"] != "blob":
                    continue
                    
                path = item["path"]
                
                # Skip binary files
                if any(path.endswith(ext) for ext in BINARY_EXTENSIONS):
                    continue
                
                # Check if file is in a source directory
                if any(path.startswith(f"{src_dir}/") for src_dir in src_dirs):
                    src_paths.append(path)
                    continue
                
                # Check if file has a source file extension
                if path.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.rb', '.go')):
                    # Skip test files
                    if 'test' not in path and 'spec' not in path:
                        src_paths.append(path)
            
            # Limit to a reasonable number of source files
            src_paths = src_paths[:10]  # Limit to 10 source files
            
            # Fetch content for each source file
            for path in src_paths:
                try:
                    file_response = self._make_request(f"repos/{owner}/{repo}/contents/{path}?ref={branch}")
                    
                    if file_response.headers.get("Content-Type") == "application/vnd.github.raw":
                        content = file_response.text
                    else:
                        # Fall back to decoding base64 content
                        try:
                            data = file_response.json()
                            if data.get("size", 0) > MAX_FILE_SIZE:
                                content = f"[File too large to include: {data.get('size')} bytes]"
                            else:
                                content = base64.b64decode(data.get("content", "")).decode("utf-8")
                        except Exception as e:
                            logger.warning(f"Error decoding content for {path}: {str(e)}")
                            content = ""
                    
                    # Skip if content is binary
                    if self._is_binary_content(content):
                        continue
                    
                    src_files.append({
                        "name": os.path.basename(path),
                        "path": path,
                        "type": "file",
                        "size": len(content),
                        "content": content
                    })
                    
                except Exception as e:
                    logger.warning(f"Error fetching source file {path}: {str(e)}")
            
            return src_files
            
        except Exception as e:
            logger.error(f"Error fetching source files: {str(e)}")
            return []
    
    def fetch_requirements(self, owner: str, repo: str, branch: str = "main") -> Optional[Dict[str, Any]]:
        """
        Fetch requirements file from the repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            
        Returns:
            Dictionary with requirements file information or None if not found
        """
        logger.info(f"Fetching requirements file for {owner}/{repo}")
        
        # Common requirements file names
        req_file_names = [
            "requirements.txt",
            "Pipfile",
            "pyproject.toml",
            "setup.py",
            "package.json",
            "Gemfile",
            "go.mod",
            "Cargo.toml"
        ]
        
        try:
            # Use the repository tree to check for requirements files
            tree_data = self.fetch_repository_tree(owner, repo, branch)
            
            # Check for requirements files in root directory
            for item in tree_data:
                if item["type"] != "blob":
                    continue
                    
                path = item["path"]
                name = os.path.basename(path)
                
                # Skip files not in root directory
                if "/" in path:
                    continue
                
                # Check if file is a requirements file
                if name in req_file_names:
                    try:
                        file_response = self._make_request(f"repos/{owner}/{repo}/contents/{path}?ref={branch}")
                        
                        if file_response.headers.get("Content-Type") == "application/vnd.github.raw":
                            content = file_response.text
                        else:
                            # Fall back to decoding base64 content
                            try:
                                data = file_response.json()
                                if data.get("size", 0) > MAX_FILE_SIZE:
                                    content = f"[File too large to include: {data.get('size')} bytes]"
                                else:
                                    content = base64.b64decode(data.get("content", "")).decode("utf-8")
                            except Exception as e:
                                logger.warning(f"Error decoding content for {path}: {str(e)}")
                                content = ""
                        
                        # Skip if content is binary
                        if self._is_binary_content(content):
                            continue
                        
                        return {
                            "name": name,
                            "path": path,
                            "type": "file",
                            "size": len(content),
                            "content": content
                        }
                        
                    except Exception as e:
                        logger.warning(f"Error fetching requirements file {path}: {str(e)}")
            
            # Check for requirements files in subdirectories
            for item in tree_data:
                if item["type"] != "blob":
                    continue
                    
                path = item["path"]
                name = os.path.basename(path)
                
                # Only check files in subdirectories
                if "/" not in path:
                    continue
                
                # Check if file is a requirements file
                if name == "requirements.txt":
                    try:
                        file_response = self._make_request(f"repos/{owner}/{repo}/contents/{path}?ref={branch}")
                        
                        if file_response.headers.get("Content-Type") == "application/vnd.github.raw":
                            content = file_response.text
                        else:
                            # Fall back to decoding base64 content
                            try:
                                data = file_response.json()
                                if data.get("size", 0) > MAX_FILE_SIZE:
                                    content = f"[File too large to include: {data.get('size')} bytes]"
                                else:
                                    content = base64.b64decode(data.get("content", "")).decode("utf-8")
                            except Exception as e:
                                logger.warning(f"Error decoding content for {path}: {str(e)}")
                                content = ""
                        
                        # Skip if content is binary
                        if self._is_binary_content(content):
                            continue
                        
                        return {
                            "name": name,
                            "path": path,
                            "type": "file",
                            "size": len(content),
                            "content": content
                        }
                        
                    except Exception as e:
                        logger.warning(f"Error fetching requirements file {path}: {str(e)}")
            
            # No requirements file found
            return None
            
        except Exception as e:
            logger.error(f"Error fetching requirements file: {str(e)}")
            return None
    
    def detect_project_structure(self, tree_data: List[Dict[str, Any]], root_files: List[Dict[str, Any]]) -> str:
        """
        Detect the project structure type based on repository contents
        
        Args:
            tree_data: Repository tree data
            root_files: Root files with content
            
        Returns:
            Project structure type (e.g., python_package, node_js, etc.)
        """
        logger.info("Detecting project structure type")
        
        # Extract all file paths
        file_paths = [item["path"] for item in tree_data if item["type"] == "blob"]
        root_file_names = [file["name"] for file in root_files]
        
        # Check for Python package
        if "setup.py" in root_file_names or "pyproject.toml" in root_file_names:
            return "python_package"
        
        # Check for Python project without package structure
        python_files = [path for path in file_paths if path.endswith(".py")]
        if len(python_files) > 3:  # More than 3 Python files
            return "python_project"
        
        # Check for Node.js project
        if "package.json" in root_file_names:
            # Check if it's a React project
            if any("react" in file.get("content", "").lower() for file in root_files if file["name"] == "package.json"):
                return "react_project"
            return "node_js"
        
        # Check for Java project
        if "pom.xml" in root_file_names or "build.gradle" in root_file_names:
            return "java_project"
        
        # Check for Ruby project
        if "Gemfile" in root_file_names:
            return "ruby_project"
        
        # Check for Go project
        if "go.mod" in root_file_names:
            return "go_project"
        
        # Check for Rust project
        if "Cargo.toml" in root_file_names:
            return "rust_project"
        
        # Check for C# project
        if any(path.endswith(".csproj") for path in file_paths):
            return "csharp_project"
        
        # Default to generic
        return "generic"
    
    def fetch_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fetch repository data including README, root files, and source files
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with repository data
        """
        logger.info(f"Fetching repository data for {owner}/{repo}")
        
        # Get repository info
        repo_info = self.fetch_repository_info(owner, repo)
        default_branch = repo_info.get("default_branch", "main")
        
        # Get README
        readme = self.fetch_readme(owner, repo)
        
        # Get the complete repository tree (more efficient than multiple API calls)
        repo_tree = self.fetch_repository_tree(owner, repo, default_branch)
        
        # Extract code samples from README and other markdown files
        code_samples_from_md = []
        if readme and readme.get("content"):
            code_samples_from_md = self.extract_code_from_markdown(readme["content"])
        
        # Get root files
        root_files = self.fetch_root_files(owner, repo, default_branch)
        
        # Get source files
        src_files = self.fetch_src_files(owner, repo, default_branch)
        
        # Get example files using the repository tree
        example_files = self.identify_example_files(repo_tree, owner, repo, default_branch)
        
        # Get documentation files
        doc_files = self.identify_documentation_files(repo_tree, owner, repo, default_branch)
        
        # Get requirements file if it exists
        requirements = self.fetch_requirements(owner, repo, default_branch)
        
        # Detect project structure type
        project_structure = self.detect_project_structure(repo_tree, root_files)
        
        # Combine data
        repo_data = {
            "owner": owner,
            "name": repo,
            "full_name": f"{owner}/{repo}",
            "description": repo_info.get("description", ""),
            "default_branch": default_branch,
            "stars": repo_info.get("stars", 0),
            "forks": repo_info.get("forks", 0),
            "language": repo_info.get("language", ""),
            "topics": repo_info.get("topics", []),
            "readme": readme,
            "root_files": root_files,
            "src_files": src_files,
            "example_files": example_files,
            "doc_files": doc_files,
            "code_samples": code_samples_from_md,
            "project_structure": project_structure,
            "repo_tree": repo_tree
        }
        
        # Add requirements if found
        if requirements:
            repo_data["requirements"] = requirements
        
        return repo_data
