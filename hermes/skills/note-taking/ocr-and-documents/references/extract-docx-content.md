---
name: extract-docx-content
description: Extract text content from DOCX files without LibreOffice/pandoc using unzip and sed
version: 1.0.0
tags: [documents, docx, extraction, text-processing]
---

# Extract Content from DOCX Files

## When to Use

When you need to extract text content from .docx files but don't have LibreOffice, pandoc, or python-docx available in the environment.

## Method

DOCX files are actually ZIP archives containing XML files. The main content is in `word/document.xml`.

### Basic Extraction

```bash
cd /tmp && unzip -p "/path/to/file.docx" word/document.xml 2>/dev/null | sed 's/<[^>]*>//g'
```

### With Head Limit (first N lines)

```bash
cd /tmp && unzip -p "/path/to/file.docx" word/document.xml 2>/dev/null | sed 's/<[^>]*>//g' | head -200
```

### Batch Processing Multiple Files

```bash
for file in /path/to/docs/*.docx; do
    echo "=== $(basename "$file") ==="
    unzip -p "$file" word/document.xml 2>/dev/null | sed 's/<[^>]*>//g' | head -100
    echo ""
done
```

## Limitations

- Output is plain text without formatting
- May contain some XML artifacts if sed pattern doesn't catch all tags
- Does not preserve images, tables, or styling
- Chinese filenames need proper quoting

## Alternative: Check for Tools First

Always check if proper tools are available before using this workaround:

```bash
which libreoffice || which pandoc || which docx2txt || echo "Using fallback method"
```

## Integration with Analysis Workflows

This method works well for:
1. Extracting content from multiple documents for analysis
2. Building domain-specific knowledge frameworks
3. Summarizing large document collections
4. Creating structured data from unstructured documents

## Example: Comprehensive Analysis Pattern

```python
# Pseudo-code for document analysis workflow
1. List all .docx files in target directory
2. Extract content from each using unzip+sed method
3. Read extracted content from multiple files in parallel
4. Analyze and synthesize common themes/frameworks
5. Compile into structured knowledge base
6. Save to memory for future reference
```