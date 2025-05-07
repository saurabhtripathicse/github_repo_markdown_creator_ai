#!/usr/bin/env python3
"""
Command-line script for generating documentation from GitHub repositories.
This script allows users to provide a GitHub repository URL and generate documentation.
"""

import os
import sys
import argparse
import requests
import json
import time
import subprocess
from urllib.parse import urlparse

def is_valid_github_url(url):
    """Check if a URL is a valid GitHub repository URL"""
    try:
        parsed = urlparse(url)
        return (parsed.netloc == 'github.com' and 
                len(parsed.path.strip('/').split('/')) >= 2)
    except:
        return False

def ensure_server_running():
    """Ensure the FastAPI server is running"""
    try:
        print("Checking if server is already running...")
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("Server is already running.")
            return None
    except:
        print("Server is not running. Starting the server...")
        # Start the server in the background
        server_process = subprocess.Popen(
            ["uvicorn", "src.main:app", "--reload"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for the server to start
        print("Waiting for server to start...")
        for i in range(10):  # Try for 10 seconds
            try:
                print(f"Attempt {i+1}/10 to connect to server...")
                response = requests.get("http://localhost:8000/health")
                if response.status_code == 200:
                    print("Server started successfully.")
                    return server_process
            except Exception as e:
                print(f"Connection attempt {i+1} failed: {str(e)}")
                # Check if there's any output from the server process
                if server_process.poll() is not None:
                    # Server process has terminated
                    stdout, stderr = server_process.communicate()
                    print("Server process terminated unexpectedly!")
                    print("STDOUT:", stdout.decode('utf-8', errors='replace') if stdout else "None")
                    print("STDERR:", stderr.decode('utf-8', errors='replace') if stderr else "None")
                    break
                time.sleep(1)
        
        # If we get here, server failed to start
        print("Failed to start server. Checking server process output...")
        if server_process.poll() is None:
            # Server is still running but not responding
            print("Server process is running but not responding. Terminating...")
            server_process.terminate()
            stdout, stderr = server_process.communicate()
        else:
            # Server has already terminated
            stdout, stderr = server_process.communicate()
        
        print("Server process output:")
        print("STDOUT:", stdout.decode('utf-8', errors='replace') if stdout else "None")
        print("STDERR:", stderr.decode('utf-8', errors='replace') if stderr else "None")
        print("Failed to start server. Please check the logs.")
        sys.exit(1)

def generate_documentation(repo_url, include_diagram=False, enable_web_search=False):
    """
    Generate documentation for a GitHub repository
    
    Args:
        repo_url: URL of the GitHub repository
        include_diagram: Whether to generate a C4 architecture diagram
        enable_web_search: Whether to enable web search for additional code examples
    
    Returns:
        Path to the overview file if successful, None otherwise
    """
    print(f"Generating documentation for {repo_url}...")
    if enable_web_search:
        print("Web search enabled: Will search for additional code examples and context")
    
    try:
        payload = {
            "repo_url": repo_url,
            "diagram": include_diagram,
            "web_search": enable_web_search
        }
        
        print("Sending request to documentation generator...")
        response = requests.post(
            "http://localhost:8000/generate-docs",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("\nDocumentation generated successfully!")
                print("Generated files:")
                for file_path in result.get("files", []):
                    print(f"- {file_path}")
                
                # Find and return the overview file path
                for file_path in result.get("files", []):
                    if "OVERVIEW.md" in file_path:
                        return file_path
            else:
                print("\nError in response:", result)
        else:
            print(f"\nError: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error generating documentation: {str(e)}")
    
    return None

def web_search(query, max_results=5):
    """
    Perform a web search for code examples
    
    Args:
        query: Search query
        max_results: Maximum number of search results to process
    
    Returns:
        True if successful, False otherwise
    """
    print(f"Searching for: {query}...")
    
    try:
        payload = {
            "query": query,
            "max_results": max_results
        }
        
        response = requests.post(
            "http://localhost:8000/web-search",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("\nSearch completed successfully!")
                print("\nSearch Results:")
                print(result.get("content"))
                return True
            else:
                print("\nError in response:", result)
        else:
            print(f"\nError: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error during web search: {str(e)}")
    
    return False

def open_file(file_path):
    """Open a file with the default application"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    if sys.platform == "darwin":  # macOS
        subprocess.call(["open", file_path])
    elif sys.platform == "win32":  # Windows
        os.startfile(file_path)
    else:  # Linux
        subprocess.call(["xdg-open", file_path])

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate documentation for GitHub repositories")
    parser.add_argument("repo_url", nargs="?", default="https://github.com/openai/openai-agents-python",
                        help="GitHub repository URL (default: openai/openai-agents-python)")
    parser.add_argument("--diagram", "-d", action="store_true",
                        help="Generate C4 architecture diagram")
    parser.add_argument("--web-search", "-w", action="store_true",
                        help="Enable web search for additional code examples and context")
    parser.add_argument("--search-only", "-s", metavar="QUERY",
                        help="Perform only a web search with the given query (no documentation generation)")
    parser.add_argument("--max-results", "-m", type=int, default=5,
                        help="Maximum number of search results to process (default: 5)")
    parser.add_argument("--no-open", action="store_true",
                        help="Don't open the documentation after generation")
    
    args = parser.parse_args()
    
    # Ensure the server is running
    server_process = ensure_server_running()
    
    try:
        # Handle search-only mode
        if args.search_only:
            web_search(args.search_only, args.max_results)
            return 0
        
        # Validate GitHub URL for documentation generation
        if not is_valid_github_url(args.repo_url):
            print(f"Error: Invalid GitHub repository URL: {args.repo_url}")
            print("Expected format: https://github.com/owner/repo")
            return 1
        
        # Generate documentation
        overview_path = generate_documentation(
            args.repo_url, 
            args.diagram, 
            args.web_search
        )
        
        # Open the documentation if requested
        if overview_path and not args.no_open:
            print(f"\nOpening documentation: {overview_path}")
            open_file(overview_path)
        
        return 0
    
    finally:
        # Clean up server process if we started it
        if server_process:
            print("Stopping server...")
            server_process.terminate()

if __name__ == "__main__":
    sys.exit(main())
