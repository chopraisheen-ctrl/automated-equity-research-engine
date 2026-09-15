import os
import sys
import math
import requests
import yfinance as yf
import matplotlib.pyplot as plt

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# PROJECT SETTINGS
# ============================================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

SEC_EMAIL = os.getenv("SEC_EMAIL")

SEC_HEADERS = {
    "User-Agent": f"FinanceProject1 {SEC_EMAIL}"
}

# ============================================================
# DCF ASSUMPTIONS
# ============================================================
#
# These are model assumptions.
# They are NOT facts pulled from the company.
#
# You can change these later when building company-specific
# valuation scenarios.
# ============================================================

DCF_YEARS = 5

DCF_GROWTH_RATE = 0.05
DCF_WACC = 0.09
DCF_TERMINAL_GROWTH = 0.025


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_billions(value):

    if value is None:
        return "Unavailable"

    return (
        f"${value / 1_000_000_000:.2f}B"
    )


def format_money(value):

    if value is None:
        return "Unavailable"

    return f"${value:,.2f}"


def format_percent(value):

    if value is None:
        return "Unavailable"

    return f"{value * 100:.2f}%"


def format_multiple(value):

    if value is None:
        return "Unavailable"

    return f"{value:.2f}x"


def safe_number(value):

    try:

        if value is None:
            return None

        if math.isnan(float(value)):
            return None

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return None


# ============================================================
# FIND LATEST SEC 10-K
# ============================================================

def get_sec_filing(
    ticker_symbol
):

    tickers_url = (
        "https://www.sec.gov/files/"
        "company_tickers.json"
    )

    response = requests.get(
        tickers_url,
        headers=SEC_HEADERS,
        timeout=30
    )

    response.raise_for_status()

    tickers_data = (
        response.json()
    )

    cik = None

    for company in tickers_data.values():

        if (
            company["ticker"].upper()
            ==
            ticker_symbol.upper()
        ):

            cik = str(
                company["cik_str"]
            ).zfill(10)

            break

    if cik is None:
        return None

    submissions_url = (
        "https://data.sec.gov/"
        f"submissions/CIK{cik}.json"
    )

    response = requests.get(
        submissions_url,
        headers=SEC_HEADERS,
        timeout=30
    )

    response.raise_for_status()

    submissions = (
        response.json()
    )

    recent_filings = (
        submissions["filings"]["recent"]
    )

    forms = (
        recent_filings["form"]
    )

    accession_numbers = (
        recent_filings[
            "accessionNumber"
        ]
    )

    primary_documents = (
        recent_filings[
            "primaryDocument"
        ]
    )

    for i, form in enumerate(
        forms
    ):

        if form == "10-K":

            accession = (
                accession_numbers[i]
                .replace("-", "")
            )

            document = (
                primary_documents[i]
            )

            filing_url = (
                "https://www.sec.gov/"
                "Archives/edgar/data/"
                f"{int(cik)}/"
                f"{accession}/"
                f"{document}"
            )

            return filing_url

    return None


# ============================================================
# DOWNLOAD SEC FILING
# ============================================================

