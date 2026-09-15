# Automated Equity Research Engine

Python-based automated equity research, SEC filing analysis, financial modeling, and DCF valuation engine.

## Overview

The Automated Equity Research Engine allows a user to enter a stock ticker and automatically generate a structured financial and qualitative analysis of a public company.

The program:

1. Retrieves company financial data
2. Finds the latest SEC 10-K filing
3. Downloads and processes the filing
4. Extracts Risk Factors and Management's Discussion & Analysis
5. Calculates financial ratios
6. Analyzes multi-year financial trends
7. Calculates valuation multiples
8. Performs an illustrative DCF valuation
9. Generates financial charts
10. Uses AI to produce a structured equity research report
11. Automatically saves the final report

---

## Features

### Financial Analysis

The program analyzes:

- Revenue
- Operating income
- Net income
- EBITDA
- Operating margin
- Net margin
- EBITDA margin
- Revenue growth
- Operating cash flow
- Free cash flow
- Free cash flow margin
- Cash
- Debt
- Net debt
- Debt / EBITDA
- Cash / Debt

### SEC 10-K Analysis

The project connects to SEC EDGAR and automatically retrieves the latest available 10-K filing.

It extracts and analyzes:

- Item 1A — Risk Factors
- Item 7 — Management's Discussion & Analysis

### Valuation Multiples

The program retrieves:

- Trailing P/E
- Forward P/E
- Price / Sales
- EV / EBITDA

### Discounted Cash Flow Valuation

The project includes a simplified five-year DCF model.

Current default assumptions:

```text
Forecast Period: 5 years
Free Cash Flow Growth: 5.0%
WACC: 9.0%
Terminal Growth Rate: 2.5%
```

The DCF estimates:

- Enterprise value
- Equity value
- Intrinsic value per share
- Implied upside or downside

These assumptions are illustrative and are not company forecasts.

---

## Example Output

Example ticker:

```text
NKE
```

Example valuation output:

```text
--- VALUATION MULTIPLES ---
Trailing P/E: 17.33x
Forward P/E: 15.90x
Price / Sales: 1.16x
EV / EBITDA: 11.56x

--- DCF VALUATION ---
Base Free Cash Flow: $1.89B
Forecast Period: 5 years
FCF Growth Assumption: 5.00%
Discount Rate / WACC: 9.00%
Terminal Growth Rate: 2.50%
DCF Enterprise Value: $33.17B
DCF Equity Value: $31.15B
Estimated Intrinsic Value: $25.91 per share
Current Price: $36.40
Implied Upside / Downside: -28.80%
```

---

## AI Equity Research Report

The AI-generated report includes:

1. Executive Summary
2. Revenue Trend
3. Profitability Trend
4. Margin Analysis
5. Cash Flow
6. Balance Sheet and Liquidity
7. Management Commentary
8. Major 10-K Risk Factors
9. Financial Strengths
10. Financial Risks
11. Valuation Multiples
12. DCF Valuation
13. Bull Case
14. Bear Case
15. Key Catalysts
16. Overall Investment View

---

## Project Structure

```text
automated-equity-research-engine/
│
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
├── .env
│
├── charts/
│   ├── NKE_revenue.png
│   └── NKE_margins.png
│
└── reports/
    └── NKE_equity_research_report.md
```

---

## Technologies Used

- Python
- yfinance
- SEC EDGAR
- Requests
- BeautifulSoup
- Matplotlib
- OpenAI API
- python-dotenv

---

## Installation

Clone the repository:

```bash
git clone https://github.com/chopraisheen-ctrl/automated-equity-research-engine.git
```

Enter the project folder:

```bash
cd automated-equity-research-engine
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project folder.

Add:

```text
OPENAI_API_KEY=your_openai_api_key_here
SEC_EMAIL=your_email@example.com
```

Do not upload your `.env` file to GitHub.

---

## Running the Program

Run:

```bash
python main.py
```

When prompted:

```text
Enter stock ticker:
```

enter only the ticker symbol.

Example:

```text
NKE
```

The program will automatically perform the financial analysis, SEC filing analysis, valuation, chart generation, and AI equity research workflow.

---

## Output

The program creates:

```text
charts/NKE_revenue.png
charts/NKE_margins.png
reports/NKE_equity_research_report.md
```

---

## Workflow

```text
Stock Ticker
      ↓
Financial Data
      ↓
Financial Statements
      ↓
Financial Ratios
      ↓
Historical Trend Analysis
      ↓
SEC EDGAR
      ↓
Latest 10-K
      ↓
Risk Factors + MD&A
      ↓
Valuation Multiples
      ↓
DCF Valuation
      ↓
Charts
      ↓
AI Equity Research
      ↓
Automated Research Report
```

---

## Data Sources

Financial and market data:

- Yahoo Finance through yfinance

Official company filings:

- U.S. Securities and Exchange Commission
- SEC EDGAR

---

## Skills Demonstrated

This project demonstrates experience with:

- Python
- Corporate finance
- Equity research
- Financial statement analysis
- Financial modeling
- DCF valuation
- Financial ratio analysis
- SEC filing research
- API integration
- HTML parsing
- Data visualization
- AI integration
- Automation
- Report generation
- Error handling

---

## Limitations

This project is intended for educational and portfolio purposes.

Important limitations include:

- Financial data may be delayed or incomplete
- Financial statement formatting may differ between companies
- SEC filing formatting varies between companies
- Automated section extraction may not work perfectly for every company
- DCF valuation is highly sensitive to assumptions
- The current DCF model is simplified
- AI-generated analysis may contain errors
- Financial information should be independently verified

---

## Future Improvements

Potential improvements include:

- DCF sensitivity analysis
- Bear / base / bull valuation scenarios
- Comparable-company analysis
- Peer valuation comparison
- Automated WACC calculation
- FRED macroeconomic data
- Earnings-call transcript analysis
- Quarterly 10-Q analysis
- PDF report generation
- Interactive dashboard
- Streamlit interface

---

## Why I Built This Project

I built this project to develop practical skills in corporate finance, equity research, financial modeling, Python, and AI-assisted financial analysis.

Rather than analyzing one company manually, I wanted to build a reusable workflow that could take a stock ticker and automatically perform much of the initial research process.

The project helped me combine financial analysis, SEC filing research, valuation, programming, data visualization, and AI into one automated workflow.

---

## Disclaimer

This software and all reports produced by it are for educational and portfolio purposes only.

Nothing generated by this project constitutes investment, financial, legal, or tax advice.

Financial data may be inaccurate, incomplete, delayed, or subject to change.

DCF valuations and other estimates depend on assumptions and should not be interpreted as guaranteed fair values or future stock prices.

Users should independently verify all information before making financial decisions.

---

## Author

**Ishaan Chopra**

Finance student interested in:

- Corporate Finance
- Equity Research
- Financial Analysis
- Financial Modeling
- AI in Finance
- Fashion and Luxury Industry Finance
