"""
Markdown Formatter Module

This module provides functions to format markdown files according to best practices
and fix common linting issues.
"""

import os
import re
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('markdown_formatter')

class MarkdownFormatter:
    """
    A class to format markdown files according to best practices
    and fix common linting issues.
    """
    
    def __init__(self):
        """Initialize the MarkdownFormatter."""
        pass
    
    def format_file(self, file_path: str) -> bool:
        """
        Format a markdown file according to best practices.
        
        Args:
            file_path: Path to the markdown file to format
            
        Returns:
            True if formatting was successful, False otherwise
        """
        try:
            logger.info(f"Formatting markdown file: {file_path}")
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply formatting rules
            formatted_content = self._format_content(content)
            
            # Write the formatted content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            logger.info(f"Successfully formatted: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error formatting file {file_path}: {str(e)}")
            return False
    
    def format_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, bool]:
        """
        Format all markdown files in a directory.
        
        Args:
            directory_path: Path to the directory containing markdown files
            recursive: Whether to recursively format files in subdirectories
            
        Returns:
            Dictionary mapping file paths to formatting success/failure
        """
        results = {}
        
        try:
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if file.lower().endswith('.md'):
                        file_path = os.path.join(root, file)
                        results[file_path] = self.format_file(file_path)
                
                if not recursive:
                    break
        except Exception as e:
            logger.error(f"Error formatting directory {directory_path}: {str(e)}")
        
        return results
    
    def _format_content(self, content: str) -> str:
        """
        Apply formatting rules to markdown content.
        
        Args:
            content: Markdown content to format
            
        Returns:
            Formatted markdown content
        """
        # Fix multiple top-level headings (MD025)
        content = self._fix_multiple_h1(content)
        
        # Fix heading increment (MD001)
        content = self._fix_heading_increment(content)
        
        # Fix spacing around headings (MD022)
        content = self._fix_heading_spacing(content)
        
        # Fix spacing around lists (MD032)
        content = self._fix_list_spacing(content)
        
        # Fix spacing around tables (MD058)
        content = self._fix_table_spacing(content)
        
        # Fix trailing whitespace (MD009)
        content = self._fix_trailing_whitespace(content)
        
        # Fix trailing punctuation in headings (MD026)
        content = self._fix_heading_punctuation(content)
        
        # Fix bare URLs (MD034)
        content = self._fix_bare_urls(content)
        
        # Fix spacing around code blocks (MD031)
        content = self._fix_code_block_spacing(content)
        
        # Fix code blocks without language specified (MD040)
        content = self._fix_code_block_language(content)
        
        # Fix duplicate headings (MD024)
        content = self._fix_duplicate_headings(content)
        
        # Fix multiple consecutive blank lines (MD012)
        content = self._fix_multiple_blank_lines(content)
        
        # Ensure file ends with a single newline (MD047)
        if not content.endswith('\n'):
            content += '\n'
        elif content.endswith('\n\n'):
            content = content.rstrip('\n') + '\n'
        
        return content
    
    def _fix_multiple_h1(self, content: str) -> str:
        """Fix multiple top-level headings (MD025)."""
        lines = content.split('\n')
        h1_found = False
        result = []
        
        for line in lines:
            if line.startswith('# '):
                if h1_found:
                    # Convert subsequent H1s to H2s
                    result.append('## ' + line[2:])
                else:
                    result.append(line)
                    h1_found = True
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def _fix_heading_increment(self, content: str) -> str:
        """Fix heading increment (MD001)."""
        lines = content.split('\n')
        result = []
        current_level = 0
        
        for line in lines:
            if line.startswith('#'):
                # Count the number of # at the beginning
                level = 0
                for char in line:
                    if char == '#':
                        level += 1
                    else:
                        break
                
                # Ensure heading level increments by at most 1
                if level > current_level + 1 and current_level > 0:
                    # Replace with a properly incremented heading
                    result.append('#' * (current_level + 1) + line[level:])
                else:
                    result.append(line)
                    current_level = level
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def _fix_heading_spacing(self, content: str) -> str:
        """Fix spacing around headings (MD022)."""
        lines = content.split('\n')
        result = []
        
        for i in range(len(lines)):
            line = lines[i]
            
            if line.startswith('#') and ' ' in line:  # It's a heading
                # Check if there's a blank line before (except for the first line)
                if i > 0 and lines[i-1].strip() != '':
                    result.append('')
                
                result.append(line)
                
                # Check if there's a blank line after (except for the last line)
                if i < len(lines) - 1 and lines[i+1].strip() != '':
                    result.append('')
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def _fix_list_spacing(self, content: str) -> str:
        """Fix spacing around lists (MD032)."""
        # Regular expressions for list items
        unordered_list_pattern = r'^(\s*)[*+-](\s+)'
        ordered_list_pattern = r'^(\s*)\d+\.(\s+)'
        
        lines = content.split('\n')
        result = []
        in_list = False
        
        for i in range(len(lines)):
            line = lines[i]
            is_list_item = re.match(unordered_list_pattern, line) or re.match(ordered_list_pattern, line)
            
            if is_list_item and not in_list:
                # Starting a new list, add a blank line before if needed
                if i > 0 and result and result[-1].strip() != '':
                    result.append('')
                in_list = True
            elif not is_list_item and in_list and line.strip() == '':
                # Empty line after a list item
                in_list = False
                # Add a blank line after the list if the next line isn't blank
                if i < len(lines) - 1 and lines[i+1].strip() != '':
                    result.append('')
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _fix_table_spacing(self, content: str) -> str:
        """Fix spacing around tables (MD058)."""
        # Regular expression for table header row and separator row
        table_pattern = r'^\|.*\|$'
        separator_pattern = r'^[\|\-:\s]+$'
        
        lines = content.split('\n')
        result = []
        in_table = False
        
        for i in range(len(lines)):
            line = lines[i]
            is_table_row = re.match(table_pattern, line) is not None
            is_separator = re.match(separator_pattern, line) is not None
            
            if (is_table_row or is_separator) and not in_table:
                # Starting a new table, add a blank line before if needed
                if i > 0 and result and result[-1].strip() != '':
                    result.append('')
                in_table = True
            elif in_table and not (is_table_row or is_separator):
                # Ending a table, add a blank line after if needed
                in_table = False
                if line.strip() != '':
                    result.append('')
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _fix_trailing_whitespace(self, content: str) -> str:
        """Fix trailing whitespace (MD009)."""
        lines = content.split('\n')
        result = []
        
        for line in lines:
            result.append(line.rstrip())
        
        return '\n'.join(result)
    
    def _fix_heading_punctuation(self, content: str) -> str:
        """Fix trailing punctuation in headings (MD026)."""
        lines = content.split('\n')
        result = []
        
        for line in lines:
            if line.startswith('#') and ' ' in line:
                # It's a heading, remove trailing punctuation
                heading_text = line.split(' ', 1)[1]
                if heading_text and heading_text[-1] in '.,;:!?':
                    line = line[:-1]
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _fix_bare_urls(self, content: str) -> str:
        """Fix bare URLs (MD034)."""
        # Regular expression for bare URLs
        url_pattern = r'(?<!\(|\[)https?://[^\s)>]+'
        
        # Replace bare URLs with Markdown links
        return re.sub(url_pattern, lambda m: f'[{m.group(0)}]({m.group(0)})', content)
    
    def _fix_code_block_spacing(self, content: str) -> str:
        """Fix spacing around code blocks (MD031)."""
        # Regular expression for fenced code blocks
        code_block_pattern = r'```(?:[a-zA-Z0-9]+)?\n'
        code_block_end_pattern = r'```\n'
        
        lines = content.split('\n')
        result = []
        in_code_block = False
        
        for i in range(len(lines)):
            line = lines[i]
            
            if line.startswith('```') and not in_code_block:
                # Starting a code block, add a blank line before if needed
                if i > 0 and result and result[-1].strip() != '':
                    result.append('')
                in_code_block = True
                result.append(line)
            elif line.strip() == '```' and in_code_block:
                # Ending a code block, add the line
                result.append(line)
                in_code_block = False
                
                # Add a blank line after if needed
                if i < len(lines) - 1 and lines[i+1].strip() != '':
                    result.append('')
            else:
                result.append(line)
        
        return '\n'.join(result)
        
    def _fix_duplicate_headings(self, content: str) -> str:
        """Fix duplicate headings (MD024)."""
        lines = content.split('\n')
        result = []
        heading_texts = {}
        
        # First pass: identify special patterns and build heading hierarchy
        document_title = None
        section_titles = []
        current_section = None
        current_subsection = None
        current_function = None
        heading_hierarchy = {}  # Maps line index to parent section/subsection/function
        
        for i, line in enumerate(lines):
            if line.startswith('# '):
                document_title = line[2:].strip()
                current_section = None
                current_subsection = None
                current_function = None
            elif line.startswith('## '):
                current_section = line[3:].strip()
                section_titles.append(current_section)
                current_subsection = None
                current_function = None
            elif line.startswith('### '):
                current_subsection = line[4:].strip()
                current_function = None
                # Check if this is a function or class definition
                if 'Function:' in current_subsection or 'Class:' in current_subsection:
                    # Extract the function or class name
                    if 'Function:' in current_subsection:
                        current_function = current_subsection.split('Function:')[1].strip()
                    else:
                        current_function = current_subsection.split('Class:')[1].strip()
                    # Remove backticks if present
                    current_function = current_function.strip('`')
            elif line.startswith('#### '):
                # Store the parent context for this heading
                heading_hierarchy[i] = (current_section, current_subsection, current_function)
        
        # Second pass: fix duplicate headings and ensure proper heading levels
        prev_heading_level = 0
        for i, line in enumerate(lines):
            if line.startswith('#') and ' ' in line:
                # It's a heading
                heading_level = 0
                for char in line:
                    if char == '#':
                        heading_level += 1
                    else:
                        break
                
                heading_text = line[heading_level:].strip()
                
                # Fix heading increment issues (MD001)
                if heading_level > prev_heading_level + 1 and prev_heading_level > 0:
                    heading_level = prev_heading_level + 1
                prev_heading_level = heading_level
                
                # Check if this heading text has been seen before
                if heading_text in heading_texts:
                    # If it's a duplicate, make it more descriptive
                    count = heading_texts[heading_text] + 1
                    heading_texts[heading_text] = count
                    
                    # Handle special cases
                    if heading_text.lower() == document_title.lower():
                        # Document title repeated as section - rename to "About"
                        new_heading_text = "About " + heading_text
                        result.append('#' * heading_level + ' ' + new_heading_text)
                    elif heading_text.lower() in ['example', 'examples']:
                        # For example headings, add context from parent section/function
                        if i in heading_hierarchy:
                            _, _, function_name = heading_hierarchy[i]
                            if function_name:
                                new_heading_text = f"Example: {function_name}"
                                result.append('#' * heading_level + ' ' + new_heading_text)
                            else:
                                # Try to use parent section/subsection
                                parent_section, parent_subsection, _ = heading_hierarchy[i]
                                if parent_subsection:
                                    new_heading_text = f"Example: {parent_subsection}"
                                    result.append('#' * heading_level + ' ' + new_heading_text)
                                elif parent_section:
                                    new_heading_text = f"Example: {parent_section}"
                                    result.append('#' * heading_level + ' ' + new_heading_text)
                                else:
                                    # Fall back to numbering if no context available
                                    new_heading_text = f"{heading_text} {count}"
                                    result.append('#' * heading_level + ' ' + new_heading_text)
                        else:
                            # Fall back to numbering for other example headings
                            new_heading_text = f"{heading_text} {count}"
                            result.append('#' * heading_level + ' ' + new_heading_text)
                    elif heading_text.lower() in ['usage', 'overview', 'modules', 'dependencies']:
                        # These are often used as both document title and section title
                        if heading_level == 1:  # It's a document title
                            result.append(line)
                        else:  # It's a section title
                            new_heading_text = "Detailed " + heading_text
                            result.append('#' * heading_level + ' ' + new_heading_text)
                    elif heading_text.lower() in ['import path', 'parameters', 'returns', 'example usage']:
                        # These are common headings that might be duplicated but should be kept with their parent context
                        if i in heading_hierarchy:
                            _, parent_subsection, _ = heading_hierarchy[i]
                            if parent_subsection:
                                new_heading_text = f"{heading_text} ({parent_subsection})"
                                result.append('#' * heading_level + ' ' + new_heading_text)
                            else:
                                # Fall back to numbering
                                new_heading_text = f"{heading_text} {count}"
                                result.append('#' * heading_level + ' ' + new_heading_text)
                        else:
                            # Fall back to numbering
                            new_heading_text = f"{heading_text} {count}"
                            result.append('#' * heading_level + ' ' + new_heading_text)
                    else:
                        # For other duplicates, add context if possible
                        if len(section_titles) > 0 and count <= len(section_titles):
                            # Use the current section title for context
                            section_context = section_titles[count - 1]
                            new_heading_text = f"{heading_text} ({section_context})"
                        else:
                            # Fall back to numbering
                            new_heading_text = f"{heading_text} {count}"
                        result.append('#' * heading_level + ' ' + new_heading_text)
                else:
                    # First occurrence of this heading text
                    heading_texts[heading_text] = 1
                    result.append('#' * heading_level + ' ' + heading_text)
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def _fix_multiple_blank_lines(self, content: str) -> str:
        """Fix multiple consecutive blank lines (MD012)."""
        # Replace 3 or more consecutive newlines with 2 newlines
        import re
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content
        
    def _fix_code_block_language(self, content: str) -> str:
        """Fix code blocks without language specified (MD040)."""
        import re
        
        # Pattern to match code blocks that don't have a language specified
        # This matches ```<newline> (no language after the backticks)
        pattern = r'```\s*\n'
        
        # Function to determine appropriate language based on code content
        def determine_language(code_block):
            # Extract the content of the code block
            code_content = code_block.strip()
            
            # Check for common language indicators
            if re.search(r'\bdef\b.*:|\bclass\b.*:', code_content):
                return 'python'
            elif re.search(r'\bfunction\b.*{|\bconst\b|\blet\b|\bvar\b|=>|\$\(', code_content):
                return 'javascript'
            elif re.search(r'<.*>.*</.*>|<.*/>|<!DOCTYPE', code_content):
                return 'html'
            elif re.search(r'\bbody\b.*{|\bmargin:|\bpadding:|\bcolor:', code_content):
                return 'css'
            elif re.search(r'\bSELECT\b|\bFROM\b|\bWHERE\b|\bJOIN\b', code_content, re.IGNORECASE):
                return 'sql'
            elif re.search(r'\bpackage\b|\bimport\b.*;|\bpublic\b.*class', code_content):
                return 'java'
            elif re.search(r'#include|int main\(|std::', code_content):
                return 'cpp'
            elif re.search(r'\bgit\b|\bapt-get\b|\bnpm\b|\byarn\b|\bpip\b', code_content):
                return 'bash'
            elif re.search(r'\{.*:.*\}|\[.*\]', code_content):
                return 'json'
            else:
                # Default to text if we can't determine the language
                return 'text'
        
        # Split the content by code block markers
        parts = re.split(r'(```(?:\w+)?\s*\n[\s\S]*?```)', content)
        
        result = []
        i = 0
        while i < len(parts):
            part = parts[i]
            
            # Check if this part is a code block without language
            if part.startswith('```') and re.match(pattern, part):
                # Find the end of the code block
                code_end = part.find('```', 3)
                if code_end != -1:
                    # Extract the code content
                    code_content = part[part.find('\n', 3):code_end]
                    # Determine the language
                    language = determine_language(code_content)
                    # Replace the opening ``` with ```language
                    new_part = f'```{language}\n{code_content}```'
                    result.append(new_part)
                else:
                    # If we can't find the end, just append as is
                    result.append(part)
            else:
                result.append(part)
            
            i += 1
        
        return ''.join(result)


def format_markdown_files(directory_path: str, recursive: bool = True) -> Dict[str, bool]:
    """
    Format all markdown files in a directory.
    
    Args:
        directory_path: Path to the directory containing markdown files
        recursive: Whether to recursively format files in subdirectories
        
    Returns:
        Dictionary mapping file paths to formatting success/failure
    """
    formatter = MarkdownFormatter()
    return formatter.format_directory(directory_path, recursive)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python markdown_formatter.py <directory_path> [--non-recursive]")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    recursive = "--non-recursive" not in sys.argv
    
    results = format_markdown_files(directory_path, recursive)
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"Formatted {success_count}/{total_count} markdown files successfully.")
