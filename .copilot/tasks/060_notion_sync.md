# Task 060: Notion Synchronization

## Goal

Implement synchronization between the repository prompts/documentation and Notion for team collaboration and visibility.

## Files to Create/Edit

### New Files
- `scripts/register_prompt_notion.sh` - Bash script to sync prompts to Notion
- `scripts/notion_sync.py` - Python implementation for Notion API integration
- `.github/workflows/notion-sync.yml` - GitHub Actions workflow for automated sync
- `tests/scripts/test_notion_sync.py` - Tests for Notion sync functionality

### Supporting Files
- `requirements.txt` - Add `notion-client` package
- `.env.example` - Example environment variables

## Requirements

### Functional Requirements

1. **Prompt Synchronization**
   - Sync `prompts/legendary_lidlift_v14.md` to Notion page
   - Sync capsule summaries to Notion database
   - Preserve markdown formatting
   - Include metadata (version, last updated)

2. **GitHub Actions Integration**
   - Trigger sync on push to main branch
   - Manual workflow dispatch option
   - Only sync when relevant files change
   - Report sync status in workflow

3. **Notion API Integration**
   - Use Notion API v2
   - Handle authentication securely via secrets
   - Update existing pages or create new ones
   - Handle rate limiting gracefully

4. **Error Handling**
   - Graceful failures (don't block main workflow)
   - Retry transient errors
   - Log sync status and errors
   - Notify on persistent failures

### Acceptance Criteria
- [ ] `register_prompt_notion.sh` script working
- [ ] Python Notion client implemented
- [ ] GitHub Actions workflow created
- [ ] Sync triggered on relevant file changes
- [ ] Markdown formatting preserved in Notion
- [ ] Error handling and retries implemented
- [ ] Tests for Notion sync logic
- [ ] Documentation for setup

## Implementation Guidance

```bash
#!/bin/bash
# scripts/register_prompt_notion.sh

set -euo pipefail

NOTION_API_KEY="${NOTION_API_KEY:-}"
NOTION_PAGE_ID="${NOTION_PAGE_ID:-}"

if [ -z "$NOTION_API_KEY" ] || [ -z "$NOTION_PAGE_ID" ]; then
    echo "Error: NOTION_API_KEY and NOTION_PAGE_ID must be set"
    exit 1
fi

# Call Python script for actual sync
python scripts/notion_sync.py \
    --api-key "$NOTION_API_KEY" \
    --page-id "$NOTION_PAGE_ID" \
    --file "prompts/legendary_lidlift_v14.md"
```

```python
# scripts/notion_sync.py
from notion_client import Client
import argparse
import sys

def sync_to_notion(api_key: str, page_id: str, markdown_file: str):
    """Sync markdown file to Notion page"""
    notion = Client(auth=api_key)
    
    with open(markdown_file, 'r') as f:
        content = f.read()
    
    # Convert markdown to Notion blocks
    blocks = markdown_to_notion_blocks(content)
    
    # Update Notion page
    notion.blocks.children.append(page_id, children=blocks)
    
    print(f"Successfully synced {markdown_file} to Notion")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--page-id", required=True)
    parser.add_argument("--file", required=True)
    args = parser.parse_args()
    
    sync_to_notion(args.api_key, args.page_id, args.file)
```

## GitHub Actions Workflow

```yaml
# .github/workflows/notion-sync.yml
name: Notion Sync

on:
  push:
    branches: [main]
    paths:
      - 'prompts/**'
      - 'capsules/**'
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install notion-client
          
      - name: Sync to Notion
        env:
          NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
          NOTION_PAGE_ID: ${{ secrets.NOTION_PAGE_ID }}
        run: |
          bash scripts/register_prompt_notion.sh
```

## Configuration

Secrets to add in GitHub repository settings:
- `NOTION_API_KEY`: Notion integration token
- `NOTION_PAGE_ID`: Target Notion page ID

## References
- Notion API Documentation: https://developers.notion.com/
- notion-client Python SDK: https://github.com/ramnes/notion-sdk-py
