"""
Construe - Obsidian Context MCP Server

A FastMCP server that extracts and concatenated personal context from an Obsidian vault
using frontmatter properties and tags for filtering.
"""

import argparse
from pathlib import Path
from typing import Dict, List, Any
from fastmcp import FastMCP
import obsidian_utils

# Create the MCP server
mcp = FastMCP("Construe")

# Global configuration storage
_config = None
_config_path = None


def load_config() -> Dict[str, Any]:
    """Load configuration with caching."""
    global _config, _config_path
    
    if _config is not None:
        return _config
    
    if _config_path is None:
        script_dir = Path(__file__).parent
        _config_path = script_dir / "config.yaml"
    
    _config = obsidian_utils.load_config(_config_path)
    return _config


@mcp.tool(
    name="fetch_context",
    description="Load context files from Obsidian vault by context type - specify 'personal', 'work', or any custom context",
    tags={"obsidian", "context", "load"}
)
def fetch_context(context_type: str) -> str:
    """
    Fetch context files based on context type.
    
    Args:
        context_type: The context value to match in frontmatter properties (e.g., 'personal', 'work')
    
    Returns:
        Concatenated content of all files matching the context type
    """
    try:
        config = load_config()
        vault_path = Path(config['vault_path']).expanduser().resolve()
        
        if not vault_path.exists():
            return f"Error: Vault path does not exist: {vault_path}"
        
        if not vault_path.is_dir():
            return f"Error: Vault path is not a directory: {vault_path}"
        
        # Use the context_type parameter to filter by context property
        properties = {"context": context_type}
        tags = []
        
        matching_files = obsidian_utils.find_matching_files(vault_path, properties, tags)
        return obsidian_utils.concatenate_files(matching_files)
        
    except Exception as e:
        return f"Error fetching {context_type} context: {str(e)}"


@mcp.tool(
    name="fetch_matching_files", 
    description="Fetch files from Obsidian vault matching custom properties and tags criteria",
    tags={"obsidian", "search", "filter"}
)
def fetch_matching_files(
    properties: Dict[str, Any] = None,
    tags: List[str] = None,
    match_all_tags: bool = False
) -> str:
    """
    Fetch files matching specified properties and tags.
    
    Args:
        properties: Dictionary of frontmatter properties to match (AND logic)
        tags: List of tags to match (OR logic by default, AND if match_all_tags=True)
        match_all_tags: If True, require ALL specified tags; if False, require ANY tag
        
    Returns:
        Concatenated content of all matching files, sorted by modification date
    """
    try:
        config = load_config()
        vault_path = Path(config['vault_path']).expanduser().resolve()
        
        if not vault_path.exists():
            return f"Error: Vault path does not exist: {vault_path}"
        
        if not vault_path.is_dir():
            return f"Error: Vault path is not a directory: {vault_path}"
        
        properties = properties or {}
        tags = tags or []
        
        matching_files = obsidian_utils.find_matching_files(vault_path, properties, tags, match_all_tags)
        return obsidian_utils.concatenate_files(matching_files)
        
    except Exception as e:
        return f"Error fetching matching files: {str(e)}"


@mcp.resource("config://vault-info")
def get_vault_info() -> Dict[str, Any]:
    """
    Get information about the configured Obsidian vault.
    
    Returns:
        Dictionary with vault path and basic statistics
    """
    try:
        config = load_config()
        vault_path = Path(config['vault_path']).expanduser().resolve()
        
        info = obsidian_utils.get_vault_info(vault_path)
        if "error" not in info:
            info["default_context"] = config.get('default_context', {})
        
        return info
        
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construe - Obsidian Context MCP Server")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    
    args = parser.parse_args()
    
    # Set the global config path before starting the server
    _config_path = Path(args.config).resolve()
    
    mcp.run()
