"""
Diagrammer Module

This module handles the generation of C4 architecture diagrams using mermaid-cli.
"""

import os
import subprocess
import logging
import tempfile
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('diagrammer')

class Diagrammer:
    """Generator for C4 architecture diagrams"""
    
    def __init__(self):
        """Initialize Diagrammer"""
        # Check if mermaid-cli is installed
        try:
            subprocess.run(["mmdc", "--version"], capture_output=True, check=False)
        except FileNotFoundError:
            logger.warning("mermaid-cli not found. Please install it with 'npm install -g @mermaid-js/mermaid-cli'")
    
    def generate_diagram(self, repo_data: Dict[str, Any], output_dir: str) -> Optional[str]:
        """
        Generate a C4 architecture diagram for a repository
        
        Args:
            repo_data: Repository data
            output_dir: Output directory
            
        Returns:
            Path to generated diagram file or None if generation failed
        """
        try:
            logger.info(f"Generating C4 diagram for {repo_data['owner']}/{repo_data['name']}")
            
            # Create the mermaid diagram definition
            diagram_def = self._create_c4_diagram_definition(repo_data)
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Write diagram definition to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as temp_file:
                temp_file.write(diagram_def)
                temp_file_path = temp_file.name
            
            try:
                # Generate the output file path
                output_path = os.path.join(output_dir, "ARCHITECTURE.png")
                
                # Run mermaid-cli to generate the diagram
                logger.info(f"Running mermaid-cli to generate diagram at {output_path}")
                result = subprocess.run(
                    ["mmdc", "-i", temp_file_path, "-o", output_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if os.path.exists(output_path):
                    logger.info(f"Successfully generated diagram at {output_path}")
                    return output_path
                else:
                    logger.error("Diagram file was not created")
                    logger.error(f"mermaid-cli output: {result.stdout}")
                    logger.error(f"mermaid-cli error: {result.stderr}")
                    return None
            
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running mermaid-cli: {e}")
            logger.error(f"Command output: {e.stdout}")
            logger.error(f"Command error: {e.stderr}")
            return None
        
        except Exception as e:
            logger.error(f"Error generating diagram: {str(e)}", exc_info=True)
            return None
    
    def _create_c4_diagram_definition(self, repo_data: Dict[str, Any]) -> str:
        """
        Create a C4 diagram definition in mermaid syntax
        
        Args:
            repo_data: Repository data
            
        Returns:
            Mermaid diagram definition
        """
        # Extract repository information
        repo_name = repo_data["name"]
        repo_owner = repo_data["owner"]
        
        # Start with diagram header
        diagram = "```mermaid\nC4Context\n"
        
        # Add title
        diagram += f"title System Context diagram for {repo_name}\n\n"
        
        # Add repository as the main system
        diagram += f"Enterprise_Boundary(b0, \"{repo_owner}\") {{\n"
        diagram += f"  System(sys1, \"{repo_name}\", \"A software system\")\n"
        
        # Add components based on directories
        directories = set()
        for file in repo_data.get("src_files", []):
            dir_path = os.path.dirname(file["path"])
            if dir_path and dir_path not in directories:
                directories.add(dir_path)
        
        # If no src_files, use root_files
        if not directories:
            for file in repo_data.get("root_files", []):
                if file["type"] == "dir":
                    directories.add(file["path"])
        
        # Add components
        for i, directory in enumerate(directories, start=1):
            diagram += f"  System_Boundary(c{i}, \"{directory}\") {{\n"
            diagram += f"    Container(app{i}, \"{directory}\", \"Component\")\n"
            diagram += "  }\n"
        
        # Close enterprise boundary
        diagram += "}\n\n"
        
        # Add external dependencies
        if repo_data.get("requirements") and repo_data["requirements"].get("content"):
            # Parse requirements.txt
            requirements = repo_data["requirements"]["content"].split("\n")
            for i, req in enumerate(requirements, start=1):
                req = req.strip()
                if req and not req.startswith("#"):
                    # Extract package name (remove version specifiers)
                    package = req.split("==")[0].split(">=")[0].split("<=")[0].strip()
                    if package:
                        diagram += f"System_Ext(ext{i}, \"{package}\", \"External Dependency\")\n"
                        diagram += f"Rel(sys1, ext{i}, \"depends on\")\n"
        
        # Close diagram
        diagram += "```"
        
        return diagram
