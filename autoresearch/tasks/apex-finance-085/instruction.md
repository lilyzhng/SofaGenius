You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

Build a fully diluted market capitalization and an enterprise value valuation analysis for Coinbase. Use only the attached Form 10-Q, attached Form 10-K, attached Coinbase share trading data, and the following assumptions.

Assumptions:
- Coinbase's share price as of October 14, 2025, is used for purposes of determining dilutive shares
- The volume-weighted average price (VWAP) is calculated using the closing share price and trading volume of each of the last 45 trading days (August 12, 2025, to October 14, 2025)
- Do not include unamortized debt discount, premium, and issuance costs in gross debt
- Do not include restricted cash and restricted short-term investments in cash and equivalents
- Do not include lease liabilities in debt-like items
- Do not double-count converts: if shares are included on an if-converted basis, exclude the item from debt; otherwise, include the item in debt
- Do not include the impact of capped calls on dilution  
- 100% of outstanding performance-based restricted stock units (PSUs) are dilutive
- Treat crypto assets not loaned, pledged as collateral, or held for operations as cash equivalents at their market value
- Treat crypto-denominated debt as debt at its market value
- The current market value per Bitcoin is $107,200
- The current market value per Ethereum is $3,875
- Other crypto assets are measured at their fair value from the balance sheet as of June 30, 2025  
- Define Gross Profit as revenue minus transaction expense

Report:
(a) Basic shares outstanding
(b) Total dilutive shares (impact of dilutive securities)
(c) Fully diluted shares outstanding 
(d) Fully diluted market capitalization (using VWAP)
(e) Enterprise value (be sure to consider strategic investments when calculating enterprise value)
(f) Enterprise value to last twelve months (LTM) June 30, 2025 Revenue
(g) Enterprise value to LTM June 30, 2025 Gross Profit
(h) Enterprise value to LTM June 30, 2025 Operating Income
(i) Fully diluted market capitalization (using VWAP) to LTM June 30, 2025 Revenue
(j) Fully diluted market capitalization (using VWAP) to LTM June 30, 2025 Net Income

Note: round final dollar figures to the nearest million, ratios to one decimal, and round shares to the nearest 0.1 million. Currency: USD (all monetary figures).

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
