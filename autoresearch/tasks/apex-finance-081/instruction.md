You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

A well-known U.S. PE firm is evaluating a leveraged buyout (LBO) of Summit Outdoor Gear, Inc. Build a 5-year LBO model and answer six questions. Assumptions are provided in the attached CSV (LBO_Assumption.csv); do not restate any assumption that is present in the CSV—reference it directly. 

Cash flow priority and debt logic:
1. Pay interest and taxes first (taxes on EBT, i.e., after interest)
2. Mandatory amortization = 10% of beginning debt each year
3. Optional repayments = 50% of residual free cash flow after interest, taxes, and mandatory amortization
4. Dividends = 50% of the residual cash after optional repayments
5. Add-on acquisition ($10M in Year 3) is funded from operating cash (not new equity)
6. Interest expense each year is computed on average debt; rates: Years 1–3 = 8%, Years 4–5 = 9%
7. Refinancing: at the end of Year 3 the company refinances; a one-time refinancing fee equal to 2% of ending Year 3 debt must be deducted from Year 4 free cash flow and is explicitly not tax-deductible (i.e., it does not reduce taxable income).
8. Dividend threshold (minimum cash policy): dividends can only be paid if post-debt-service residual free cash flow exceeds $2.0M; when this condition is met, dividends equal 50% of (residual − $2.0M); otherwise, dividends are zero.

Required outputs (show work, formulas, and intermediate steps):
1. Total equity investment at acquisition
2. Year 5 EBITDA
3. Ending debt at Year 5
4. Enterprise Value (EV) at exit
5. Equity value at exit
6. Equity MOIC and IRR over 5 years (use equity cash flows; include any interim dividends)

Rounding & tolerance:
- Units: millions of USD ($M)
- Monetary answers: round to two decimals; state tolerance as ±1% of the stated value
- Percentages (IRR): round to one decimal place; state tolerance as ±0.2 percentage points
- MOIC: round to two decimals; tolerance ±0.02×
- Use dynamic interest on average debt and taxes on EBT

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
