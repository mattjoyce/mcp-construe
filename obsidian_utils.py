"""
Obsidian Utilities - Core functionality for processing Obsidian vault files

This module provides functions for extracting frontmatter, searching files,
and concatenating content from Obsidian vaults based on properties and tags.
"""

import re
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from config.yaml.
    
    Args:
        config_path: Optional path to config file. If None, looks in current directory.
        
    Returns:
        Dictionary containing configuration data
        
    Raises:
        FileNotFoundError: If config.yaml doesn't exist
        yaml.YAMLError: If config.yaml is malformed
    """
    if config_path is None:
        config_path = Path("config.yaml")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing config.yaml: {e}")


def extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract YAML frontmatter from markdown content.
    
    Args:
        content: Full markdown file content
        
    Returns:
        Tuple of (frontmatter_dict, remaining_content)
        Returns empty dict if no valid frontmatter found
    """
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, content, re.DOTALL)
    
    if not match:
        return {}, content
    
    frontmatter_text = match.group(1)
    remaining_content = content[match.end():]
    
    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
        return frontmatter, remaining_content
    except yaml.YAMLError:
        return {}, content


def matches_criteria(
    frontmatter: Dict[str, Any], 
    properties: Dict[str, Any], 
    tags: List[str], 
    match_all_tags: bool = False
) -> bool:
    """
    Check if a file's frontmatter matches the specified criteria.
    
    Args:
        frontmatter: Parsed frontmatter dictionary
        properties: Key-value pairs that must match (AND logic)
        tags: List of tags to match
        match_all_tags: If True, require ALL tags (AND), else ANY tags (OR)
        
    Returns:
        True if file matches all criteria
    """
    for key, value in properties.items():
        if frontmatter.get(key) != value:
            return False
    
    if tags:
        file_tags = frontmatter.get('tags', [])
        
        if isinstance(file_tags, str):
            file_tags = [file_tags]
        elif not isinstance(file_tags, list):
            file_tags = []
        
        if match_all_tags:
            return all(tag in file_tags for tag in tags)
        else:
            return any(tag in file_tags for tag in tags)
    
    return True


def find_matching_files(
    vault_path: Path, 
    properties: Dict[str, Any], 
    tags: List[str], 
    match_all_tags: bool = False
) -> List[Tuple[Path, str]]:
    """
    Find all markdown files in vault that match the specified criteria.
    
    Args:
        vault_path: Path to Obsidian vault
        properties: Properties to match in frontmatter
        tags: Tags to match
        match_all_tags: Whether to require all tags vs any tags
        
    Returns:
        List of tuples (file_path, file_content) sorted by modification time
    """
    matching_files = []
    
    for md_file in vault_path.rglob("*.md"):
        if not md_file.is_file():
            continue
            
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frontmatter, _ = extract_frontmatter(content)
            
            if matches_criteria(frontmatter, properties, tags, match_all_tags):
                matching_files.append((md_file, content))
                
        except (IOError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read {md_file}: {e}")
            continue
    
    matching_files.sort(key=lambda x: x[0].stat().st_mtime)
    return matching_files


def concatenate_files(files: List[Tuple[Path, str]]) -> str:
    """
    Concatenate file contents with separator headers.
    
    Args:
        files: List of (file_path, content) tuples
        
    Returns:
        Concatenated string with file separators
    """
    if not files:
        return "No matching files found."
    
    result_parts = []
    
    for file_path, content in files:
        separator = "=" * 80
        result_parts.append(separator)
        result_parts.append(str(file_path.resolve()))
        result_parts.append(separator)
        result_parts.append(content)
        result_parts.append("")
    
    return "\n".join(result_parts)


def get_vault_info(vault_path: Path) -> Dict[str, Any]:
    """
    Get information about an Obsidian vault.
    
    Args:
        vault_path: Path to the vault
        
    Returns:
        Dictionary with vault path and basic statistics
    """
    if not vault_path.exists():
        return {"error": "Vault path does not exist"}
    
    md_files = list(vault_path.rglob("*.md"))
    
    return {
        "vault_path": str(vault_path),
        "exists": vault_path.exists(),
        "is_directory": vault_path.is_dir(),
        "markdown_files_count": len(md_files)
    }


def main():
    """CLI interface for obsidian utilities."""
    parser = argparse.ArgumentParser(
        description="Extract and concatenate context from Obsidian vault files"
    )
    parser.add_argument(
        "--vault", "-v", 
        type=Path,
        help="Path to Obsidian vault (overrides config)"
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Path to config file (default: config.yaml)"
    )
    parser.add_argument(
        "--property", "-p",
        action="append",
        help="Property filter in format key=value (can be used multiple times). Example: context=work"
    )
    parser.add_argument(
        "--tag", "-t",
        action="append",
        help="Tag to match (can be used multiple times)"
    )
    parser.add_argument(
        "--all-tags",
        action="store_true",
        help="Require ALL specified tags (default: ANY tag)"
    )
    parser.add_argument(
        "--use-default",
        action="store_true",
        help="Use default context from config file"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show vault information"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be in scope without outputting content"
    )
    
    args = parser.parse_args()
    
    try:
        # Load config
        config = load_config(args.config)
        
        # Get vault path
        if args.vault:
            vault_path = args.vault.expanduser().resolve()
        else:
            vault_path = Path(config['vault_path']).expanduser().resolve()
        
        if not vault_path.exists():
            print(f"Error: Vault path does not exist: {vault_path}")
            return 1
        
        if args.info:
            info = get_vault_info(vault_path)
            print(f"Vault: {info['vault_path']}")
            print(f"Markdown files: {info['markdown_files_count']}")
            return 0
        
        # Determine search criteria
        if args.use_default:
            default_context = config.get('default_context', {})
            properties = default_context.get('properties', {})
            tags = default_context.get('tags', [])
        else:
            # Parse properties from command line
            properties = {}
            if args.property:
                for prop in args.property:
                    if '=' in prop:
                        key, value = prop.split('=', 1)
                        properties[key.strip()] = value.strip()
                    else:
                        print(f"Warning: Invalid property format '{prop}', expected key=value")
            
            tags = args.tag or []
        
        # Find matching files
        matching_files = find_matching_files(vault_path, properties, tags, args.all_tags)
        
        # Output results
        if args.dry_run:
            print(f"Found {len(matching_files)} matching files:")
            for file_path, _ in matching_files:
                print(f"  {file_path}")
        else:
            result = concatenate_files(matching_files)
            print(result)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())