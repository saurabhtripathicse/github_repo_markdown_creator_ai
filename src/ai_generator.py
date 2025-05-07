"""
AI Generator Module

This module serves as a compatibility layer for the enhanced AI Generator.
It imports and re-exports the enhanced version to maintain backward compatibility.
"""

import logging
import warnings
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_generator')

# Import the enhanced AI Generator
try:
    from .ai_generator_enhanced import AIGenerator as EnhancedAIGenerator
    
    # Re-export the enhanced version as AIGenerator
    AIGenerator = EnhancedAIGenerator
    logger.info("Using enhanced AI Generator for documentation generation")
    
except ImportError:
    # Fallback implementation if the enhanced version is not available
    warnings.warn(
        "Enhanced AI Generator not found. Using a minimal implementation. "
        "Please ensure ai_generator_enhanced.py is in the src directory.",
        ImportWarning
    )
    
    # Define a minimal AIGenerator class for backward compatibility
    class AIGenerator:
        """Generator for AI-powered documentation"""
        
        def __init__(self):
            """Initialize AI Generator"""
            logger.warning("Using minimal AIGenerator implementation. Some features may be limited.")
        
        def generate_docs_content(self, repo_data: Dict[str, Any]) -> Dict[str, str]:
            """Generate documentation content for a repository
            
            Args:
                repo_data: Repository data
                
            Returns:
                Dictionary mapping filenames to content
            """
            logger.error("Minimal AIGenerator implementation cannot generate documentation.")
            logger.error("Please ensure ai_generator_enhanced.py is in the src directory.")
            
            # Return minimal documentation
            return {
                "OVERVIEW.md": f"# {repo_data.get('full_name', 'Repository')} Overview\n\nThis is a placeholder overview.",
                "MODULES.md": "# Modules Documentation\n\nThis is a placeholder for modules documentation.",
                "USAGE.md": "# Usage Guide\n\nThis is a placeholder for usage documentation.",
                "DEPENDENCIES.md": "# Dependencies\n\nThis is a placeholder for dependencies documentation."
            }
