"""
Documentation Writer Module

This module handles writing generated documentation to files.
"""

import os
import logging
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger('github_doc_scanner')

class DocWriter:
    """Writer for documentation files"""
    
    def __init__(self, output_dir: str = "docs"):
        """
        Initialize documentation writer
        
        Args:
            output_dir: Output directory for documentation files
        """
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def write_docs(self, docs_content: Dict[str, str], repo_name: str = None) -> List[str]:
        """
        Write documentation to files
        
        Args:
            docs_content: Dictionary mapping filenames to content
            repo_name: Repository name (optional)
            
        Returns:
            List of written file paths
        """
        written_files = []
        
        # Create repo-specific directory if repo_name is provided
        if repo_name:
            repo_dir = os.path.join(self.output_dir, repo_name.replace("/", "_"))
            os.makedirs(repo_dir, exist_ok=True)
            base_dir = repo_dir
        else:
            base_dir = self.output_dir
        
        # Write each document
        for filename, content in docs_content.items():
            file_path = os.path.join(base_dir, filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Format markdown file if applicable
            if filename.lower().endswith('.md'):
                try:
                    from .markdown_formatter import MarkdownFormatter
                    formatter = MarkdownFormatter()
                    formatter.format_file(file_path)
                    logger.info(f"Formatted markdown file: {filename}")
                except Exception as e:
                    logger.warning(f"Error formatting markdown file {filename}: {str(e)}")
            
            written_files.append(file_path)
        
        return written_files
    
    def write_diagram(self, diagram_content: str, repo_name: str = None) -> str:
        """
        Write diagram to file
        
        Args:
            diagram_content: Diagram content (SVG)
            repo_name: Repository name (optional)
            
        Returns:
            Path to written diagram file
        """
        # Create repo-specific directory if repo_name is provided
        if repo_name:
            repo_dir = os.path.join(self.output_dir, repo_name.replace("/", "_"))
            os.makedirs(repo_dir, exist_ok=True)
            base_dir = repo_dir
        else:
            base_dir = self.output_dir
        
        # Write diagram
        diagram_path = os.path.join(base_dir, "ARCH.svg")
        
        with open(diagram_path, "w", encoding="utf-8") as f:
            f.write(diagram_content)
        
        return diagram_path
