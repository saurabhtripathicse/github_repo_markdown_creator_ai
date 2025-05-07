"""
Main FastAPI Application

This module defines the FastAPI application and API endpoints for generating
documentation from GitHub repositories.
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from .github_fetcher import GitHubFetcher
from .ai_generator import AIGenerator
from .doc_writer import DocWriter
from .diagrammer import Diagrammer
from .web_scraper import WebScraper
from .markdown_formatter import MarkdownFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_doc_scanner')

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="GitHub Documentation Generator",
    description="Generate documentation from GitHub repositories",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request and response models
class GenerateDocsRequest(BaseModel):
    repo_url: str
    diagram: bool = False
    web_search: bool = False  # New parameter to enable web search

class GenerateDocsResponse(BaseModel):
    ok: bool
    files: List[str] = []
    message: str

class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 5

class WebSearchResponse(BaseModel):
    ok: bool
    content: str
    message: str

@app.get("/health")
async def health_check() -> Dict[str, bool]:
    """
    Health check endpoint
    
    Returns:
        Dictionary with status
    """
    logger.info("Health check requested")
    return {"ok": True}

@app.post("/web-search", response_model=WebSearchResponse)
async def web_search_and_scrape_code(request: WebSearchRequest) -> Dict[str, Any]:
    """
    Search the web for code examples related to the query
    
    Args:
        request: Request with search query and max results
        
    Returns:
        Response with status and markdown-formatted search results
        
    Raises:
        HTTPException: If web search fails
    """
    try:
        logger.info(f"Web search requested for query: {request.query}")
        
        # Initialize web scraper
        web_scraper = WebScraper()
        
        # Search and scrape code snippets
        markdown_content = web_scraper.search_and_scrape(
            query=request.query,
            max_results=request.max_results
        )
        
        return {
            "ok": True,
            "content": markdown_content,
            "message": f"Successfully searched for: {request.query}"
        }
    
    except Exception as e:
        logger.error(f"Error during web search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during web search: {str(e)}")

@app.post("/generate-docs", response_model=GenerateDocsResponse)
async def generate_docs(request: GenerateDocsRequest) -> Dict[str, Any]:
    """
    Generate documentation from a GitHub repository
    
    Args:
        request: Request with repository URL and diagram flag
        
    Returns:
        Response with status and generated files
        
    Raises:
        HTTPException: If documentation generation fails
    """
    try:
        logger.info(f"Documentation generation requested for: {request.repo_url}")
        
        # Parse GitHub URL
        github_fetcher = GitHubFetcher()
        try:
            owner, repo = github_fetcher.parse_url(request.repo_url)
            logger.info(f"Parsed GitHub URL: {owner}/{repo}")
        except ValueError as e:
            logger.error(f"Invalid GitHub URL: {request.repo_url}")
            raise HTTPException(status_code=400, detail=f"Invalid GitHub URL: {str(e)}")
        
        # Fetch repository data
        try:
            logger.info(f"Fetching repository data for {owner}/{repo}")
            repo_data = github_fetcher.fetch_repository(owner, repo)
            logger.info(f"Successfully fetched repository data with {len(repo_data.get('root_files', []))} root files")
        except Exception as e:
            logger.error(f"Error fetching repository: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching repository: {str(e)}")
        
        # Perform web search if requested
        if request.web_search:
            try:
                logger.info(f"Performing web search for {owner}/{repo}")
                web_scraper = WebScraper()
                search_query = f"{owner} {repo} code examples documentation"
                web_search_results = web_scraper.search_and_scrape(search_query)
                
                # Add web search results to repository data
                repo_data["web_search_results"] = web_search_results
                logger.info("Web search results added to repository data")
            except Exception as e:
                logger.warning(f"Error during web search: {str(e)}")
                # Continue without web search results if it fails
        
        # Generate documentation
        try:
            logger.info("Generating documentation content")
            ai_generator = AIGenerator()
            docs_content = ai_generator.generate_docs_content(repo_data)
            logger.info(f"Generated {len(docs_content)} documentation files")
        except Exception as e:
            logger.error(f"Error generating documentation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating documentation: {str(e)}")
        
        # Write documentation to files
        try:
            logger.info("Writing documentation to files")
            doc_writer = DocWriter()
            output_dir = f"docs/{owner}_{repo}"
            file_paths = doc_writer.write_docs(docs_content, output_dir)
            logger.info(f"Documentation written to {output_dir}")
            
            # Format markdown files
            try:
                from .markdown_formatter import format_markdown_files
                logger.info("Formatting markdown files according to best practices")
                format_results = format_markdown_files(output_dir, recursive=True)
                formatted_count = sum(1 for success in format_results.values() if success)
                logger.info(f"Formatted {formatted_count}/{len(format_results)} markdown files successfully")
            except Exception as e:
                logger.warning(f"Error formatting markdown files: {str(e)}")
                # Continue without formatting if it fails
        except Exception as e:
            logger.error(f"Error writing documentation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error writing documentation: {str(e)}")
        
        # Generate diagram if requested
        if request.diagram:
            try:
                logger.info("Generating C4 diagram")
                diagrammer = Diagrammer()
                diagram_path = diagrammer.generate_diagram(repo_data, output_dir)
                if diagram_path:
                    file_paths.append(diagram_path)
                    logger.info(f"Diagram generated at {diagram_path}")
            except Exception as e:
                logger.warning(f"Error generating diagram: {str(e)}")
                # Continue without diagram if it fails
        
        # Return success response
        logger.info(f"Documentation generation completed successfully for {request.repo_url}")
        return {
            "ok": True,
            "files": file_paths,
            "message": f"Successfully generated documentation for {request.repo_url}"
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Log and convert other exceptions to HTTP exceptions
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: \n\n{str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run("src.main:app", host=host, port=port, reload=True)
