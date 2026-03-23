You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

Build a fully diluted market capitalization and an enterprise value valuation analysis for Ford Motor Company, excluding the Ford Credit segment. Use only the attached filings and the following assumptions.

Assumptions:
- Ford Motor Company's current share price is $11.92 (as of October 17, 2025)
- Ford Credit's net equity value is equal to its total assets minus its total liabilities and is deducted from Ford Motor Company's fully diluted market capitalization
- Ford Credit has zero pension liabilities and zero OPEB liabilities
- For the Enterprise Value calculation, adjust the reported gross debt figure by adding back unamortized debt discount, premium, and issuance costs
- Do not include restricted cash or restricted short-term investments in cash and equivalents
- Do not include lease liabilities in debt
- Do not double-count convertible notes: if shares are included on an if-converted basis, exclude the item from debt; otherwise, include the item in debt
- 100% of outstanding restricted stock units ("RSUs") and restricted stock shares ("RSSs") are dilutive
- The weighted-average exercise price on outstanding stock options is $10.60
- Free Cash Flow ("FCF") is calculated as net cash provided by operating activities - capital expenditures
- Unlevered Free Cash Flow ("UFCF") is calculated as FCF + interest expense on Company debt excluding Ford Credit * (1 - 21.0% tax rate)
- EBITDA is calculated as operating income + depreciation and amortization 
- All last twelve months ("LTM") financial metrics (Revenue, Operating Income, EBITDA, Net Income Attributable to Ford Motor Company, FCF, and UFCF) exclude Ford Credit


Report:
(a) Basic shares outstanding
(b) Total dilutive shares (impact of dilutive securities)
(c) Fully diluted shares outstanding 
(d) Fully diluted market capitalization excluding Ford Credit ("Ford Auto FD Market Cap")
(e) Enterprise value excluding Ford Credit ("Ford Auto EV")
(f) Ford Auto EV to LTM June 30, 2025 Revenue
(g) Ford Auto EV to LTM June 30, 2025 Operating Income
(h) Ford Auto EV to LTM June 30, 2025 EBITDA
(i) Ford Auto EV to LTM June 30, 2025 UFCF
(j) Ford Auto FD Market Cap to LTM June 30, 2025 Revenue
(k) Ford Auto FD Market Cap to LTM June 30, 2025 Net Income Attributable to Ford Motor Company
(l) Ford Auto FD Market Cap to LTM June 30, 2025 FCF

Note: round final dollar figures to the nearest million, round shares to the nearest 0.1 million, and round ratios to two decimal places. Currency: USD (all monetary figures).

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
