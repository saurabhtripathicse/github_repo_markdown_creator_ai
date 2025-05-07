"""
Web Scraper Module

This module provides functionality to search the web and scrape code snippets
from relevant webpages to enhance documentation generation.
"""

import logging
import re
import time
from typing import Dict, List, Any, Optional, Tuple
import requests
from bs4 import BeautifulSoup

# Try to import duckduckgo_search, but make it optional
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    logging.warning("duckduckgo_search package not available. Web search functionality will be limited.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('web_scraper')

class WebScraper:
    """Web search and code scraping service"""
    
    def __init__(self):
        """Initialize web scraper"""
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.headers = {
            "User-Agent": self.user_agent
        }
        # Sites to avoid due to anti-bot protection or terms of service issues
        self.blacklisted_domains = [
            "stackoverflow.com/login", 
            "github.com/login",
            "linkedin.com",
            "facebook.com",
            "twitter.com"
        ]
        
        # Initialize search engine if available
        if DDGS_AVAILABLE:
            self.search_engine = DDGS()
        else:
            self.search_engine = None
    
    def search_and_scrape(self, query: str, max_results: int = 5) -> str:
        """
        Search the web for the query and scrape code snippets from the results
        
        Args:
            query: Search query
            max_results: Maximum number of search results to process
            
        Returns:
            Markdown-formatted string with code snippets
        """
        logger.info(f"Searching for: {query}")
        
        # Check if web search functionality is available
        if not DDGS_AVAILABLE:
            logger.warning("Full web search functionality is not available (duckduckgo_search package not installed)")
            return f"# Web Search Results for: {query}\n\n" + \
                   "Note: Full web search functionality is not available. " + \
                   "To enable full web search, install the duckduckgo-search package:\n\n" + \
                   "```\npip install duckduckgo-search\n```\n\n" + \
                   "Here are some GitHub links that might be helpful:\n\n" + \
                   f"- [GitHub Code Search for {query}](https://github.com/search?q={query.replace(' ', '+')}&type=code)\n" + \
                   f"- [GitHub Repository Search for {query}](https://github.com/search?q={query.replace(' ', '+')}&type=repositories)\n"
        
        # Search for relevant URLs
        try:
            search_results = self._search_web(query, max_results)
            if not search_results:
                return f"No search results found for query: {query}"
        except Exception as e:
            logger.error(f"Error searching the web: {str(e)}")
            return f"Error searching the web: {str(e)}"
        
        # Process each search result
        markdown_output = f"# Web Search Results for: {query}\n\n"
        
        # Add note about limited functionality if duckduckgo_search is not available
        if not DDGS_AVAILABLE:
            markdown_output += "**Note:** Limited web search functionality is available.\n\n"
        
        for result in search_results:
            url = result.get('href', '')
            title = result.get('title', 'Untitled')
            
            # Skip blacklisted domains
            if any(domain in url.lower() for domain in self.blacklisted_domains):
                logger.info(f"Skipping blacklisted domain: {url}")
                continue
            
            try:
                # Scrape code snippets from the URL
                code_snippets = self._scrape_code_snippets(url)
                
                # Add URL and title to markdown
                markdown_output += f"## [{title}]({url})\n\n"
                
                if code_snippets:
                    # Add up to 3 code snippets
                    for i, (code, language) in enumerate(code_snippets[:3]):
                        markdown_output += f"### Code Snippet {i+1}\n\n"
                        markdown_output += f"```{language}\n{code}\n```\n\n"
                else:
                    markdown_output += "No code snippets found on this page.\n\n"
                
                # Add separator
                markdown_output += "---\n\n"
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                markdown_output += f"Error processing URL: {url} - {str(e)}\n\n"
                markdown_output += "---\n\n"
        
        return markdown_output
    
    def _search_web(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Search the web using DuckDuckGo or fallback to a simple implementation
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title and URL
        """
        try:
            # Add "code example" to the query to bias towards code-containing pages
            enhanced_query = f"{query} code example"
            
            if DDGS_AVAILABLE and self.search_engine:
                # Use DuckDuckGo search if available
                results = list(self.search_engine.text(enhanced_query, max_results=max_results))
                logger.info(f"Found {len(results)} search results using DuckDuckGo")
                return results
            else:
                # Fallback implementation - return GitHub search results
                logger.info("Using fallback search implementation (GitHub only)")
                fallback_results = [
                    {
                        "title": f"GitHub: {query} code examples",
                        "href": f"https://github.com/search?q={query.replace(' ', '+')}&type=code"
                    },
                    {
                        "title": f"GitHub: {query} repositories",
                        "href": f"https://github.com/search?q={query.replace(' ', '+')}&type=repositories"
                    }
                ]
                return fallback_results[:max_results]
        except Exception as e:
            logger.error(f"Error during web search: {str(e)}")
            # Return empty results instead of raising an exception
            return []
    
    def _scrape_code_snippets(self, url: str) -> List[Tuple[str, str]]:
        """
        Scrape code snippets from a webpage
        
        Args:
            url: URL to scrape
            
        Returns:
            List of tuples containing (code_snippet, language)
        """
        logger.info(f"Scraping code snippets from: {url}")
        
        try:
            # Fetch the webpage
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract code snippets
            code_snippets = []
            
            # Look for <pre> tags
            pre_tags = soup.find_all('pre')
            for pre in pre_tags:
                # Check if there's a nested <code> tag
                code_tag = pre.find('code')
                if code_tag:
                    # Try to determine the language
                    language = "text"
                    class_attr = code_tag.get('class', [])
                    for cls in class_attr:
                        if cls.startswith(('language-', 'lang-')):
                            language = cls.split('-')[1]
                            break
                    
                    code_snippets.append((code_tag.get_text(), language))
                else:
                    # Use the pre tag directly
                    code_snippets.append((pre.get_text(), "text"))
            
            # If no <pre> tags with code, look for standalone <code> tags
            if not code_snippets:
                code_tags = soup.find_all('code')
                for code in code_tags:
                    # Only include substantial code blocks (more than 1 line)
                    code_text = code.get_text()
                    if '\n' in code_text and len(code_text) > 50:
                        language = "text"
                        class_attr = code.get('class', [])
                        for cls in class_attr:
                            if cls.startswith(('language-', 'lang-')):
                                language = cls.split('-')[1]
                                break
                        
                        code_snippets.append((code_text, language))
            
            # Clean up code snippets
            cleaned_snippets = []
            for code, language in code_snippets:
                # Remove excessive whitespace
                code = re.sub(r'\n\s*\n', '\n\n', code)
                code = code.strip()
                
                # Skip if too short
                if len(code) < 20:
                    continue
                
                # Truncate if too long
                if len(code) > 1500:
                    code = code[:1500] + "\n\n[... truncated ...]"
                
                cleaned_snippets.append((code, language))
            
            logger.info(f"Found {len(cleaned_snippets)} code snippets")
            return cleaned_snippets
            
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error scraping code snippets from {url}: {str(e)}")
            return []
