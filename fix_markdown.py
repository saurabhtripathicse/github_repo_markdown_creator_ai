#!/usr/bin/env python3
"""
Fix Markdown Script

This script fixes markdown formatting issues in documentation files
using the MarkdownFormatter class.
"""

import os
import sys
import argparse
from src.markdown_formatter import format_markdown_files

def main():
    """Main function to fix markdown formatting issues."""
    parser = argparse.ArgumentParser(description="Fix markdown formatting issues in documentation files.")
    parser.add_argument("--path", default="docs", help="Path to the directory containing markdown files (default: docs)")
    parser.add_argument("--recursive", action="store_true", default=True, help="Recursively format files in subdirectories (default: True)")
    parser.add_argument("--project-docs", action="store_true", help="Also format project documentation files in the root directory")
    
    args = parser.parse_args()
    
    # Format markdown files in the specified directory
    results = format_markdown_files(args.path, args.recursive)
    
    # Format project documentation files if requested
    if args.project_docs:
        project_docs = [
            "README.md",
            "OVERVIEW.md",
            "MODULES.md",
            "USAGE.md",
            "DEPENDENCIES.md",
            "PROJECT_DOCS.md",
            "TASK_LOG.md",
            "PROGRESS_TRACKING.md"
        ]
        
        for doc in project_docs:
            if os.path.exists(doc):
                from src.markdown_formatter import MarkdownFormatter
                formatter = MarkdownFormatter()
                success = formatter.format_file(doc)
                results[doc] = success
    
    # Print results
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"Formatted {success_count}/{total_count} markdown files successfully.")
    
    if success_count < total_count:
        print("\nFailed to format the following files:")
        for file_path, success in results.items():
            if not success:
                print(f"  - {file_path}")
    
    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())
