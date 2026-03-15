# Connector References

This directory contains scraped API documentation and generated technical specifications for each connector.

## Directory Structure

Each connector has its own subdirectory:

```
references/
├── {connector_name}/
│   ├── 01_authentication.md          # Scraped: Auth documentation
│   ├── 02_create_payment.md          # Scraped: Payment creation docs
│   ├── 03_capture_payment.md         # Scraped: Capture docs
│   ├── ...                           # Scraped: Other endpoint docs
│   └── technical_specification.md    # Generated: Complete tech spec
└── README.md                         # This file
```

## Available Connector Specs

| Connector | Tech Spec | Scraped Docs | Status | Date |
|-----------|-----------|--------------|--------|------|
| Finix | Yes | Yes | Complete | 2026-03-10 |
| Paystack | Yes | Yes | Complete | 2026-03-15 |

## How to Add a New Connector

1. Create directory: `references/{connector_name}/`
2. Scrape documentation: Follow [link_fetcher.md](../link_fetcher.md)
3. Generate tech spec: Follow [techspec.md](../techspec.md)
4. Update this table with the new connector

## Notes

- Scraped markdown files are source-of-truth for API documentation
- Technical specifications are generated from the scraped files
- This directory is gitignored except for this README
