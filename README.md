# Datapoint

Upload a document — a PDF report, an Excel workbook, a Word document, a CSV export, or a plain text
file — and get back a structured, explorable dashboard and a clean Excel export, without hand-writing
a parser for every format.

The platform was built around Rwanda Stock Exchange (RSE) market reports, and RSE reports still get
a specialized, deeply verified pipeline (see [RSE support](#rse-support-first-class) below). But the
underlying engine — extraction → schema inference → validation → dashboard → export — is generic and
works on documents that have nothing to do with RSE: sales data, HR spreadsheets, operations reports
written in Word, fuel logs in a plain text file — any table-shaped content, whatever the file format.

---

## Product vision

```
ANY DOCUMENT → EXTRACT → UNDERSTAND → STRUCTURE → VALIDATE → VISUALIZE → EXPORT
```

The intelligence comes from the quality of deterministic extraction, schema inference, and validation
— not from an LLM guessing at numbers. No model is in the request path for the workflows this project
currently ships; every value shown in the dashboard or the exported workbook traces back to a cell or
line of text in the source document. See [Architectural principle](#architectural-principle) for why,
and [Roadmap](#roadmap--whats-not-built-yet) for where an LLM would fit in later.

---

## Supported document types

| Format | Extension | Status |
|---|---|---|
| PDF | `.pdf` | ✅ Text + table extraction (pdfplumber, with a PyMuPDF fallback) |
| Excel | `.xlsx`, `.xls`, `.xlsm` | ✅ Every non-empty worksheet is inspected |
| Word | `.docx` | ✅ Paragraphs, headings, and every table (`python-docx`), in true document order |
| CSV | `.csv` | ✅ Delimiter-sniffed, encoding-tolerant |
| Plain text | `.txt` | ✅ Best-effort: embedded delimited tables are detected; the rest becomes sections |

A PDF or Excel file that matches the shape of an RSE market report (recognized by its title text or
its worksheet names) is routed to the specialized RSE pipeline. Everything else — including every CSV,
DOCX, and TXT file, which can never be an RSE report — is routed to the generic document-intelligence
pipeline. No supported format is ever rejected just because it isn't RSE-shaped.

---

## How it works

```
 SOURCE FILE
     │
     ▼
 FILE TYPE DETECTION            services/pipeline.py
     │
     ▼
 EXTRACTION                     services/extraction/{pdf,excel,csv,docx,txt}_extractor.py
     │                          → raw text, tables, worksheets — no interpretation yet
     ▼
 RSE REPORT?  ──yes──▶  RSE PARSING PIPELINE (unchanged, RSE-specific)
     │no                services/parsers/*.py
     │  (CSV/DOCX/TXT always take this branch — they can never be RSE)
     ▼
 GENERIC DATASET BUILDING       services/documents/generic_parser.py
     │                          → every table becomes a Dataset; pandas DataFrames back the
     │                            per-column numeric/date coercion and whole-row duplicate detection
     ▼
 SCHEMA INFERENCE               services/documents/schema_inference.py
     │                          → each column classified: currency, date, category, identifier, …
     │                            (pandas/NumPy for the stats, dateutil for flexible date parsing)
     ▼
 DATASET PROFILING              (part of schema_inference — NumPy min/mean/max/std per column)
     ▼
 DOCUMENT CLASSIFICATION        services/documents/classification.py
     │                          → "Sales" / "HR" / "Financial" / … or "General dataset" if unsure
     ▼
 METRICS + CHART SUGGESTIONS    services/documents/metrics.py, charts.py
     │                          → sums/averages that make sense; a chart only when one clearly helps
     ▼
 VALIDATION                     services/documents/schemas.py (Pydantic structural check)
     │                          + services/documents/validate.py (business-rule warnings)
     │                          (services/normalization/validate_data.py plays both roles for RSE)
     │                          → flags real problems; never invents a value to fill a gap
     ▼
 API RESPONSE  ──────────────▶  REACT DASHBOARD (renders whichever schema it received)
     │
     ▼
 EXCEL EXPORT                   services/export/{excel,generic}_exporter.py
                                 → same validated data the dashboard showed, one sheet per dataset
```

The dashboard and the Excel export are always built from the same validated dict — there is no
separate code path that could show one thing on screen and export another.

### Architectural principle

Extraction is deterministic: regex and rule-based parsing for RSE's fixed report layout, and
name+value heuristics (not just column names) for the generic engine's schema inference — backed by
pandas/NumPy for the actual numeric coercion, aggregation, and duplicate-row detection, rather than
hand-rolled loops reimplementing what those libraries already do well. Every generic Document is then
validated against a Pydantic schema before it's returned, so a malformed field is caught as a clear
internal error at the source, not as a broken dashboard three layers downstream. No LLM sits in this
request path. If a future version adds one, its role would be semantic interpretation only —
suggesting what a column *means*, not producing the numbers themselves; the roadmap section below is
explicit about this boundary.

---

## RSE support (first-class)

The original use case — Rwanda Stock Exchange market reports (PDF or Excel) — has its own pipeline
under `services/parsers/` and is verified against the real sample reports on every test run:

- Market overview (equity/bond turnover and deal counts, shares traded, market capitalization, repo
  market activity)
- Equities (ISIN, 12-month and session high/low, closing/previous, change, volume, value)
- Market indices (RSI, ALSI, and any others the report publishes)
- Trading statistics (session-over-session comparison)
- Government bonds and corporate bonds (ISIN, security, maturity, coupon, prices, bids/offers)
- Bond trades (derived from bonds with a nonzero traded volume)
- Exchange rates (buying/selling/average per currency)

A known data-quality trap this pipeline handles correctly: some corporate bond issuers (e.g.
`MGMRW`) reuse the same short code across genuinely different bond series. Duplicate detection keys
on the full identifying tuple (code + security + maturity + coupon), not the code alone, so two
different issuances under the same code are correctly kept as separate records — see
`services/normalization/validate_data.py` and the regression tests in `backend/reports/tests.py`.

---

## Technology stack

**Backend** — Django + Django REST Framework, `pdfplumber`/PyMuPDF (PDF), `openpyxl` (Excel, both
reading and the exported workbook), `python-docx` (Word), Python's `csv` module (CSV and embedded
tables in TXT). `pandas`/`NumPy` back the generic engine's per-column numeric coercion, statistics
(min/mean/max/std), and whole-row duplicate detection; `python-dateutil` extends date recognition
beyond RSE's fixed formats for arbitrary documents; `Pydantic` validates the shape of every generic
Document before it leaves the pipeline. SQLite for local development.

**Frontend** — React + TypeScript + Vite, Tailwind CSS, Recharts, Axios.

No RAG, vector database, PostgreSQL, authentication, or microservices — none of the current workflows
need them (see [Roadmap](#roadmap--whats-not-built-yet) for what would justify adding authentication).

---

## Project structure

```
backend/
  config/                   Django settings, URLs
  reports/                  The one Django app: Report model, views, serializers, all tests
  services/
    extraction/             pdf_extractor.py, excel_extractor.py, csv_extractor.py, docx_extractor.py,
                             txt_extractor.py, table_extractor.py, text_extractor.py — read raw
                             content, no interpretation
    parsers/                RSE-specific: rse_parser.py (orchestrator, also home to the
                             RSE-vs-generic routing check) + one parser per section (stock, bond,
                             market, index, exchange_rate)
    documents/              Generic engine: model.py (Document/Dataset/Column), schemas.py (Pydantic
                             structural validation), schema_inference.py (pandas/NumPy/dateutil-backed),
                             classification.py, metrics.py, charts.py, generic_parser.py, validate.py
    normalization/          clean_data.py (shared value parsing), validate_data.py (RSE validation)
    export/                 xlsx_style.py (shared styling), excel_exporter.py (RSE),
                             generic_exporter.py (generic documents)
    pipeline.py             Wires it all together; the only place that decides RSE vs. generic
  sample_data/ (repo root)  Real RSE PDF/Excel samples, plus generic CSV, Excel, Word and TXT samples

frontend/
  src/
    pages/                  Home, Dashboard (router), RseDashboard, GenericDashboard
    components/
      dashboard/            RSE-specific dashboard sections and tables
      generic/              Generic dashboard: DatasetTable, DatasetChart, MetricsGrid, header
      common/               Shared: Card, Badge, EmptyState, ErrorMessage, SearchInput, ThemeToggle
      upload/               Drag-and-drop upload with progress states
    types/report.ts         TypeScript types for both schemas, discriminated by `extracted_data.kind`
    utils/                  formatters.ts, genericFormat.ts, chartColors.ts
```

---

## Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows; use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Local URL

The app is served at **http://rsemarketreports.localhost:5173** (API at
`http://rsemarketreports.localhost:8000`). Browsers resolve any `*.localhost` hostname to the loopback
address natively — no hosts-file entry is needed. This is configured in `frontend/vite.config.ts`
(`server.allowedHosts`), `frontend/.env` (`VITE_API_URL`), and `backend/config/settings.py`
(`CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`). Plain `localhost` still works if you prefer it.

---

## Development commands

| | Backend | Frontend |
|---|---|---|
| Run dev server | `python manage.py runserver` | `npm run dev` |
| Tests | `python manage.py test` | — |
| Type check | — | `npx tsc -b` |
| Lint | — | `npm run lint` |
| Production build | — | `npm run build` |
| Django checks | `python manage.py check` | — |

---

## Testing & data integrity

44 backend tests cover both pipelines:

- **RSE regression** (`backend/reports/tests.py`): every figure in the dashboard is cross-checked
  against the literal text of the real sample PDF — market overview, all equities, both index values,
  every exchange rate, every bond trade, and the MGMRW duplicate-detection fix (proving both the false
  positive is gone *and* a genuinely duplicated row is still caught).
- **Generic pipeline** (`backend/reports/test_generic_documents.py`): schema inference unit tests
  (currency/percentage/date/category/identifier detection), document classification, pandas-backed
  duplicate-row detection, and full upload→dashboard→Excel-export round trips against real CSV,
  multi-sheet Excel, Word (mixed text + two tables), and TXT (prose with an embedded table) samples.

Run everything with `python manage.py test` from `backend/`.

---

## Export

The download always reflects the exact data validated and shown on screen — dates are real Excel
dates, percentages use a literal `%`-suffix format (source values are already percentage points, so
Excel's native percent format would multiply by 100 and misdisplay them), numeric columns stay
numeric (never exported as text), and headers are frozen. RSE exports use the sheet names
`MARKET SUMMARY`, `STOCK`, `MARKET STATS`, `BONDS`, `BONDS TRADES`, `EXCHANGE RATE`, `INDICES`;
generic documents get one sheet per extracted dataset plus an `OVERVIEW` summary sheet.

---

## Limitations

- **No authentication, landing page, or account/document management UI.** The app is currently a
  single upload → dashboard flow with no login; every report/document is visible to anyone who can
  reach the app. Fine for local/single-user use, not for a shared deployment.
- **No natural-language assistant.** Asking the dashboard a question in plain English ("which region
  performed best?") isn't implemented — today you filter/sort/search the extracted tables directly.
- Schema inference is heuristic, not exhaustive: unusual column naming or highly irregular tables may
  be classified with low confidence (reported honestly as such) rather than confidently mislabeled.
- Chart suggestions favor clarity over coverage: a dataset with no clear date or low-cardinality
  category column intentionally gets no chart, only a table.
- TXT heading/table detection is inherently best-effort on the least structured input format: a
  heading is recognized when it stands alone (blank line on both sides), and a table when consecutive
  lines share a delimiter and field count — documents that don't follow either convention still come
  through as plain paragraph sections rather than being dropped, just without the extra structure.
- OCR (scanned/image-only PDFs) is not implemented — extraction assumes the PDF has a real text layer.

## Roadmap — what's not built yet

Recommended next steps, roughly in order of value:

1. **Authentication + a documents list** — accounts, a saved-documents page, and the app shell
   (sidebar navigation, settings) needed once more than one person/session uses the same instance.
2. **A public landing page** — marketing/onboarding surface in front of the current upload flow.
3. **LLM-assisted semantic layer** (optional, additive) — for *interpreting* structure already
   extracted deterministically: better column-name suggestions, a short plain-language document
   summary, or a natural-language query answered by looking up the already-extracted datasets. It
   should never be the source of a numeric value shown to the user.
4. **OCR fallback** for scanned/image-only PDFs, using the same PdfExtractionResult shape so nothing
   downstream needs to change.
