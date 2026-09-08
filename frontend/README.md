# RSE Market Reports

A full-stack application that converts Rwanda Stock Exchange (RSE) market reports into a clean, interactive dashboard and an organized Excel workbook.

The application extracts market data from RSE PDF and Excel reports, validates and normalizes the data, presents it through a dashboard, and allows users to export the processed information to Excel.

---

## Features

- Upload RSE market reports
- Support PDF and Excel reports
- Extract market and financial data automatically
- Normalize dates, numbers, percentages, and financial values
- Validate extracted data and identify genuine data-quality issues
- View market information through an interactive dashboard
- View equity, bond, trading, index, and exchange-rate data
- Export processed data to Excel
- Responsive interface for desktop, tablet, and mobile
- Light and dark themes
- Professional financial-reporting interface

---

## Data Covered

The application is designed to process the main sections of an RSE Market Report.

### Market Overview

- Equity turnover
- Bond turnover
- Number of deals
- Shares traded
- Repo market activity
- Market indices

### Equity Market

- ISIN
- Stock
- 12-month high/low
- Session high/low
- Closing price
- Previous price
- Change
- Volume
- Value

### Market Indices

- Rwanda Share Index (RSI)
- All Share Index (ALSI)

### Trading Statistics

- Shares traded
- Equity turnover
- Number of deals
- Market capitalization

### Bond Market

#### Government Bonds

- ISIN
- Status
- Security
- Maturity
- Coupon rate
- Closing price
- Previous price
- Bids
- Offers
- Bond traded

#### Corporate Bonds

- ISIN
- Security/issue
- Maturity
- Coupon rate
- Closing price
- Previous price
- Bids
- Offers
- Bond traded

### Bond Trades

Bond transaction information is extracted and presented separately from bond reference information.

### Exchange Rates

- Currency
- Buy rate
- Sell rate
- Average rate

---

# Architecture

The application uses a simple processing pipeline:

```text
                RSE Report
                    │
                    ▼
              File Upload
                    │
                    ▼
               Extraction
             PDF / Excel
                    │
                    ▼
                 Parsing
                    │
                    ▼
              Normalization
                    │
                    ▼
               Validation
                    │
              ┌─────┴─────┐
              ▼           ▼
          Dashboard      Excel