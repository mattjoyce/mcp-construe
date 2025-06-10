# mcp-construe
A FastMCP server that loads personal context from Obsidian vaults using frontmatter filtering - curate your knowledge for AI conversations.

## Usage

### Basic Usage
```bash
python3 mcp-construe.py
```

### Custom Configuration
```bash
python3 mcp-construe.py --config other-config.yaml
python3 mcp-construe.py --config /path/to/custom-config.yaml
```

### Configuration
Create a `config.yaml` file in the same directory as the script:

```yaml
vault_path: "/path/to/obsidian/vault"
default_context:
  properties:
    context: "personal"
  tags: []
```

## Tools

- **fetch_context(context_type)** - Load files by context type (e.g., 'personal', 'work')
- **fetch_matching_files(properties, tags, match_all_tags)** - Flexible filtering by properties and tags
