# Datapoint

Upload a document PDF, Excel, Word, CSV, or plain text and get back a clean, explorable
dashboard, plus an Excel export you can download. No manual parsing, no templates to fill in.

It started as a tool for reading Rwanda Stock Exchange (RSE) market reports, and RSE reports
still get their own specialized pipeline. Everything else sales data, HR spreadsheets, ops
reports, fuel logs, whatever goes through a generic engine that figures out the structure on
its own.

## What it does

1. **Detects the file type** and, for PDFs/Excel files, whether it's an RSE report or not.
2. **Extracts** the text, tables, or worksheets no interpretation yet, just getting the raw content out.
3. **RSE reports** go through a dedicated parser that knows the report's exact layout: equities,
   bonds, indices, exchange rates, market overview, the works.
4. **Everything else** goes through the generic engine, which infers what each column actually is
   (a currency, a date, a category, an ID...), profiles it, classifies the document type, and
   suggests metrics and charts that make sense for that data.
5. Both paths run through the same **validation** step before anything is shown, so a bad value
   gets flagged rather than silently displayed or exported.
6. The **dashboard and the Excel export always come from the same validated data** — there's no
   separate code path that could show one thing and export another.

No LLM is involved in producing any number you see. Everything traces back to a cell or line in
your original document. If a model gets added later, its job would be suggesting what a column
*means* not generating the numbers.

## Advanced Intelligence

Every dashboard has an "Investigate Document" button that runs a deeper, still fully
deterministic pass over the data no invented numbers here either:

- **Anomaly Radar** outliers, sudden jumps, totals that don't match their own rows.
- **Data Forensics** a 0–100 data-quality score based on missing values, duplicates, bad dates.
- **Discoveries** plain-language "what matters most" insights.
- **Explain This** shows the exact source rows behind any number on screen.
- **Entity graph & geographic view** relationships and locations, built only from your data.
- **Time Machine** compares two of your own reports side by side.
- **What-If Simulator** lets you project scenarios, clearly labeled as assumptions, never
  mixed in with real data.
- **AI Analyst** a chat that answers questions about your document using the modules above.

## Tech stack

- **Backend:** Django + DRF, PostgreSQL, pandas/NumPy for the number-crunching, pdfplumber /
  openpyxl / python-docx for reading files.
- **Frontend:** React + TypeScript + Vite, Tailwind, Recharts.

## Getting started

**Backend** — needs a local PostgreSQL server with a `datapoint` database created.

```bash
cd backend
python -m venv venv && source venv/bin/activate 
pip install -r requirements.txt
cp .env.example .env  
python manage.py migrate
python manage.py runserver
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open **http://rsemarketreports.localhost:5173** (plain `localhost` also works — see
`frontend/vite.config.ts` if you'd rather use a different hostname).

## Tests

```bash
cd backend
python manage.py test
```

132 tests, covering both pipelines and the intelligence layer — including a full regression
suite that checks every figure in the RSE dashboard against the real sample report.

## Current limitations

- No login or document history yet it's a single upload → dashboard flow, fine for local use,
  not for sharing with a team.
- No natural-language search over your data yet you filter and sort the tables directly.
- Scanned/image-only PDFs aren't supported (no OCR) the PDF needs a real text layer.
- Schema inference is heuristic an unusually named or irregular column may get flagged as
  low-confidence rather than confidently (and wrongly) labeled.

## What's next

1. Accounts and a saved-documents list.
2. A landing page in front of the upload flow.
3. An optional LLM layer for *interpreting* already-extracted data (summaries, better column
   naming, natural-language queries) never for producing the numbers themselves.
4. OCR support for scanned PDFs.