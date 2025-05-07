"""
Enhanced AI Generator Module

This module handles the generation of documentation using OpenAI's API.
It creates overview, modules documentation, usage examples, and dependencies documentation.
Includes enhanced repository analysis and code sample extraction.
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
    """Enhanced generator for AI-powered documentation"""
    
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
        try:
            logger.info(f"Making OpenAI request with system prompt: {system_prompt[:100]}...")
            logger.info(f"User prompt length: {len(user_prompt)} characters")
            
            response = client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o for better documentation quality
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=3000  # Increased for more comprehensive documentation
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"Received response of length: {len(result)} characters")
            return result
        except Exception as e:
            logger.error(f"Error making OpenAI request: {str(e)}")
            # Add exponential backoff for rate limits
            if "rate limit" in str(e).lower():
                wait_time = 10
                logger.info(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return self._make_completion_request(system_prompt, user_prompt, temperature)
            raise
    
    def _process_code_samples(self, repo_data: Dict[str, Any]) -> str:
        """
        Process code samples from repository data
        
        Args:
            repo_data: Repository data
            
        Returns:
            Formatted string with code samples
        """
        code_samples_text = ""
        
        # Process code samples from markdown files
        if repo_data.get("code_samples"):
            code_samples_text += "\n## Code Samples from Documentation\n\n"
            for i, sample in enumerate(repo_data["code_samples"][:5]):  # Limit to 5 samples
                language = sample.get("language", "text")
                code = sample.get("code", "")
                
                # Truncate very long code samples
                if len(code) > 500:
                    code = code[:500] + "\n# ... [truncated] ..."
                
                code_samples_text += f"### Code Sample {i+1} ({language})\n```{language}\n{code}\n```\n\n"
        
        # Process example files
        if repo_data.get("example_files"):
            code_samples_text += "\n## Example Files\n\n"
            for i, example in enumerate(repo_data["example_files"][:3]):  # Limit to 3 examples
                name = example.get("name", "")
                path = example.get("path", "")
                content = example.get("content", "")
                
                # Determine language from file extension
                ext = os.path.splitext(name)[1].lower()
                language = "python" if ext == ".py" else \
                           "javascript" if ext in [".js", ".jsx"] else \
                           "typescript" if ext in [".ts", ".tsx"] else \
                           "java" if ext == ".java" else \
                           "ruby" if ext == ".rb" else \
                           "go" if ext == ".go" else \
                           "rust" if ext == ".rs" else \
                           "csharp" if ext in [".cs", ".csx"] else \
                           "text"
                
                # Truncate very long examples
                if len(content) > 800:
                    content = content[:800] + "\n# ... [truncated] ..."
                
                code_samples_text += f"### Example: {name} (from {path})\n```{language}\n{content}\n```\n\n"
        
        return code_samples_text
    
    def _truncate_content(self, content: str, max_chars: int = MAX_PROMPT_CHARS) -> str:
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
        
        # Truncate and add note
        return content[:max_chars] + "\n\n[Content truncated due to length...]"
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated number of tokens
        """
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def _should_use_summarization_approach(self, repo_data: Dict[str, Any]) -> bool:
        """
        Determine if we should use a summarization approach for large repositories
        
        Args:
            repo_data: Repository data
            
        Returns:
            True if summarization approach should be used
        """
        # Calculate total content size
        total_content = ""
        if repo_data.get("readme") and repo_data["readme"].get("content"):
            total_content += repo_data["readme"]["content"]
        
        for file in repo_data.get("root_files", [])[:5]:  # Limit to first 5 files
            if file.get("content"):
                total_content += file.get("content", "")
        
        # Estimate tokens
        estimated_tokens = self._estimate_tokens(total_content)
        logger.info(f"Estimated tokens for repository: {estimated_tokens}")
        return estimated_tokens > TOKEN_LIMIT_THRESHOLD
        
    def _analyze_project_structure(self, repo_data: Dict[str, Any]) -> str:
        """
        Analyze project structure and generate a description
        
        Args:
            repo_data: Repository data
            
        Returns:
            Formatted string with project structure analysis
        """
        structure_text = "\n## Project Structure Analysis\n\n"
        
        # Get project structure type
        project_type = repo_data.get("project_structure", "generic")
        structure_text += f"Project Type: {project_type}\n\n"
        
        # Add specific information based on project type
        if project_type == "python_package":
            structure_text += "This is a Python package with a standard structure.\n"
            # Look for setup.py or pyproject.toml
            for file in repo_data.get("root_files", []):
                if file.get("name") == "setup.py" and file.get("content"):
                    structure_text += "\n### Package Configuration (setup.py)\n"
                    # Extract package information
                    setup_content = file.get("content", "")
                    # Look for name, version, description
                    name_match = re.search(r'name=["\']([^"\']*)["\'\s,]', setup_content)
                    version_match = re.search(r'version=["\']([^"\']*)["\'\s,]', setup_content)
                    description_match = re.search(r'description=["\']([^"\']*)["\'\s,]', setup_content)
                    
                    if name_match:
                        structure_text += f"- Package Name: {name_match.group(1)}\n"
                    if version_match:
                        structure_text += f"- Version: {version_match.group(1)}\n"
                    if description_match:
                        structure_text += f"- Description: {description_match.group(1)}\n"
                    
                    # Look for install_requires
                    install_requires = re.search(r'install_requires\s*=\s*\[([^\]]*)\]', setup_content, re.DOTALL)
                    if install_requires:
                        structure_text += "\n#### Dependencies:\n"
                        deps = re.findall(r'["\']([^"\']*)["\']', install_requires.group(1))
                        for dep in deps:
                            structure_text += f"- {dep}\n"
                
                elif file.get("name") == "pyproject.toml" and file.get("content"):
                    structure_text += "\n### Package Configuration (pyproject.toml)\n"
                    # Extract basic info from pyproject.toml
                    content = file.get("content", "")
                    name_match = re.search(r'name\s*=\s*["\']([^"\']*)["\'\s]', content)
                    version_match = re.search(r'version\s*=\s*["\']([^"\']*)["\'\s]', content)
                    
                    if name_match:
                        structure_text += f"- Package Name: {name_match.group(1)}\n"
                    if version_match:
                        structure_text += f"- Version: {version_match.group(1)}\n"
        
        elif project_type == "node_js":
            structure_text += "This is a Node.js project.\n"
            # Look for package.json
            for file in repo_data.get("root_files", []):
                if file.get("name") == "package.json" and file.get("content"):
                    try:
                        package_json = json.loads(file.get("content", "{}"))
                        structure_text += "\n### Package Configuration\n"
                        structure_text += f"- Package Name: {package_json.get('name', 'N/A')}\n"
                        structure_text += f"- Version: {package_json.get('version', 'N/A')}\n"
                        structure_text += f"- Description: {package_json.get('description', 'N/A')}\n"
                        
                        if package_json.get("dependencies"):
                            structure_text += "\n#### Dependencies:\n"
                            for dep, version in package_json.get("dependencies", {}).items():
                                structure_text += f"- {dep}: {version}\n"
                    except json.JSONDecodeError:
                        structure_text += "Could not parse package.json\n"
        
        # Add directory structure overview
        structure_text += "\n### Directory Structure\n\n"
        
        # Get main directories from repo tree
        if repo_data.get("repo_tree"):
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
                structure_text += f"- {directory}/\n"
        
        return structure_text
    
    def _extract_dependencies(self, repo_data: Dict[str, Any]) -> List[str]:
        """
        Extract dependencies from repository data
        
        Args:
            repo_data: Repository data
            
        Returns:
            List of dependencies
        """
        dependencies = []
        
        # Check for requirements.txt
        if repo_data.get("requirements") and repo_data["requirements"].get("content"):
            content = repo_data["requirements"]["content"]
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    # Remove version specifiers
                    dep = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                    if dep and dep not in dependencies:
                        dependencies.append(dep)
        
        # Check for setup.py
        for file in repo_data.get("root_files", []):
            if file.get("name") == "setup.py" and file.get("content"):
                content = file.get("content", "")
                install_requires = re.search(r'install_requires\s*=\s*\[([^\]]*)\]', content, re.DOTALL)
                if install_requires:
                    deps = re.findall(r'["\']([^"\']*)["\']', install_requires.group(1))
                    for dep in deps:
                        if dep and dep not in dependencies:
                            dependencies.append(dep)
        
        # Check for package.json
        for file in repo_data.get("root_files", []):
            if file.get("name") == "package.json" and file.get("content"):
                try:
                    package_json = json.loads(file.get("content", "{}"))
                    if package_json.get("dependencies"):
                        for dep in package_json["dependencies"].keys():
                            if dep and dep not in dependencies:
                                dependencies.append(dep)
                    if package_json.get("devDependencies"):
                        for dep in package_json["devDependencies"].keys():
                            if dep and dep not in dependencies:
                                dependencies.append(dep)
                except json.JSONDecodeError:
                    pass
        
        return dependencies
    
    def generate_docs_content(self, repo_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate documentation content for a repository
        
        Args:
            repo_data: Repository data
            
        Returns:
            Dictionary mapping filenames to content
        """
        logger.info(f"Generating documentation for {repo_data['owner']}/{repo_data['name']}")
        
        # Generate overview documentation
        overview_doc = self.generate_overview_doc(repo_data)
        
        # Generate modules documentation
        modules_doc = self.generate_modules_doc(repo_data)
        
        # Generate usage documentation
        usage_doc = self.generate_usage_doc(repo_data)
        
        # Generate dependencies documentation
        dependencies_doc = self.generate_dependencies_doc(repo_data)
        
        # Combine all documentation
        docs_content = {
            "OVERVIEW.md": overview_doc,
            "MODULES.md": modules_doc,
            "USAGE.md": usage_doc,
            "DEPENDENCIES.md": dependencies_doc
        }
        
        return docs_content
    
    def generate_overview_doc(self, repo_data: Dict[str, Any]) -> str:
        """
        Generate overview documentation
        
        Args:
            repo_data: Repository data
            
        Returns:
            Overview documentation content
        """
        logger.info(f"Generating overview documentation for {repo_data['owner']}/{repo_data['name']}")
        
        # Prepare repository overview
        repo_overview = f"""# {repo_data['full_name']} Overview

## Repository Information

- **Repository**: {repo_data['full_name']}
- **Description**: {repo_data.get('description', 'No description provided')}
- **Language**: {repo_data.get('language', 'Unknown')}
- **Stars**: {repo_data.get('stars', 0)}
- **Forks**: {repo_data.get('forks', 0)}
- **Topics**: {', '.join(repo_data.get('topics', []))}
"""
        
        # Add README content if available
        if repo_data.get("readme") and repo_data["readme"].get("content"):
            readme_content = repo_data["readme"]["content"]
            repo_overview += f"\n## README Content\n\n{readme_content}\n"
        
        # Add project structure analysis
        project_structure = self._analyze_project_structure(repo_data)
        repo_overview += project_structure
        
        # Add code samples
        code_samples = self._process_code_samples(repo_data)
        if code_samples:
            repo_overview += f"\n{code_samples}\n"
        
        # Prepare system prompt
        system_prompt = """
        You are a documentation expert. Your task is to analyze the provided GitHub repository
        information and generate a comprehensive overview of the project. Focus on:
        
        1. What the project does and its main purpose
        2. Key features and capabilities
        3. High-level architecture or components
        4. Target audience or use cases
        5. Any notable technologies or frameworks used
        
        Use the provided code samples and project structure to inform your analysis.
        Format your response in Markdown. Be concise but informative.
        """
        
        # Prepare user prompt
        user_prompt = f"""
        Please generate an overview for the following GitHub repository:
        
        {repo_overview}
        
        Please analyze the information and create a comprehensive overview that explains
        what this project is, what it does, its key features, and how it's structured.
        
        Pay special attention to the code samples and project structure information provided.
        Use these to accurately describe how the project works and its architecture.
        
        Format your response in Markdown with appropriate headings and sections.
        """
        
        # Add web search results if available
        web_search_results = repo_data.get("web_search_results", "")
        if web_search_results:
            user_prompt += f"\n\nAdditional context from web search:\n\n{web_search_results}"
        
        # Generate overview using OpenAI
        try:
            overview_content = self._make_completion_request(system_prompt, user_prompt)
            return overview_content
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
        
        # Check if we need to use summarization approach
        if self._should_use_summarization_approach(repo_data):
            logger.info("Using summarization approach for modules documentation due to repository size")
            return self._generate_modules_doc_summarized(repo_data)
        
        # Prepare system prompt
        system_prompt = """
        You are a senior AI technical writer generating a MODULES.md file for a GitHub repository.
        Your task is to document the architecture and code organization of the project.
        
        Use markdown with proper formatting:
        - Use a single `#` for the document title
        - Use `##`, `###` for section headers (don't skip levels)
        - Add blank lines before and after headings, lists, code blocks, and tables
        - Use triple-backtick code blocks with language specified
        - Avoid trailing whitespace and punctuation in headings
        
        Include the following sections:
        
        ### Project Architecture
        High-level overview of how the codebase is organized.
        
        ### Core Modules
        Key components that implement the main functionality.
        
        ### Helper/Utility Modules
        Supporting code, helpers, and utilities.
        
        ### Module Relationships
        How different parts of the codebase interact.
        
        ### Extension Points
        Areas where the code can be extended or customized.
        
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
        
        # Add web search results if available
        web_search_results = repo_data.get("web_search_results", "")
        if web_search_results:
            user_prompt += f"Web Search Results:\n\n{web_search_results}\n\n"
        
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
        - Add blank lines before and after headings, lists, code blocks, and tables
        - Use proper table formatting with blank lines before and after
        - Avoid trailing whitespace and punctuation in headings
        
        Group dependencies based on type and provide useful metadata.
        
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
        APIs or platforms the project connects to (e.g., databases, cloud services).
        
        Be concise but comprehensive. Infer dependency purposes from the code when not explicitly stated.
        Use [Assumed] for unclear parts. Don't duplicate or hallucinate packages.
        """
        
        # Extract dependencies
        dependencies = self._extract_dependencies(repo_data)
        
        # Prepare user prompt
        user_prompt = f"Repository Information:\n\n"
        user_prompt += f"Repository: {repo_data['owner']}/{repo_data['name']}\n"
        user_prompt += f"Description: {repo_data.get('description', 'No description provided')}\n\n"
        
        # Add requirements file content if available
        if repo_data.get("requirements") and repo_data["requirements"].get("content"):
            user_prompt += f"Requirements File: {repo_data['requirements']['name']}\n\n"
            user_prompt += self._truncate_content(repo_data["requirements"]["content"], max_chars=2000)
            user_prompt += "\n\n"
        
        # Add extracted dependencies
        if dependencies:
            user_prompt += "Extracted Dependencies:\n\n"
            for dep in dependencies:
                user_prompt += f"- {dep}\n"
            user_prompt += "\n\n"
        
        # Extract environment variables
        env_vars = []
        
        # Look for environment variables in Python files
        source_files = repo_data.get("src_files", [])
        if not source_files:
            source_files = repo_data.get("root_files", [])
        
        for file in source_files:
            if file.get("content") and file["path"].endswith(".py"):
                content = file.get("content", "")
                # Look for os.environ, os.getenv, and dotenv patterns
                env_matches = re.findall(r'(?:os\.environ(?:\.|\[\'|\"|\[\")|os\.getenv\(|getenv\(|\.env\.|dotenv)[\'"]([A-Z0-9_]+)[\'"]', content)
                for match in env_matches:
                    if match not in env_vars:
                        env_vars.append(match)
        
        if env_vars:
            user_prompt += "Environment Variables:\n\n"
            for var in env_vars:
                user_prompt += f"- {var}\n"
            user_prompt += "\n\n"
        
        # Look for .env or .env.example files
        env_file_content = ""
        for file in repo_data.get("root_files", []):
            if file.get("path") in [".env.example", ".env.sample", ".env.template"]:
                env_file_content = file.get("content", "")
                user_prompt += f"Environment File: {file['path']}\n\n"
                user_prompt += env_file_content
                user_prompt += "\n\n"
                break
        
        # Generate dependencies documentation
        try:
            dependencies_doc = self._make_completion_request(system_prompt, user_prompt)
            return f"# Dependencies\n\n{dependencies_doc}"
        except Exception as e:
            logger.error(f"Error generating dependencies documentation: {str(e)}")
            return f"# Error Generating Dependencies Documentation\n\nAn error occurred while generating the dependencies documentation: {str(e)}"
