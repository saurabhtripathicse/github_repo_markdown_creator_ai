"""
AI Generator Module

This module handles the generation of documentation using OpenAI's API.
It creates overview, modules documentation, usage examples, and dependencies documentation.
"""

import os
import re
import json
import time
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_generator')

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Constants
MAX_PROMPT_CHARS = 4000  # Maximum characters to include in a prompt
TOKEN_LIMIT_THRESHOLD = 15000  # Token threshold for summarization approach

class AIGenerator:
    """Generator for AI-powered documentation"""
    
    def __init__(self):
        """Initialize AI Generator"""
        # Verify API key is set
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    def _make_completion_request(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """
        Make a request to OpenAI's API
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            temperature: Temperature for generation (0.0-1.0)
            
        Returns:
            Generated text
        """
        logger.info(f"Making OpenAI request with system prompt: {system_prompt[:100]}...")
        logger.info(f"User prompt length: {len(user_prompt)} characters")
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o for better quality
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=3000  # Increased token limit for more comprehensive documentation
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"Received response of length: {len(content)} characters")
            return content
        except Exception as e:
            logger.error(f"Error making OpenAI request: {str(e)}")
            raise
    
    def _truncate_content(self, content: str, max_chars: int = 1500) -> str:
        """
        Truncate content to a maximum number of characters
        
        Args:
            content: Content to truncate
            max_chars: Maximum number of characters
            
        Returns:
            Truncated content
        """
        if len(content) <= max_chars:
            return content
        
        return content[:max_chars] + "...[truncated]"
    
    def _analyze_project_structure(self, repo_data: Dict[str, Any]) -> str:
        """
        Analyze project structure
        
        Args:
            repo_data: Repository data
            
        Returns:
            Project structure analysis
        """
        structure = "Project Structure Analysis:\n\n"
        
        # Analyze directory structure
        if repo_data.get("repo_tree"):
            dirs = set()
            for item in repo_data.get("repo_tree", []):
                path = item.get("path", "")
                if "/" in path:
                    dirs.add(path.split("/")[0])
                else:
                    dirs.add(path)
            
            # Filter out files and sort directories
            main_dirs = sorted([d for d in dirs if not any(d.endswith(ext) for ext in [".py", ".js", ".md", ".txt", ".json", ".toml", ".yml", ".yaml"])])
            
            structure += "Main Directories:\n"
            for directory in main_dirs:
                structure += f"- {directory}/\n"
            structure += "\n"
        
        return structure
    
    def _process_code_samples(self, repo_data: Dict[str, Any]) -> str:
        """
        Process code samples from repository
        
        Args:
            repo_data: Repository data
            
        Returns:
            Processed code samples
        """
        code_samples = "Code Samples:\n\n"
        
        # Extract code samples from example files
        if repo_data.get("example_files"):
            for i, example in enumerate(repo_data.get("example_files", [])[:3]):  # Limit to 3 examples
                if example.get("content"):
                    code_samples += f"Example {i+1} from {example.get('path', '')}:\n\n"
                    code_samples += f"```\n{self._truncate_content(example.get('content', ''))}\n```\n\n"
        
        return code_samples
    
    def generate_docs_content(self, repo_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate documentation content for a repository
        
        Args:
            repo_data: Repository data
            
        Returns:
            Dictionary mapping filenames to content
        """
        logger.info(f"Generating documentation for {repo_data['owner']}/{repo_data['name']}")
        
        docs_content = {}
        
        try:
            # Generate overview documentation
            docs_content["OVERVIEW.md"] = self.generate_overview_doc(repo_data)
            
            # Generate modules documentation
            docs_content["MODULES.md"] = self.generate_modules_doc(repo_data)
            
            # Generate usage documentation
            docs_content["USAGE.md"] = self.generate_usage_doc(repo_data)
            
            # Generate dependencies documentation
            docs_content["DEPENDENCIES.md"] = self.generate_dependencies_doc(repo_data)
            
            return docs_content
        except Exception as e:
            logger.error(f"Error generating documentation: {str(e)}")
            raise
    
    def generate_overview_doc(self, repo_data: Dict[str, Any]) -> str:
        """
        Generate overview documentation
        
        Args:
            repo_data: Repository data
            
        Returns:
            Generated overview documentation
        """
        logger.info(f"Generating overview documentation for {repo_data['owner']}/{repo_data['name']}")
        
        # Prepare system prompt
        system_prompt = """
        You are a documentation expert. Your task is to analyze the provided GitHub repository
        information and create a concise, informative OVERVIEW.md file.
        
        The overview should include:
        
        1. Project Purpose: Explain what the project does and why it exists.
        2. Key Features and Capabilities: List the main functionalities.
        3. High-Level Architecture: Describe the overall structure and components.
        4. Target Audience and Use Cases: Explain who would use this and how.
        5. Notable Technologies and Frameworks: Mention key dependencies.
        
        Use markdown formatting with clear section headers (## for main sections).
        Be factual, concise, and focus on the most important aspects of the project.
        If information is missing, make reasonable inferences based on file names, 
        directory structure, and available content.
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
        
        # Add root files
        if repo_data.get("root_files"):
            user_prompt += "Root Files:\n\n"
            for file in repo_data["root_files"]:
                user_prompt += f"- {file['name']}\n"
            user_prompt += "\n"
        
        # Add project structure analysis
        project_structure = self._analyze_project_structure(repo_data)
        user_prompt += project_structure
        
        # Generate overview documentation
        try:
            overview_doc = self._make_completion_request(system_prompt, user_prompt)
            return overview_doc
        except Exception as e:
            logger.error(f"Error generating overview documentation: {str(e)}")
            return f"# Error Generating Overview\n\nAn error occurred while generating the overview documentation: {str(e)}"
    
    def generate_modules_doc(self, repo_data: Dict[str, Any]) -> str:
        """
        Generate modules documentation
        
        Args:
            repo_data: Repository data
            
        Returns:
            Generated modules documentation
        """
        logger.info(f"Generating modules documentation for {repo_data['owner']}/{repo_data['name']}")
        
        # Estimate tokens based on source files
        estimated_tokens = sum(len(file.get("content", "")) // 4 for file in repo_data.get("src_files", []))
        logger.info(f"Estimated tokens for repository: {estimated_tokens}")
        
        # Use summarization approach for large repositories
        if estimated_tokens > TOKEN_LIMIT_THRESHOLD:
            return self._generate_modules_doc_summarized(repo_data)
        
        # Prepare system prompt
        system_prompt = """
        You are a senior AI technical writer generating a MODULES.md file for a GitHub repository.
        Your task is to document the key modules, classes, and functions in the codebase.
        
        Use markdown with proper formatting:
        - Use a single `#` for the document title
        - Use `##`, `###` for section headers (don't skip levels)
        - Use triple-backtick code blocks with language specified
        - Use tables when appropriate for structured information
        
        For each module, include:
        - Purpose and responsibility
        - Key classes/functions with brief descriptions
        - Example usage (if available from the repository)
        - Dependencies on other modules
        
        Focus on the most important modules first. Be concise but comprehensive.
        Use actual examples from the repository when available.
        """
        
        # Prepare user prompt
        user_prompt = f"Repository: {repo_data['owner']}/{repo_data['name']}\n\n"
        
        # Add repository description
        if repo_data.get("description"):
            user_prompt += f"Description: {repo_data['description']}\n\n"
        
        # Add source files
        if repo_data.get("src_files"):
            user_prompt += "Source Files:\n\n"
            for file in repo_data["src_files"][:10]:  # Limit to first 10 files
                user_prompt += f"- {file['path']}\n"
                
                # Add file content if available and not too large
                content = file.get("content", "")
                if content and len(content) <= 1500:  # Limit to 1500 characters
                    language = "python" if file['path'].endswith(".py") else \
                               "javascript" if file['path'].endswith(".js") else \
                               "typescript" if file['path'].endswith(".ts") else "text"
                    user_prompt += f"```{language}\n{content[:1500]}\n```\n\n"
        
        # Add code samples
        code_samples = self._process_code_samples(repo_data)
        if code_samples:
            user_prompt += f"\n{code_samples}\n"
        
        # Add project structure analysis
        project_structure = self._analyze_project_structure(repo_data)
        user_prompt += project_structure
        
        # Generate modules documentation
        try:
            modules_doc = self._make_completion_request(system_prompt, user_prompt)
            return f"# Modules Documentation\n\n{modules_doc}"
        except Exception as e:
            logger.error(f"Error generating modules documentation: {str(e)}")
            return f"# Error Generating Modules Documentation\n\nAn error occurred while generating the modules documentation: {str(e)}"
    
    def _generate_modules_doc_summarized(self, repo_data: Dict[str, Any]) -> str:
        """
        Generate modules documentation using a summarization approach for large repositories
        
        Args:
            repo_data: Repository data
            
        Returns:
            Generated modules documentation
        """
        logger.info(f"Generating summarized modules documentation for {repo_data['owner']}/{repo_data['name']}")
        
        # Prepare system prompt
        system_prompt = """
        You are a senior AI technical writer generating a MODULES.md file for a large GitHub repository.
        Your task is to provide a high-level overview of the architecture and code organization.
        
        Focus on the main components and their relationships rather than detailed documentation of each file.
        Use markdown with proper formatting and structure your response with clear sections.
        """
        
        # Prepare user prompt
        user_prompt = f"Repository: {repo_data['owner']}/{repo_data['name']}\n\n"
        
        # Add repository description
        if repo_data.get("description"):
            user_prompt += f"Description: {repo_data['description']}\n\n"
        
        # Add directory structure
        if repo_data.get("repo_tree"):
            user_prompt += "Directory Structure:\n\n"
            dirs = set()
            for item in repo_data["repo_tree"]:
                path = item.get("path", "")
                if "/" in path:
                    dirs.add(path.split("/")[0])
                else:
                    dirs.add(path)
            
            # Filter out files and sort directories
            main_dirs = sorted([d for d in dirs if not any(d.endswith(ext) for ext in [".py", ".js", ".md", ".txt", ".json", ".toml", ".yml", ".yaml"])])
            
            for directory in main_dirs:
                user_prompt += f"- {directory}/\n"
            user_prompt += "\n"
        
        # Add key files (just names, not content)
        if repo_data.get("src_files"):
            user_prompt += "Key Source Files:\n\n"
            for file in repo_data["src_files"][:20]:  # Limit to first 20 files
                user_prompt += f"- {file['path']}\n"
            user_prompt += "\n"
        
        # Add project structure analysis
        project_structure = self._analyze_project_structure(repo_data)
        user_prompt += project_structure
        
        # Generate modules documentation
        try:
            modules_doc = self._make_completion_request(system_prompt, user_prompt)
            return f"# Modules Documentation (Summarized)\n\n{modules_doc}"
        except Exception as e:
            logger.error(f"Error generating summarized modules documentation: {str(e)}")
            return f"# Error Generating Modules Documentation\n\nAn error occurred while generating the modules documentation: {str(e)}"
    
    def generate_usage_doc(self, repo_data: Dict[str, Any]) -> str:
        """
        Generate usage documentation
        
        Args:
            repo_data: Repository data
            
        Returns:
            Generated usage documentation
        """
        logger.info(f"Generating usage documentation for {repo_data['owner']}/{repo_data['name']}")
        
        # Prepare system prompt
        system_prompt = """
        You are a senior AI technical writer generating a USAGE.md file for a GitHub repository.
        Your task is to create clear, practical usage examples and instructions for the project.
        
        Use markdown with proper formatting:
        - Use a single `#` for the document title
        - Use `##`, `###` for section headers (don't skip levels)
        - Add blank lines before and after headings, lists, code blocks, and tables
        - Use triple-backtick code blocks with language specified
        - Avoid trailing whitespace and punctuation in headings
        
        Include the following sections:
        
        ### Installation
        Step-by-step installation instructions.
        
        ### Basic Usage
        Simple examples to get started quickly.
        
        ### Advanced Usage
        More complex examples and use cases.
        
        ### Configuration
        Available configuration options and how to use them.
        
        ### Troubleshooting
        Common issues and their solutions.
        
        Focus on practical, runnable examples. Use actual code from the repository when available.
        Be concise but comprehensive. Ensure code examples are complete with proper imports and context.
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
                        "code": example.get("content", "")
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
                        "code": code.strip()
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
            for i, example in enumerate(code_examples[:5]):  # Limit to first 5 examples
                user_prompt += f"Example {i+1} from {example['source']}: {example['name']}\n\n"
                user_prompt += "```python\n"
                user_prompt += self._truncate_content(example["code"], max_chars=1000)
                user_prompt += "\n```\n\n"
        
        # Generate usage documentation
        try:
            usage_doc = self._make_completion_request(system_prompt, user_prompt)
            return f"# Usage Guide\n\n{usage_doc}"
        except Exception as e:
            logger.error(f"Error generating usage documentation: {str(e)}")
            return f"# Error Generating Usage Documentation\n\nAn error occurred while generating the usage documentation: {str(e)}"
    
    def generate_dependencies_doc(self, repo_data: Dict[str, Any]) -> str:
        """
        Generate dependencies documentation
        
        Args:
            repo_data: Repository data
            
        Returns:
            Generated dependencies documentation
        """
        logger.info(f"Generating dependencies documentation for {repo_data['owner']}/{repo_data['name']}")
        
        # Prepare system prompt
        system_prompt = """
        You are a senior AI technical writer generating a DEPENDENCIES.md file for a GitHub repository.
        Your task is to document all dependencies, their purposes, and requirements.
        
        Use markdown with proper formatting:
        - Use a single `#` for the document title
        - Use `##`, `###` for section headers (don't skip levels)
        - Use tables for structured information about dependencies
        
        Include the following sections:
        
        ### Runtime Dependencies
        Core packages required for the application to run.
        
        ### Development Dependencies
        Packages used for development, testing, and building.
        
        ### Optional Dependencies
        Packages that provide additional functionality but aren't required.
        
        ### Environment Variables
        Configuration variables needed by the application.
        
        ### External Services
        APIs or platforms the project connects to.
        
        For each dependency, include:
        - Package name
        - Version requirements (if available)
        - Purpose/functionality it provides
        
        If information is missing, make reasonable inferences based on the repository content
        and mark these with [Assumed] to indicate uncertainty.
        """
        
        # Prepare user prompt
        user_prompt = f"Repository: {repo_data['owner']}/{repo_data['name']}\n\n"
        
        # Look for dependency files
        dependency_files = []
        for file in repo_data.get("root_files", []):
            filename = file.get("name", "").lower()
            if filename in ["requirements.txt", "pyproject.toml", "setup.py", "package.json", 
                           "gemfile", "cargo.toml", "go.mod", "pom.xml", "build.gradle"]:
                dependency_files.append(file)
        
        if dependency_files:
            user_prompt += "Dependency Files:\n\n"
            for file in dependency_files:
                user_prompt += f"File: {file['name']}\n\n"
                user_prompt += f"```\n{file['content']}\n```\n\n"
        
        # Generate dependencies documentation
        try:
            dependencies_doc = self._make_completion_request(system_prompt, user_prompt)
            return f"# Dependencies\n\n{dependencies_doc}"
        except Exception as e:
            logger.error(f"Error generating dependencies documentation: {str(e)}")
            return f"# Error Generating Dependencies Documentation\n\nAn error occurred while generating the dependencies documentation: {str(e)}"
