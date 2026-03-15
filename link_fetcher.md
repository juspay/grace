# Link Fetcher -- Playwright MCP Web Scraping

Instructions for scraping connector API documentation into clean markdown using the Playwright MCP server.

> **Prerequisite**: Playwright MCP server must be configured. See [codegen.md](codegen.md#playwright-mcp-server) for setup instructions.

---

## Purpose

Scrape one or more API documentation URLs and convert them to clean, structured markdown files. These files serve as input for tech spec generation (see [techspec.md](techspec.md)).

---

## Process

### Step 1: Navigate to the URL

Use the Playwright MCP `browser_navigate` tool to open the target URL:

```
browser_navigate({ url: "https://docs.example.com/api/payments" })
```

Wait for the page to fully load. For SPA/JavaScript-heavy documentation sites, the page may need additional time to render.

### Step 2: Extract Main Content

Use `browser_snapshot` to capture the page content as structured text:

```
browser_snapshot()
```

This returns the accessible content of the page including text, links, and structural elements.

### Step 3: Convert to Clean Markdown

From the snapshot, extract and structure the relevant content into markdown. Focus on:

**Include:**
- API endpoint URLs and HTTP methods
- Request headers (with types and descriptions)
- Request body structure (complete JSON with field descriptions)
- Response body structure (complete JSON with field descriptions)
- Authentication details
- Status codes and error responses
- cURL examples (if present)
- Code samples (if relevant)
- Rate limits and constraints

**Exclude:**
- Navigation menus and sidebars
- Footer content
- Advertisements and promotional material
- Cookie banners
- UI chrome (breadcrumbs, search bars, etc.)

### Step 4: Handle Multi-Page Documentation

Most connector APIs have documentation spread across multiple pages. For each page:

1. Navigate to the page
2. Extract content
3. Save as a separate markdown file
4. Move to the next page

Name files descriptively:
```
references/{connector_name}/01_authentication.md
references/{connector_name}/02_create_payment.md
references/{connector_name}/03_capture_payment.md
references/{connector_name}/04_refunds.md
references/{connector_name}/05_webhooks.md
```

### Step 5: Save Output

Save all scraped markdown files to:
```
references/{connector_name}/
```

> **Note:** All paths are relative to the grace project root.

---

## Safety and Limits

### URL Validation
Before scraping any URL, verify:
1. The URL uses `https://` (reject plain `http://` unless explicitly requested by the user)
2. The URL points to a documentation domain, not an internal/private IP address
3. Do NOT follow redirects to localhost, 127.0.0.1, 10.x.x.x, 172.16-31.x.x, or 192.168.x.x ranges (SSRF prevention)

### Scraping Limits
To avoid excessive resource usage:
- **Maximum pages per connector:** 30 (ask user for confirmation if more are needed)
- **Maximum total scraping time:** 10 minutes per connector
- **Pause between navigations:** 2-3 seconds minimum
- If you encounter rate limiting (HTTP 429), back off exponentially

---

## Edge Cases

### JavaScript-Heavy / SPA Pages

Some documentation sites (e.g., ReadMe.io, Stoplight) render content via JavaScript. If `browser_snapshot` returns minimal content:

1. Use `browser_wait_for_text` or wait a few seconds after navigation
2. Try `browser_evaluate` to check if content has loaded
3. Scroll down to trigger lazy-loaded content

### Authentication-Gated Documentation

If documentation requires login:

1. Inform the user that the documentation requires authentication
2. Ask the user to provide session cookies or pre-authenticated access
3. Alternatively, ask the user to manually save the pages and provide file paths instead of URLs

### PDF Documentation

If the connector provides API documentation as PDF:

1. Download the PDF using `browser_navigate` to the PDF URL
2. Extract text content from the PDF
3. Structure into markdown format
4. Note: PDF extraction may lose formatting -- flag sections that need manual review

### Rate Limiting

When scraping multiple pages from the same domain:

1. Add a brief pause (2-3 seconds) between page navigations
2. If you encounter rate limiting (HTTP 429), increase the pause interval
3. Respect robots.txt directives

### Paginated API References

Some API docs paginate their endpoint listings:

1. Check for pagination controls (next/previous buttons)
2. Navigate through all pages sequentially
3. Ensure no endpoints are missed

---

## Worked Example

**Input:** Scrape Finix payment API documentation

**Step 1:** Navigate to `https://docs.finix.com/api/authorizations`

**Step 2:** Extract and structure into markdown

**Expected output format** (saved to `references/finix/01_authorizations.md`):

```markdown
# Create an Authorization

**Endpoint:** `POST /authorizations`

**Description:** Create an Authorization to process a transaction (also known as a card hold).

**Request Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Finix-Version | string | Yes | Specify the API version. Default: `2022-02-01` |
| Content-Type | string | Yes | Must be `application/json` |

**Request Body:**
{
  "amount": 100,
  "currency": "USD",
  "merchant": "MUsVtN9pH65nGw61H7Nv8Apo",
  "source": "PIkxmtueemLD6dN9ZoWGHT44",
  "tags": {
    "order_number": "21DFASJSAKAS"
  }
}

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| amount | integer (int64) | Yes | Total amount to be debited in cents (e.g., 100 cents = $1.00) |
| currency | string | Yes | ISO 4217 3-letter currency code |
| merchant | string | Yes | ID of the Merchant the Authorization was created under |
| source | string | Yes | ID of the Payment Instrument where funds get debited |
| tags | object or null | No | Up to 50 key: value pairs for custom metadata |

**cURL Example:**
curl -i -X POST \
  -u US_EXAMPLE_USER_ID:00000000-0000-0000-0000-000000000000 \
  https://finix.sandbox-payments-api.com/authorizations \
  -H 'Content-Type: application/json' \
  -H 'Finix-Version: 2022-02-01' \
  -d '{
    "amount": 100,
    "currency": "USD",
    "merchant": "MU_EXAMPLE_MERCHANT_ID",
    "source": "PI_EXAMPLE_INSTRUMENT_ID"
  }'

**Response Codes:** 201, 400, 401, 402, 403, 404, 406, 422
```

Key qualities of good output:
- **Exact field names and types** from the documentation (never invent or assume)
- **Complete request/response bodies** with all fields documented
- **cURL examples** preserved verbatim when available
- **Status codes and error responses** included
- **No navigation/UI elements** in the output
