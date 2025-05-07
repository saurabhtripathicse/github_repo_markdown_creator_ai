"""
AI Generator Module

This module handles the generation of documentation using OpenAI's API.
It creates overview, modules documentation, usage examples, and dependencies documentation.
"""

import os
import re
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
MAX_PROMPT_CHARS = 4000  # Maximum characters to include in a prompt (increased from 3000)
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
        try:
            logger.info(f"Making OpenAI request with system prompt: {system_prompt[:100]}...")
            logger.info(f"User prompt length: {len(user_prompt)} characters")
            
            response = client.chat.completions.create(
                model="gpt-4o",  # Upgraded to GPT-4o for better documentation quality
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=3000  # Increased to 3000 for more comprehensive documentation
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
    
    def _extract_sections_from_readme(self, readme_content: str) -> Dict[str, str]:
        """
        Extract sections from README content
        
        Args:
            readme_content: README content
            
        Returns:
            Dictionary with section name as key and content as value
        """
        if not readme_content:
            return {}
        
        # Find all headings
        heading_pattern = r'^(#{1,3})\s+(.+?)$'
        headings = [(len(match.group(1)), match.group(2).strip(), match.start()) 
                   for match in re.finditer(heading_pattern, readme_content, re.MULTILINE)]
        
        if not headings:
            return {"main": readme_content}
        
        sections = {}
        
        # Process each heading and its content
        for i, (level, title, start) in enumerate(headings):
            # Find the end of this section (start of next section)
            end = headings[i+1][2] if i < len(headings) - 1 else len(readme_content)
            
            # Extract section content
            section_content = readme_content[start:end].strip()
            
            # Clean up section title for use as a key
            section_key = title.lower().replace(' ', '_')
            
            # Store section
            sections[section_key] = section_content
            
            # Also store by common section names
            lower_title = title.lower()
            if any(keyword in lower_title for keyword in ['install', 'setup', 'getting started']):
                sections['installation'] = section_content
            elif any(keyword in lower_title for keyword in ['usage', 'example', 'how to use']):
                sections['usage'] = section_content
            elif any(keyword in lower_title for keyword in ['api', 'reference', 'documentation']):
                sections['api'] = section_content
            elif any(keyword in lower_title for keyword in ['feature', 'functionality']):
                sections['features'] = section_content
            
        # Add full README
        sections['full_readme'] = readme_content
        
        return sections
    
    def _extract_code_examples(self, repo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract code examples from repository data
        
        Args:
            repo_data: Repository data
            
        Returns:
            List of code examples with metadata
        """
        examples = []
        
        # Extract code blocks from README
        if repo_data.get("readme") and repo_data["readme"].get("content"):
            readme_content = repo_data["readme"]["content"]
            code_blocks = re.findall(r'```(?:python|py)?\n(.*?)\n```', readme_content, re.DOTALL)
            
            for i, code in enumerate(code_blocks):
                if len(code.strip()) > 10:  # Only include non-trivial examples
                    examples.append({
                        "source": "README",
                        "name": f"Example {i+1} from README",
                        "code": code.strip(),
                        "language": "python"
                    })
        
        # Extract examples from example files
        if repo_data.get("example_files"):
            for file in repo_data["example_files"]:
                if file.get("content") and len(file["content"].strip()) > 0:
                    examples.append({
                        "source": "Examples Directory",
                        "name": file.get("path", "Unknown example"),
                        "code": file["content"],
                        "language": "python"
                    })
        
        # If no examples found yet, look in test files
        if not examples and repo_data.get("test_files"):
            for file in repo_data["test_files"][:2]:  # Limit to first 2 test files
                if file.get("content") and len(file["content"].strip()) > 0:
                    examples.append({
                        "source": "Test Files",
                        "name": file.get("path", "Unknown test"),
                        "code": file["content"],
                        "language": "python"
                    })
        
        return examples
    
    def _extract_dependencies(self, repo_data: Dict[str, Any]) -> List[str]:
        """
        Extract dependencies from repository data
        
        Args:
            repo_data: Repository data
            
        Returns:
            List of dependencies
        """
        dependencies = []
        
        # Extract from requirements.txt
        if repo_data.get("requirements") and repo_data["requirements"].get("content"):
            content = repo_data["requirements"]["content"]
            
            # Handle different dependency file formats
            if repo_data["requirements"]["name"] == "requirements.txt":
                # Parse requirements.txt
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Remove version specifiers
                        dep = line.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].strip()
                        if dep and dep not in dependencies:
                            dependencies.append(dep)
            
            elif repo_data["requirements"]["name"] == "setup.py":
                # Extract from setup.py
                install_requires = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if install_requires:
                    deps_str = install_requires.group(1)
                    # Extract quoted strings
                    deps = re.findall(r'[\'\"](.*?)[\'\"]', deps_str)
                    for dep in deps:
                        # Remove version specifiers
                        clean_dep = dep.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].strip()
                        if clean_dep and clean_dep not in dependencies:
                            dependencies.append(clean_dep)
            
            elif repo_data["requirements"]["name"] == "pyproject.toml":
                # Extract from pyproject.toml
                deps_section = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if deps_section:
                    deps_str = deps_section.group(1)
                    # Extract quoted strings
                    deps = re.findall(r'[\'\"](.*?)[\'\"]', deps_str)
                    for dep in deps:
                        # Remove version specifiers
                        clean_dep = dep.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].strip()
                        if clean_dep and clean_dep not in dependencies:
                            dependencies.append(clean_dep)
        
        # If no dependencies found, try to infer from imports
        if not dependencies:
            # Collect all Python files
            python_files = []
            python_files.extend(repo_data.get("root_files", []))
            python_files.extend(repo_data.get("src_files", []))
            
            # Extract import statements
            for file in python_files:
                if file.get("content") and file["path"].endswith(".py"):
                    content = file["content"]
                    
                    # Find import statements
                    import_lines = re.findall(r'^(?:from|import)\s+([a-zA-Z0-9_]+)', content, re.MULTILINE)
                    for module in import_lines:
                        # Skip standard library modules
                        if module not in ['os', 'sys', 're', 'time', 'json', 'math', 'random', 
                                         'datetime', 'collections', 'itertools', 'functools', 
                                         'typing', 'pathlib', 'shutil', 'tempfile', 'io', 
                                         'unittest', 'test', 'logging', 'argparse']:
                            if module not in dependencies:
                                dependencies.append(module)
        
        return dependencies
    
    def generate_docs_content(self, repo_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate all documentation content
        
        Args:
            repo_data: Repository data
            
        Returns:
            Dictionary with generated documentation
        """
        logger.info(f"Starting documentation generation for {repo_data['owner']}/{repo_data['name']}")
        
        docs = {
            "OVERVIEW.md": self.generate_overview(repo_data),
            "MODULES.md": self.generate_modules_doc(repo_data),
            "USAGE.md": self.generate_usage_doc(repo_data),
            "DEPENDENCIES.md": self.generate_dependencies_doc(repo_data)
        }
        
        logger.info(f"Completed documentation generation for {repo_data['owner']}/{repo_data['name']}")
        return docs
    
    def generate_overview(self, repo_data: Dict[str, Any]) -> str:
        """
        Generate repository overview
        
        Args:
            repo_data: Repository data
            
        Returns:
            Generated overview
        """
        logger.info(f"Generating overview for {repo_data['owner']}/{repo_data['name']}")
        
        system_prompt = (
            "You are a senior AI technical writer generating a detailed OVERVIEW.md for a GitHub repository.\n\n"
            
            "Use markdown with proper formatting:\n"
            "- Use a single `#` for the document title\n"
            "- Use `##`, `###` for section headers (don't skip levels)\n"
            "- Add blank lines before and after headings, lists, code blocks, and tables\n"
            "- Use triple-backtick code blocks with language specified\n"
            "- Avoid trailing whitespace and punctuation in headings\n\n"
            
            "Write in clear, professional tone and include:\n"
            "### Purpose\n"
            "Describe what problem this project solves and its core utility.\n\n"
            
            "### Key Features\n"
            "Bullet list (5–10) of the main capabilities based on README, repo code, or web snippets.\n\n"
            
            "### Repository Structure\n"
            "List major folders/files with a short purpose (e.g., `src/`, `tests/`, `docs/`, `pyproject.toml`).\n\n"
            
            "### Use Cases\n"
            "Mention 2–3 realistic developer scenarios (e.g., \"automated API agents using OpenAI SDK\").\n\n"
            
            "### Requirements\n"
            "Languages, frameworks, versions, API keys (if mentioned). Pull from pyproject.toml or setup.py.\n\n"
            
            "### Project Status\n"
            "Indicate whether the repo is stable, experimental, archived, etc.\n\n"
            
            "✅ Integrate code or text from README, web_search_results, and actual repo content.\n"
            "✅ If something is unclear, label with `[Assumed]`.\n"
            "✅ Keep output length between 2000–3000 tokens. Use `###` headers.\n"
        )
        
        # Extract README sections
        readme_sections = {}
        if repo_data.get("readme") and repo_data["readme"].get("content"):
            readme_sections = self._extract_sections_from_readme(repo_data["readme"]["content"])
        
        # Prepare user prompt
        user_prompt = f"# Repository Information\n\n"
        user_prompt += f"Repository: {repo_data['owner']}/{repo_data['name']}\n"
        user_prompt += f"Description: {repo_data.get('description', 'No description provided')}\n"
        user_prompt += f"Stars: {repo_data.get('stars', 0)}\n"
        user_prompt += f"Forks: {repo_data.get('forks', 0)}\n"
        user_prompt += f"Language: {repo_data.get('language', 'Unknown')}\n"
        user_prompt += f"Topics: {', '.join(repo_data.get('topics', []))}\n\n"
        
        # Add README introduction
        if readme_sections.get("full_readme"):
            # First, try to get just the introduction (before first heading)
            intro_match = re.match(r'^(.*?)(?:^#|\Z)', readme_sections["full_readme"], re.DOTALL | re.MULTILINE)
            if intro_match and intro_match.group(1).strip():
                user_prompt += "# README Introduction\n\n"
                user_prompt += self._truncate_content(intro_match.group(1).strip(), max_chars=2000)
                user_prompt += "\n\n"
            else:
                # If no clear intro, use the first part of the README
                user_prompt += "# README Content\n\n"
                user_prompt += self._truncate_content(readme_sections["full_readme"], max_chars=2000)
                user_prompt += "\n\n"
        
        # Add specific README sections if available
        for section_name in ["features", "overview", "introduction", "description"]:
            if readme_sections.get(section_name):
                user_prompt += f"# README {section_name.title()} Section\n\n"
                user_prompt += self._truncate_content(readme_sections[section_name], max_chars=1500)
                user_prompt += "\n\n"
        
        # Add repository structure information
        user_prompt += "# Repository Structure\n\n"
        
        # List important directories and files
        directories = []
        files = []
        
        # Check for important directories
        if repo_data.get("src_files"):
            directories.append("src/ - Source code files")
        if repo_data.get("test_files"):
            directories.append("tests/ - Test files")
        if repo_data.get("example_files"):
            directories.append("examples/ - Example code")
        if repo_data.get("doc_files"):
            directories.append("docs/ - Documentation files")
        
        # Check for important root files
        root_files = repo_data.get("root_files", [])
        for file in root_files:
            path = file.get("path", "")
            if path.endswith((".py", ".js", ".ts", ".go", ".java", ".rb")):
                files.append(f"{path} - Source code file")
            elif path in ["requirements.txt", "setup.py", "pyproject.toml"]:
                files.append(f"{path} - Python package configuration")
            elif path in ["package.json", "package-lock.json", "yarn.lock"]:
                files.append(f"{path} - JavaScript package configuration")
            elif path in [".github", ".circleci", ".travis.yml"]:
                files.append(f"{path} - CI/CD configuration")
        
        if directories:
            user_prompt += "## Important Directories:\n"
            for directory in directories:
                user_prompt += f"- {directory}\n"
            user_prompt += "\n"
        
        if files:
            user_prompt += "## Important Files:\n"
            for file in files[:10]:  # Limit to 10 files
                user_prompt += f"- {file}\n"
            user_prompt += "\n"
        
        # Extract version information
        version_info = "Unknown"
        for file in root_files:
            if file.get("path") in ["setup.py", "pyproject.toml", "package.json"]:
                content = file.get("content", "")
                version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content) or re.search(r'"version":\s*"([^"]+)"', content)
                if version_match:
                    version_info = version_match.group(1)
                    break
        
        user_prompt += f"## Version Information:\n{version_info}\n\n"
        
        # Check for web search results
        web_search_results = repo_data.get("web_search_results", "")
        
        # Add web search results to prompt if available
        if web_search_results:
            user_prompt += f"""
            
            # Additional information from web search:
            {web_search_results}
            """
        
        # Generate overview
        overview = self._make_completion_request(system_prompt, user_prompt, temperature=0.3)
        
        # Format as Markdown
        return f"# Repository Overview\n\n{overview}"
    
    def generate_modules_doc(self, repo_data: Dict[str, Any]) -> str:
        """
        Generate modules documentation
        
        Args:
            repo_data: Repository data
            
        Returns:
            Generated modules documentation
        """
        logger.info(f"Generating modules documentation for {repo_data['owner']}/{repo_data['name']}")
        
        # First, analyze if the repository has enough modules to warrant a separate document
        source_files = repo_data.get("src_files", [])
        if not source_files:
            source_files = repo_data.get("root_files", [])
        
        # Count Python files to determine if we have enough modules
        python_files = [f for f in source_files if f.get("path", "").endswith(".py")]
        
        # If there are very few Python files, we might want to skip this document or make it minimal
        if len(python_files) <= 2:
            logger.info(f"Repository has only {len(python_files)} Python files. Generating minimal modules documentation.")
            return self._generate_minimal_modules_doc(repo_data)
        
        system_prompt = (
            "You are a senior AI technical writer generating a MODULES.md file describing the repo's modules and interfaces.\n\n"
            
            "Use markdown with proper formatting:\n"
            "- Use a single `#` for the document title\n"
            "- Use `##`, `###` for section headers (don't skip levels)\n"
            "- Add blank lines before and after headings, lists, code blocks, and tables\n"
            "- Use triple-backtick code blocks with language specified\n"
            "- Avoid trailing whitespace and punctuation in headings\n\n"
            
            "### Module Overview\n"
            "Describe the architectural layout and what modules exist.\n\n"
            
            "### Core Modules\n"
            "For each file in `src/` or root:\n"
            "- Filename and path\n"
            "- High-level summary\n"
            "- Public classes/functions\n"
            "- Example import path\n"
            "- 10–20 line usage snippet (use ACTUAL examples from the repository when available)\n\n"
            
            "### Extension Points\n"
            "Which classes/functions can be extended or overridden by developers.\n\n"
            
            "### Utility Modules\n"
            "Reusable components (logging, file I/O, helper functions).\n\n"
            
            "### Module Relationships\n"
            "Mention if there is coupling between modules or clear separation of concerns.\n\n"
            
            "✅ Don't document private methods (`_func`).\n"
            "✅ ALWAYS cite the source file for each code example (e.g., 'From examples/demo.py').\n"
            "✅ Prioritize REAL examples from the repository over created examples.\n"
            "✅ Infer structure based on class names, usage patterns, or imports.\n"
            "✅ Use `[Assumed]` for unclear parts.\n"
            "✅ Ensure code examples are complete with proper imports and context.\n"
            "✅ Use at least 2000 tokens of output.\n"
        )
        
        # Check if we need to use summarization approach
        if self._should_use_summarization_approach(repo_data):
            logger.info("Using summarization approach for modules documentation due to repository size")
            return self._generate_modules_doc_summarized(repo_data)
        
        # Prepare user prompt
        user_prompt = f"Repository: {repo_data['owner']}/{repo_data['name']}\n\n"
        
        # Add source files
        if source_files:
            user_prompt += "Source Files:\n\n"
            for file in source_files[:10]:  # Limit to first 10 files
                if file.get("content") and file["path"].endswith(".py"):
                    user_prompt += f"File: {file['path']}\n"
                    user_prompt += self._truncate_content(file.get("content", ""))
                    user_prompt += "\n\n"
        
        # Extract import statements to help with import paths
        import_statements = []
        for file in source_files:
            if file.get("content") and file["path"].endswith(".py"):
                # Extract import lines using regex
                imports = re.findall(r'^(?:from|import)\s+[a-zA-Z0-9_\.]+(?:\s+import\s+[a-zA-Z0-9_\.,\s]+)?', 
                                    file.get("content", ""), re.MULTILINE)
                for imp in imports:
                    if imp not in import_statements:
                        import_statements.append(imp)
        
        if import_statements:
            user_prompt += "# Import Statements Found in Source Files\n\n"
            for imp in import_statements[:20]:  # Limit to 20 import statements
                user_prompt += f"{imp}\n"
            user_prompt += "\n\n"
        
        # Extract class definitions to help identify public interfaces
        class_definitions = []
        for file in source_files:
            if file.get("content") and file["path"].endswith(".py"):
                # Extract class definitions using regex
                classes = re.findall(r'class\s+([a-zA-Z0-9_]+)(?:\(([^)]*)\))?:', file.get("content", ""))
                for class_name, parent_classes in classes:
                    class_definitions.append({
                        "name": class_name,
                        "parents": parent_classes,
                        "file": file["path"]
                    })
        
        if class_definitions:
            user_prompt += "# Class Definitions Found in Source Files\n\n"
            for cls in class_definitions:
                if cls["parents"]:
                    user_prompt += f"class {cls['name']}({cls['parents']}) in {cls['file']}\n"
                else:
                    user_prompt += f"class {cls['name']} in {cls['file']}\n"
            user_prompt += "\n\n"
        
        # Check for web search results
        web_search_results = repo_data.get("web_search_results", "")
        
        # Add web search results to prompt if available
        if web_search_results:
            user_prompt += f"""
            
            # Additional information from web search:
            {web_search_results}
            """
        
        # Generate modules documentation
        modules_doc = self._make_completion_request(system_prompt, user_prompt, temperature=0.2)
        
        # Format as Markdown
        return f"# Modules Documentation\n\n{modules_doc}"
    
    def _generate_minimal_modules_doc(self, repo_data: Dict[str, Any]) -> str:
        """
        Generate minimal modules documentation for repositories with few modules
        
        Args:
            repo_data: Repository data
            
        Returns:
            Generated minimal modules documentation
        """
        system_prompt = (
            "You are a senior AI technical writer creating concise module documentation for a small repository. "
            "The repository has very few Python files, so keep the documentation brief and focused. "
            "Document only the main classes and functions that users would interact with. "
            "Include import paths and a brief example for each main class or function. "
            "Use markdown headers (###) for each section and triple-backtick code blocks for examples. "
            "If details are missing, use fallback assumptions marked with [Assumed]. "
            "Aim for clarity and actionable documentation."
        )
        
        # Prepare user prompt
        user_prompt = f"Repository: {repo_data['owner']}/{repo_data['name']}\n\n"
        
        # Add source files
        source_files = repo_data.get("src_files", [])
        if not source_files:
            source_files = repo_data.get("root_files", [])
        
        if source_files:
            user_prompt += "Source Files:\n\n"
            for file in source_files:  # Include all files since there are few
                if file.get("content") and file["path"].endswith(".py"):
                    user_prompt += f"File: {file['path']}\n"
                    user_prompt += self._truncate_content(file.get("content", ""))
                    user_prompt += "\n\n"
        
        # Check for web search results
        web_search_results = repo_data.get("web_search_results", "")
        
        # Add web search results to prompt if available
        if web_search_results:
            user_prompt += f"""
            
            # Additional information from web search:
            {web_search_results}
            """
        
        # Generate modules documentation
        modules_doc = self._make_completion_request(system_prompt, user_prompt, temperature=0.2)
        
        # Format as Markdown
        return f"# Modules Documentation\n\n{modules_doc}"
    
    def _generate_modules_doc_summarized(self, repo_data: Dict[str, Any]) -> str:
        """
        Generate modules documentation using a summarization approach for large repositories
        
        Args:
            repo_data: Repository data
            
        Returns:
            Generated modules documentation
        """
        system_prompt = (
            "You are a senior technical writer tasked with documenting the modules of a GitHub repository. "
            "Focus only on the public interface (classes, functions, methods) that users would interact with. "
            "Do not document private implementation details. "
            "Create a bullet point list of modules with brief descriptions. "
            "Format the output as Markdown with proper headings and bullet points."
        )
        
        # First, summarize each directory/module
        summaries = []
        
        # Group files by directory
        directories = {}
        for file in repo_data.get("src_files", []):
            dir_path = os.path.dirname(file["path"])
            if not dir_path:
                dir_path = "root"
            
            if dir_path not in directories:
                directories[dir_path] = []
            
            directories[dir_path].append(file)
        
        # If no src_files, use root_files
        if not directories:
            directories["root"] = repo_data.get("root_files", [])
        
        # Summarize each directory
        for dir_path, files in directories.items():
            if not files:
                continue
            
            dir_prompt = f"Directory: {dir_path}\n\n"
            for file in files[:5]:  # Limit to first 5 files per directory
                if file.get("content"):
                    dir_prompt += f"File: {file['path']}\n"
                    dir_prompt += self._truncate_content(file.get("content", ""), max_chars=1500)
                    dir_prompt += "\n\n"
            
            summary_prompt = (
                "Summarize the public interface (classes, functions, methods) in this directory. "
                "Focus only on what users would interact with. "
                "Create a bullet point list with brief descriptions."
            )
            
            dir_summary = self._make_completion_request(
                "You are a technical documentation expert. Summarize the public API only.",
                dir_prompt + summary_prompt,
                temperature=0.2
            )
            
            summaries.append(f"## {dir_path}\n\n{dir_summary}")
        
        # Combine summaries
        combined_summary = "\n\n".join(summaries)
        
        # Generate final modules documentation
        modules_doc = self._make_completion_request(
            system_prompt,
            f"Repository: {repo_data['owner']}/{repo_data['name']}\n\nModule Summaries:\n\n{combined_summary}",
            temperature=0.2
        )
        
        # Format as Markdown
        return f"# Modules Documentation\n\n{modules_doc}"
    
    def generate_usage_doc(self, repo_data: Dict[str, Any]) -> str:
        """
        Generate usage documentation
        
        Args:
            repo_data: Repository data
            
        Returns:
            Generated usage documentation
        """
        logger.info(f"Generating usage documentation for {repo_data['owner']}/{repo_data['name']}")
        
        system_prompt = (
            "You are a senior AI technical writer generating a USAGE.md file for a GitHub project.\n\n"
            
            "Use markdown with proper formatting:\n"
            "- Use a single `#` for the document title\n"
            "- Use `##`, `###` for section headers (don't skip levels)\n"
            "- Add blank lines before and after headings, lists, code blocks, and tables\n"
            "- Use triple-backtick code blocks with language specified\n"
            "- Avoid trailing whitespace and punctuation in headings\n\n"
            "The goal is to help developers run and understand the project quickly.\n\n"
            
            "Include the following sections (skip if insufficient data):\n\n"
            
            "### Installation\n"
            "Steps via `pip`, GitHub clone, or Docker. Mention requirements or virtualenv setup.\n\n"
            
            "### Quick Start\n"
            "A working 10–30 line script showing how to import and run the core feature. ALWAYS use real examples from the repository (especially from 'examples/' or 'demos/' directories). Include full import paths.\n\n"
            
            "### Configuration & Authentication\n"
            "Environment variables, API keys, or config files (from .env or dotenv). Use table format if needed.\n\n"
            
            "### Core Usage Patterns\n"
            "Common API calls, flows, or class usage. PRIORITIZE real examples from the repository code. For each example, cite the source file path. Include complete code snippets with imports.\n\n"
            
            "### Error Handling\n"
            "List at least 2 possible issues (e.g., auth errors, rate limits) and how to fix.\n\n"
            
            "### Advanced Usage\n"
            "Optional plugins, tool calling, SDK extensions, or uncommon features.\n\n"
            
            "### Common Pitfalls\n"
            "Mention things users often misconfigure or miss (e.g., `OPENAI_API_KEY` not loaded).\n\n"
            
            "✅ ALWAYS cite the source file path for each code example (e.g., 'From examples/demo.py').\n"
            "✅ Only use code that exists in the repo or web search. Don't invent or modify examples unless necessary.\n"
            "✅ Mark inferred values with `[Assumed]`. Include import paths (`from x import y`).\n"
            "✅ Ensure code examples are complete and runnable with proper imports and context.\n"
            "✅ Output size: 2000–3000 tokens.\n"
        )
        
        # Extract README sections
        readme_sections = {}
        if repo_data.get("readme") and repo_data["readme"].get("content"):
            readme_sections = self._extract_sections_from_readme(repo_data["readme"]["content"])
        
        # Extract code examples
        code_examples = self._extract_code_examples(repo_data)
        
        # Prepare user prompt
        user_prompt = f"# Repository Information\n\n"
        user_prompt += f"Repository: {repo_data['owner']}/{repo_data['name']}\n"
        user_prompt += f"Description: {repo_data.get('description', 'No description provided')}\n\n"
        
        # Add installation section from README if available
        if readme_sections.get("installation"):
            user_prompt += "# Installation Instructions from README\n\n"
            user_prompt += self._truncate_content(readme_sections["installation"], max_chars=1500)
            user_prompt += "\n\n"
        
        # Add usage section from README if available
        if readme_sections.get("usage"):
            user_prompt += "# Usage Instructions from README\n\n"
            user_prompt += self._truncate_content(readme_sections["usage"], max_chars=2000)
            user_prompt += "\n\n"
        
        # Add configuration or authentication sections if available
        for section_name in ["configuration", "auth", "authentication", "setup", "getting_started"]:
            if readme_sections.get(section_name):
                user_prompt += f"# {section_name.title()} Information from README\n\n"
                user_prompt += self._truncate_content(readme_sections[section_name], max_chars=1500)
                user_prompt += "\n\n"
        
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
            user_prompt += "# Import Statements Found in Examples\n\n"
            for imp in import_statements:
                user_prompt += f"```python\n{imp}\n```\n\n"
        
        # Add code examples
        if code_examples:
            user_prompt += "# Code Examples\n\n"
            for i, example in enumerate(code_examples[:5]):  # Limit to first 5 examples
                user_prompt += f"## Example {i+1} from {example['source']}: {example['name']}\n\n"
                user_prompt += "```python\n"
                user_prompt += self._truncate_content(example["code"], max_chars=1000)
                user_prompt += "\n```\n\n"
        
        # Look for error handling examples
        error_handling_examples = []
        for example in code_examples:
            if example.get("code") and re.search(r'(try|except|raise|error|exception)', example["code"], re.IGNORECASE):
                error_handling_examples.append(example)
        
        if error_handling_examples:
            user_prompt += "# Error Handling Examples\n\n"
            for i, example in enumerate(error_handling_examples[:2]):  # Limit to first 2 examples
                user_prompt += f"## Error Handling Example {i+1}\n\n"
                user_prompt += "```python\n"
                user_prompt += self._truncate_content(example["code"], max_chars=500)
                user_prompt += "\n```\n\n"
        
        # Check for web search results
        web_search_results = repo_data.get("web_search_results", "")
        
        # Add web search results to prompt if available
        if web_search_results:
            user_prompt += f"""
            
            # Additional code examples and usage information from web search:
            {web_search_results}
            """
        
        # Generate usage documentation
        usage_doc = self._make_completion_request(system_prompt, user_prompt, temperature=0.3)
        
        # Format as Markdown
        return f"# Usage Guide\n\n{usage_doc}"
    
    def generate_dependencies_doc(self, repo_data: Dict[str, Any]) -> str:
        """
        Generate dependencies documentation
        
        Args:
            repo_data: Repository data
            
        Returns:
            Generated dependencies documentation
        """
        logger.info(f"Generating dependencies documentation for {repo_data['owner']}/{repo_data['name']}")
        
        system_prompt = (
            "You are a senior AI technical writer generating a DEPENDENCIES.md file for a GitHub repository.\n\n"
            
            "Use markdown with proper formatting:\n"
            "- Use a single `#` for the document title\n"
            "- Use `##`, `###` for section headers (don't skip levels)\n"
            "- Add blank lines before and after headings, lists, code blocks, and tables\n"
            "- Use proper table formatting with blank lines before and after\n"
            "- Avoid trailing whitespace and punctuation in headings\n\n"
            "Group dependencies based on type and provide useful metadata.\n\n"
            
            "### Runtime Dependencies\n"
            "| Package | Description | Required | Version |\n"
            "|---------|-------------|----------|----------|\n\n"
            
            "### Development Dependencies\n"
            "| Package | Description | Required | Version |\n\n"
            
            "### Optional Dependencies\n"
            "| Package | Purpose | Optional? |\n\n"
            
            "### Environment Variables\n"
            "| Variable | Purpose | Required | Example |\n\n"
            
            "### External Services\n"
            "List APIs or platforms the project connects to (e.g., OpenAI, Redis, MongoDB). Include doc URLs if available.\n\n"
            
            "✅ Infer purpose from pyproject.toml, requirements.txt, imports, or web snippets.\n"
            "✅ Use `[Assumed]` if the purpose isn't clearly stated.\n"
            "✅ Don't duplicate or hallucinate packages.\n"
            "✅ Try to include version constraints if available.\n"
        )
        
        # Extract dependencies
        dependencies = self._extract_dependencies(repo_data)
        
        # Prepare user prompt
        user_prompt = f"# Repository Information\n\n"
        user_prompt += f"Repository: {repo_data['owner']}/{repo_data['name']}\n"
        user_prompt += f"Description: {repo_data.get('description', 'No description provided')}\n\n"
        
        # Add requirements file content if available
        if repo_data.get("requirements") and repo_data["requirements"].get("content"):
            user_prompt += f"# Requirements File: {repo_data['requirements']['name']}\n\n"
            user_prompt += self._truncate_content(repo_data["requirements"]["content"], max_chars=2000)
            user_prompt += "\n\n"
        
        # Add extracted dependencies
        if dependencies:
            user_prompt += "# Extracted Dependencies\n\n"
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
                env_matches = re.findall(r'(?:os\.environ(?:\.|\.get\()|\bgetenv\(|\bdotenv)[\'"]([A-Z0-9_]+)[\'"]', content)
                for match in env_matches:
                    if match not in env_vars:
                        env_vars.append(match)
        
        if env_vars:
            user_prompt += "# Environment Variables\n\n"
            for var in env_vars:
                user_prompt += f"- {var}\n"
            user_prompt += "\n\n"
        
        # Look for .env or .env.example files
        env_file_content = ""
        for file in repo_data.get("root_files", []):
            if file.get("path") in [".env.example", ".env.sample", ".env.template"]:
                env_file_content = file.get("content", "")
                user_prompt += f"# Environment File: {file['path']}\n\n"
                user_prompt += self._truncate_content(env_file_content, max_chars=1000)
                user_prompt += "\n\n"
                break
        
        # Try to categorize dependencies
        runtime_deps = []
        dev_deps = []
        
        # Check setup.py or pyproject.toml for dependency categorization
        for file in repo_data.get("root_files", []):
            if file.get("path") == "setup.py" and file.get("content"):
                content = file.get("content", "")
                # Extract install_requires for runtime deps
                install_requires = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if install_requires:
                    deps_str = install_requires.group(1)
                    deps = re.findall(r'[\'\"](.*?)[\'\"]', deps_str)
                    runtime_deps.extend(deps)
                
                # Extract extras_require for dev deps
                extras_require = re.search(r'extras_require\s*=\s*{[^}]*?[\'"]dev[\'"]:\s*\[(.*?)\]', content, re.DOTALL)
                if extras_require:
                    deps_str = extras_require.group(1)
                    deps = re.findall(r'[\'\"](.*?)[\'\"]', deps_str)
                    dev_deps.extend(deps)
            
            elif file.get("path") == "pyproject.toml" and file.get("content"):
                content = file.get("content", "")
                # Extract dependencies for runtime deps
                deps_section = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if deps_section:
                    deps_str = deps_section.group(1)
                    deps = re.findall(r'[\'\"](.*?)[\'\"]', deps_str)
                    runtime_deps.extend(deps)
                
                # Extract dev-dependencies for dev deps
                dev_deps_section = re.search(r'dev-dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if dev_deps_section:
                    deps_str = dev_deps_section.group(1)
                    deps = re.findall(r'[\'\"](.*?)[\'\"]', deps_str)
                    dev_deps.extend(deps)
        
        if runtime_deps:
            user_prompt += "# Runtime Dependencies\n\n"
            for dep in runtime_deps:
                user_prompt += f"- {dep}\n"
            user_prompt += "\n\n"
        
        if dev_deps:
            user_prompt += "# Development Dependencies\n\n"
            for dep in dev_deps:
                user_prompt += f"- {dep}\n"
            user_prompt += "\n\n"
        
        # Check for web search results
        web_search_results = repo_data.get("web_search_results", "")
        
        # Add web search results to prompt if available
        if web_search_results:
            user_prompt += f"""
            
            # Additional information from web search:
            {web_search_results}
            """
        
        # Generate dependencies documentation
        dependencies_doc = self._make_completion_request(system_prompt, user_prompt, temperature=0.2)
        
        # Format as Markdown
        return f"# Dependencies\n\n{dependencies_doc}"