def download_sec_filing_text(
    filing_url
):

    response = requests.get(
        filing_url,
        headers=SEC_HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    for element in soup([
        "script",
        "style",
        "noscript"
    ]):

        element.decompose()

    text = soup.get_text(
        separator="\n"
    )

    cleaned_lines = []

    for line in text.splitlines():

        cleaned_line = (
            line.strip()
        )

        if cleaned_line:

            cleaned_lines.append(
                cleaned_line
            )

    return "\n".join(
        cleaned_lines
    )


# ============================================================
# EXTRACT 10-K SECTION
# ============================================================

def extract_filing_section(
    filing_text,
    start_terms,
    end_terms,
    max_characters=40000
):

    if not filing_text:
        return None

    upper_text = (
        filing_text.upper()
    )

    start_positions = []

    for term in start_terms:

        search_position = 0

        while True:

            position = (
                upper_text.find(
                    term.upper(),
                    search_position
                )
            )

            if position == -1:
                break

            start_positions.append(
                position
            )

            search_position = (
                position
                + len(term)
            )

    if not start_positions:
        return None

    # Prefer later occurrence to avoid
    # table-of-contents headings.
    start_position = max(
        start_positions
    )

    end_position = None

    for term in end_terms:

        position = (
            upper_text.find(
                term.upper(),
                start_position + 500
            )
        )

        if position != -1:

            if (
                end_position is None
                or
                position < end_position
            ):

                end_position = (
                    position
                )

    if end_position is None:

        end_position = (
            start_position
            + max_characters
        )

    section = filing_text[
        start_position:
        end_position
    ]

    return section[
        :max_characters
    ]


# ============================================================
# DCF MODEL
# ============================================================

def run_dcf(
    base_free_cash_flow,
    cash,
    debt,
    shares_outstanding
):

    if (
        base_free_cash_flow is None
        or
        shares_outstanding is None
        or
        shares_outstanding <= 0
        or
        base_free_cash_flow <= 0
    ):

        return None

    projected_fcfs = []

    current_fcf = (
        base_free_cash_flow
    )

    present_value_fcfs = 0

    for year in range(
        1,
        DCF_YEARS + 1
    ):

        current_fcf = (
            current_fcf
            *
            (1 + DCF_GROWTH_RATE)
        )

        discounted_fcf = (
            current_fcf
            /
            (
                (1 + DCF_WACC)
                ** year
            )
        )

        present_value_fcfs += (
            discounted_fcf
        )

        projected_fcfs.append({
            "year": year,
            "fcf": current_fcf,
            "present_value": discounted_fcf
        })

    final_year_fcf = (
        projected_fcfs[-1]["fcf"]
    )

    terminal_value = (
        final_year_fcf
        *
        (
            1
            + DCF_TERMINAL_GROWTH
        )
        /
        (
            DCF_WACC
            - DCF_TERMINAL_GROWTH
        )
    )

    discounted_terminal_value = (
        terminal_value
        /
        (
            (1 + DCF_WACC)
            ** DCF_YEARS
        )
    )

    enterprise_value = (
        present_value_fcfs
        +
        discounted_terminal_value
    )

    cash_value = (
        cash
        if cash is not None
        else 0
    )

    debt_value = (
        debt
        if debt is not None
        else 0
    )

    equity_value = (
        enterprise_value
        + cash_value
        - debt_value
    )

    intrinsic_value_per_share = (
        equity_value
        /
        shares_outstanding
    )

    return {
        "projected_fcfs":
            projected_fcfs,

        "terminal_value":
            terminal_value,

        "discounted_terminal_value":
            discounted_terminal_value,

        "enterprise_value":
            enterprise_value,

        "equity_value":
            equity_value,

        "intrinsic_value_per_share":
            intrinsic_value_per_share
    }


# ============================================================
# USER INPUT
# ============================================================

ticker_symbol = input(
    "Enter stock ticker: "
).strip().upper()


if not ticker_symbol:

    print(
        "No ticker entered."
    )

    sys.exit()


ticker = yf.Ticker(
    ticker_symbol
)


# ============================================================
# GET FINANCIAL DATA
# ============================================================

print(
    "\nLoading company data..."
)

try:

    info = ticker.info

    income_statement = (
        ticker.financials
    )

except Exception as error:

    print(
        "Unable to download financial data:"
    )

    print(error)

    sys.exit()


# ============================================================
# VALIDATE TICKER
# ============================================================

if (
    income_statement is None
    or
    income_statement.empty
    or
    "Total Revenue"
    not in income_statement.index
):

    print(
        "\nUnable to find financial "
        "statements for this ticker."
    )

    print(
        "Make sure you enter only "
        "the ticker symbol."
    )

    print(
        "Example: NKE"
    )

    sys.exit()


# ============================================================
# COMPANY INFORMATION
# ============================================================

company_name = (
    info.get(
        "longName",
        ticker_symbol
    )
)

current_price = safe_number(
    info.get(
        "currentPrice"
    )
)

market_cap = safe_number(
    info.get(
        "marketCap"
    )
)

shares_outstanding = safe_number(
    info.get(
        "sharesOutstanding"
    )
)


# ============================================================
# VALUATION MULTIPLES
# ============================================================

trailing_pe = safe_number(
    info.get(
        "trailingPE"
    )
)

forward_pe = safe_number(
    info.get(
        "forwardPE"
    )
)

price_to_sales = safe_number(
    info.get(
        "priceToSalesTrailing12Months"
    )
)

enterprise_to_ebitda = safe_number(
    info.get(
        "enterpriseToEbitda"
    )
)


# ============================================================
# FINANCIAL STATEMENTS
# ============================================================

revenue = (
    income_statement.loc[
        "Total Revenue"
    ]
)

operating_income = (
    income_statement.loc[
        "Operating Income"
    ]
)

net_income = (
    income_statement.loc[
        "Net Income"
    ]
)


if (
    "EBITDA"
    in income_statement.index
):

    ebitda = (
        income_statement.loc[
            "EBITDA"
        ]
    )

else:

    ebitda = None


# ============================================================
# CASH FLOW / DEBT
# ============================================================

cash = safe_number(
    info.get(
        "totalCash"
    )
)

debt = safe_number(
    info.get(
        "totalDebt"
    )
)

free_cash_flow = safe_number(
    info.get(
        "freeCashflow"
    )
)

operating_cash_flow = safe_number(
    info.get(
        "operatingCashflow"
    )
)


# ============================================================
# BASIC RATIOS
# ============================================================

latest_revenue = safe_number(
    revenue.iloc[0]
)

latest_ebitda = None

if ebitda is not None:

    latest_ebitda = safe_number(
        ebitda.iloc[0]
    )


if (
    cash is not None
    and
    debt is not None
):

    net_debt = (
        debt - cash
    )

else:

    net_debt = None


if (
    cash is not None
    and
    debt is not None
    and
    debt != 0
):

    cash_to_debt = (
        cash / debt
    )

else:

    cash_to_debt = None


if (
    free_cash_flow is not None
    and
    latest_revenue is not None
    and
    latest_revenue != 0
):

    fcf_margin = (
        free_cash_flow
        /
        latest_revenue
    )

else:

    fcf_margin = None


if (
    debt is not None
    and
    latest_ebitda is not None
    and
    latest_ebitda != 0
):

    debt_to_ebitda = (
        debt
        /
        latest_ebitda
    )

else:

    debt_to_ebitda = None


# ============================================================
# SEC 10-K
# ============================================================

print(
    "\n--- SEC FILING ---"
)

sec_filing_url = None
filing_text = None
risk_factors = None
mda = None


try:

    sec_filing_url = (
        get_sec_filing(
            ticker_symbol
        )
    )

    if sec_filing_url:

        print(
            "Latest 10-K:",
            sec_filing_url
        )

        print(
            "\nDownloading 10-K..."
        )

        filing_text = (
            download_sec_filing_text(
                sec_filing_url
            )
        )

        print(
            "10-K downloaded successfully."
        )

        print(
            "Characters downloaded:",
            len(filing_text)
        )


        risk_factors = (
            extract_filing_section(

                filing_text,

                [
                    "ITEM 1A. RISK FACTORS",
                    "ITEM 1A RISK FACTORS"
                ],

                [
                    "ITEM 1B",
                    "ITEM 1C",
                    "ITEM 2"
                ]
            )
        )


        mda = (
            extract_filing_section(

                filing_text,

                [
                    "ITEM 7. MANAGEMENT'S DISCUSSION",
                    "ITEM 7 MANAGEMENT'S DISCUSSION",
                    "MANAGEMENT'S DISCUSSION AND ANALYSIS"
                ],

                [
                    "ITEM 7A",
                    "ITEM 8"
                ]
            )
        )


        print(
            "\n--- SEC SECTION CHECK ---"
        )


        if risk_factors:

            print(
                "Risk Factors found:",
                len(risk_factors),
                "characters"
            )

        else:

            print(
                "Risk Factors not found."
            )


        if mda:

            print(
                "MD&A found:",
                len(mda),
                "characters"
            )

        else:

            print(
                "MD&A not found."
            )


    else:

        print(
            "No 10-K found."
        )


except Exception as error:

    print(
        "SEC filing unavailable:",
        error
    )


# ============================================================
# COMPANY SNAPSHOT
# ============================================================

print(
    "\n--- STOCK NARRATIVE ENGINE ---"
)

print(
    "Company:",
    company_name
)

print(
    "Ticker:",
    ticker_symbol
)

print(
    "Current Price:",
    format_money(
        current_price
    )
)

print(
    "Market Cap:",
    format_billions(
        market_cap
    )
)


# ============================================================
# BALANCE SHEET / CASH FLOW
# ============================================================

print(
    "\n--- BALANCE SHEET & CASH FLOW ---"
)

print(
    "Cash:",
    format_billions(
        cash
    )
)

print(
    "Total Debt:",
    format_billions(
        debt
    )
)

print(
    "Operating Cash Flow:",
    format_billions(
        operating_cash_flow
    )
)

print(
    "Free Cash Flow:",
    format_billions(
        free_cash_flow
    )
)


# ============================================================
# FINANCIAL HEALTH RATIOS
# ============================================================

print(
    "\n--- FINANCIAL HEALTH RATIOS ---"
)

print(
    "Net Debt:",
    format_billions(
        net_debt
    )
)

print(
    "FCF Margin:",
    format_percent(
        fcf_margin
    )
)

print(
    "Debt / EBITDA:",
    format_multiple(
        debt_to_ebitda
    )
)

print(
    "Cash / Debt:",
    format_multiple(
        cash_to_debt
    )
)


# ============================================================
# VALUATION MULTIPLES
# ============================================================

print(
    "\n--- VALUATION MULTIPLES ---"
)

print(
    "Trailing P/E:",
    format_multiple(
        trailing_pe
    )
)

print(
    "Forward P/E:",
    format_multiple(
        forward_pe
    )
)

print(
    "Price / Sales:",
    format_multiple(
        price_to_sales
    )
)

print(
    "EV / EBITDA:",
    format_multiple(
        enterprise_to_ebitda
    )
)


# ============================================================
# MULTI-YEAR FINANCIAL TREND
# ============================================================

series_lengths = [
    len(revenue),
    len(operating_income),
    len(net_income)
]

if ebitda is not None:

    series_lengths.append(
        len(ebitda)
    )


years_to_analyze = min(
    4,
    *series_lengths
)


print(
    "\n--- MULTI-YEAR FINANCIAL TREND ---"
)


for i in range(
    years_to_analyze
):

    year = (
        revenue.index[i].year
    )

    rev = safe_number(
        revenue.iloc[i]
    )

    op_income = safe_number(
        operating_income.iloc[i]
    )

    ni = safe_number(
        net_income.iloc[i]
    )

    if ebitda is not None:

        ebitda_value = safe_number(
            ebitda.iloc[i]
        )

    else:

        ebitda_value = None


    if (
        rev is not None
        and
        rev != 0
    ):

        op_margin = (
            op_income / rev
            if op_income is not None
            else None
        )

        net_margin = (
            ni / rev
            if ni is not None
            else None
        )

        ebitda_margin = (
            ebitda_value / rev
            if ebitda_value is not None
            else None
        )

    else:

        op_margin = None
        net_margin = None
        ebitda_margin = None


    print(
        f"\nYear: {year}"
    )

    print(
        "Revenue:",
        format_billions(
            rev
        )
    )

    print(
        "Operating Income:",
        format_billions(
            op_income
        )
    )

    print(
        "Net Income:",
        format_billions(
            ni
        )
    )

    print(
        "EBITDA:",
        format_billions(
            ebitda_value
        )
    )

    print(
        "Operating Margin:",
        format_percent(
            op_margin
        )
    )

    print(
        "Net Margin:",
        format_percent(
            net_margin
        )
    )

    print(
        "EBITDA Margin:",
        format_percent(
            ebitda_margin
        )
    )


# ============================================================
# REVENUE GROWTH
# ============================================================

print(
    "\n--- REVENUE GROWTH ---"
)

revenue_growth_values = []


for i in range(
    years_to_analyze - 1
):

    current_revenue = safe_number(
        revenue.iloc[i]
    )

    previous_revenue = safe_number(
        revenue.iloc[i + 1]
    )

    current_year = (
        revenue.index[i].year
    )

    previous_year = (
        revenue.index[i + 1].year
    )


    if (
        current_revenue is not None
        and
        previous_revenue is not None
        and
        previous_revenue != 0
    ):

        growth = (
            current_revenue
            -
            previous_revenue
        ) / previous_revenue

        revenue_growth_values.append(
            growth
        )

        print(
            f"{previous_year} "
            f"to {current_year}: "
            f"{growth * 100:.2f}%"
        )


# ============================================================
# DCF VALUATION
# ============================================================

dcf_result = run_dcf(
    free_cash_flow,
    cash,
    debt,
    shares_outstanding
)


print(
    "\n--- DCF VALUATION ---"
)


if dcf_result:

    intrinsic_value = (
        dcf_result[
            "intrinsic_value_per_share"
        ]
    )


    if (
        current_price is not None
        and
        current_price != 0
    ):

        implied_upside = (
            intrinsic_value
            /
            current_price
            - 1
        )

    else:

        implied_upside = None


    print(
        "Base Free Cash Flow:",
        format_billions(
            free_cash_flow
        )
    )

    print(
        "Forecast Period:",
        DCF_YEARS,
        "years"
    )

    print(
        "FCF Growth Assumption:",
        format_percent(
            DCF_GROWTH_RATE
        )
    )

    print(
        "Discount Rate / WACC:",
        format_percent(
            DCF_WACC
        )
    )

    print(
        "Terminal Growth Rate:",
        format_percent(
            DCF_TERMINAL_GROWTH
        )
    )

    print(
        "DCF Enterprise Value:",
        format_billions(
            dcf_result[
                "enterprise_value"
            ]
        )
    )

    print(
        "DCF Equity Value:",
        format_billions(
            dcf_result[
                "equity_value"
            ]
        )
    )

    print(
        "Estimated Intrinsic Value:",
        format_money(
            intrinsic_value
        ),
        "per share"
    )

    print(
        "Current Price:",
        format_money(
            current_price
        )
    )

    if implied_upside is not None:

        print(
            "Implied Upside / Downside:",
            format_percent(
                implied_upside
            )
        )


else:

    intrinsic_value = None
    implied_upside = None

    print(
        "DCF unavailable because "
        "required financial data "
        "was missing or free cash "
        "flow was negative."
    )


# ============================================================
# CREATE CHARTS
# ============================================================

os.makedirs(
    "charts",
    exist_ok=True
)


chart_years = []
revenues = []
operating_margins = []
net_margins = []


for i in range(
    years_to_analyze
):

    year = (
        revenue.index[i].year
    )

    rev = safe_number(
        revenue.iloc[i]
    )

    op_income = safe_number(
        operating_income.iloc[i]
    )

    ni = safe_number(
        net_income.iloc[i]
    )


    if (
        rev is None
        or
        rev == 0
    ):

        continue


    chart_years.append(
        year
    )

    revenues.append(
        rev
        /
        1_000_000_000
    )

    operating_margins.append(
        op_income
        /
        rev
        *
        100
    )

    net_margins.append(
        ni
        /
        rev
        *
        100
    )


chart_years.reverse()
revenues.reverse()
operating_margins.reverse()
net_margins.reverse()


# ============================================================
# REVENUE CHART
# ============================================================

plt.figure()

plt.plot(
    chart_years,
    revenues,
    marker="o"
)

plt.title(
    f"{company_name} Revenue"
)

plt.xlabel(
    "Year"
)

plt.ylabel(
    "Revenue ($B)"
)

plt.tight_layout()

plt.savefig(
    f"charts/"
    f"{ticker_symbol}_revenue.png"
)

plt.close()


# ============================================================
# MARGIN CHART
# ============================================================

plt.figure()

plt.plot(
    chart_years,
    operating_margins,
    marker="o",
    label="Operating Margin"
)

plt.plot(
    chart_years,
    net_margins,
    marker="o",
    label="Net Margin"
)

plt.title(
    f"{company_name} Profitability"
)

plt.xlabel(
    "Year"
)

plt.ylabel(
    "Margin (%)"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    f"charts/"
    f"{ticker_symbol}_margins.png"
)

plt.close()


print(
    "\nCharts created successfully."
)


# ============================================================
# BUILD DCF TEXT FOR AI
# ============================================================

if dcf_result:

    dcf_summary = f"""
DCF VALUATION

Base Free Cash Flow:
{format_billions(free_cash_flow)}

Forecast Period:
{DCF_YEARS} years

FCF Growth Assumption:
{format_percent(DCF_GROWTH_RATE)}

WACC:
{format_percent(DCF_WACC)}

Terminal Growth:
{format_percent(DCF_TERMINAL_GROWTH)}

DCF Enterprise Value:
{format_billions(dcf_result["enterprise_value"])}

DCF Equity Value:
{format_billions(dcf_result["equity_value"])}

Estimated Intrinsic Value Per Share:
{format_money(intrinsic_value)}

Current Market Price:
{format_money(current_price)}

Implied Upside / Downside:
{format_percent(implied_upside)}

IMPORTANT:
The DCF result is an illustrative model based on
explicit assumptions and should not be treated as
a factual company forecast.
"""

else:

    dcf_summary = """
DCF VALUATION

DCF valuation unavailable because required
financial information was unavailable.
"""


# ============================================================
# BUILD FINANCIAL SUMMARY FOR AI
# ============================================================

financial_summary = f"""
COMPANY

Company:
{company_name}

Ticker:
{ticker_symbol}

Current Price:
{format_money(current_price)}

Market Capitalization:
{format_billions(market_cap)}


FINANCIAL DATA

Latest Revenue:
{format_billions(safe_number(revenue.iloc[0]))}

Prior-Year Revenue:
{format_billions(safe_number(revenue.iloc[1]))}

Two-Years-Ago Revenue:
{format_billions(safe_number(revenue.iloc[2]))}

Latest Operating Margin:
{
format_percent(
    safe_number(operating_income.iloc[0])
    /
    safe_number(revenue.iloc[0])
)
}

Latest Net Margin:
{
format_percent(
    safe_number(net_income.iloc[0])
    /
    safe_number(revenue.iloc[0])
)
}

Cash:
{format_billions(cash)}

Total Debt:
{format_billions(debt)}

Operating Cash Flow:
{format_billions(operating_cash_flow)}

Free Cash Flow:
{format_billions(free_cash_flow)}

Net Debt:
{format_billions(net_debt)}

FCF Margin:
{format_percent(fcf_margin)}

Debt / EBITDA:
{format_multiple(debt_to_ebitda)}

Cash / Debt:
{format_multiple(cash_to_debt)}


VALUATION MULTIPLES

Trailing P/E:
{format_multiple(trailing_pe)}

Forward P/E:
{format_multiple(forward_pe)}

Price / Sales:
{format_multiple(price_to_sales)}

EV / EBITDA:
{format_multiple(enterprise_to_ebitda)}


SEC FILING

Latest SEC 10-K:
{
sec_filing_url
if sec_filing_url
else "Unavailable"
}
"""


# ============================================================
# ADD SEC TEXT
# ============================================================

sec_summary_text = ""


if risk_factors:

    sec_summary_text += f"""

SEC 10-K RISK FACTORS

{risk_factors[:12000]}
"""


if mda:

    sec_summary_text += f"""

SEC 10-K MANAGEMENT DISCUSSION & ANALYSIS

{mda[:12000]}
"""


# ============================================================
# AI ANALYSIS
# ============================================================

print(
    "\nGenerating AI equity research analysis..."
)


response = client.responses.create(

    model="gpt-5.6-luna",

    instructions="""
You are an equity research analyst.

Analyze only the financial data, valuation model,
and SEC filing text supplied to you.

Create a professional equity research report.

Use these sections:

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

Important rules:

- Do not invent company facts.
- Do not invent financial numbers.
- Clearly separate SEC filing statements from
  conclusions based on financial data.
- Treat DCF assumptions as model assumptions,
  not management forecasts.
- Explain whether the DCF indicates upside or
  downside, but do not present the result as certain.
- Do not issue personalized investment advice.
- If data is unavailable, say so.

Keep the report analytical and professional.
""",

    input=(
        financial_summary
        +
        dcf_summary
        +
        sec_summary_text
    )
)


ai_analysis = (
    response.output_text
)


# ============================================================
# PRINT AI ANALYSIS
# ============================================================

print(
    "\n--- AI EQUITY RESEARCH ANALYSIS ---"
)

print(
    ai_analysis
)


# ============================================================
# CREATE REPORT FOLDER
# ============================================================

os.makedirs(
    "reports",
    exist_ok=True
)


# ============================================================
# BUILD FINAL REPORT
# ============================================================

report = f"""
# {company_name} ({ticker_symbol})

## Automated Equity Research Report

---

## Company Snapshot

**Company:** {company_name}

**Ticker:** {ticker_symbol}

**Current Price:** {format_money(current_price)}

**Market Capitalization:** {format_billions(market_cap)}

**Shares Outstanding:** {
format_billions(shares_outstanding)
}

---

## Financial Snapshot

**Latest Revenue:** {
format_billions(
    safe_number(
        revenue.iloc[0]
    )
)
}

**Cash:** {format_billions(cash)}

**Total Debt:** {format_billions(debt)}

**Net Debt:** {format_billions(net_debt)}

**Operating Cash Flow:** {
format_billions(
    operating_cash_flow
)
}

**Free Cash Flow:** {
format_billions(
    free_cash_flow
)
}

**FCF Margin:** {
format_percent(
    fcf_margin
)
}

**Debt / EBITDA:** {
format_multiple(
    debt_to_ebitda
)
}

---

## Valuation Multiples

**Trailing P/E:** {
format_multiple(
    trailing_pe
)
}

**Forward P/E:** {
format_multiple(
    forward_pe
)
}

**Price / Sales:** {
format_multiple(
    price_to_sales
)
}

**EV / EBITDA:** {
format_multiple(
    enterprise_to_ebitda
)
}

---

## DCF Valuation

**Forecast Period:** {DCF_YEARS} years

**FCF Growth Assumption:** {
format_percent(
    DCF_GROWTH_RATE
)
}

**WACC:** {
format_percent(
    DCF_WACC
)
}

**Terminal Growth Rate:** {
format_percent(
    DCF_TERMINAL_GROWTH
)
}

**Estimated Intrinsic Value Per Share:** {
format_money(
    intrinsic_value
)
}

**Current Price:** {
format_money(
    current_price
)
}

**Implied Upside / Downside:** {
format_percent(
    implied_upside
)
}

> The DCF is an illustrative valuation model based on
> assumptions and is not a company forecast.

---

## Equity Research Analysis

{ai_analysis}

---

## SEC Filing

**Latest 10-K:**

{sec_filing_url if sec_filing_url else "Unavailable"}

---

## Generated Charts

Revenue:

`charts/{ticker_symbol}_revenue.png`

Profitability:

`charts/{ticker_symbol}_margins.png`

---

## Methodology

This project combines:

- Yahoo Finance financial data
- SEC EDGAR 10-K filings
- Historical financial trend analysis
- Financial ratio calculations
- Relative valuation multiples
- Discounted cash flow valuation
- Automated chart generation
- AI-assisted qualitative equity research

---

## Disclaimer

This report was created for educational and portfolio
purposes. Financial data and model assumptions may contain
errors or change over time. The DCF valuation is illustrative
and does not constitute investment advice.

---

*Generated automatically by the Stock Narrative Engine.*
"""


# ============================================================
# SAVE REPORT
# ============================================================

report_path = (
    "reports/"
    f"{ticker_symbol}"
    "_equity_research_report.md"
)


with open(
    report_path,
    "w",
    encoding="utf-8"
) as report_file:

    report_file.write(
        report
    )


print(
    "\n--- REPORT CREATED ---"
)

print(
    "Saved report:",
    report_path
)


# ============================================================
# FINISHED
# ============================================================

print(
    "\n======================================"
)

print(
    "STOCK NARRATIVE ENGINE COMPLETE"
)

print(
    "======================================"
)
