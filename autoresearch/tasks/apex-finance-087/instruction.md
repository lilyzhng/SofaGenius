You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

Albion Technologies plc (a UK company, GBP as the functional currency) will acquire Horizone Sistemas S.A. (a Brazilian company, with BRL as the functional currency) for a USD denominated headline price. Closing is expected in 4.5 months (135 days). The SPA uses a locked-box mechanism; working capital is pegged and trued up in BRL at close. Two post-close structures are evaluated:

Option A – Direct UK Parent (Brazil company to pay UK dividends, 15% WHT)
Option B – NL HoldCo (Brazil to pay NL HoldCo dividends, 10% WHT) plus a USD 500m intercompany loan at SOFR + 2.5% (currently 7.6%), interest only in Year 1 (paid quarterly), with Brazil WHT on outbound intercompany interest at 10%.

Brazilian frictions include IOF (0.38%) on dividend remittances only (ignore IOF on intercompany interest), 30% interest-deductibility limit (based on the provided tax‑EBITDA), and quarterly remittance caps.
Financing is a USD Term Loan B with 2.0% OID, a 0.75% p.a. ticking fee on the committed amount through close, and cross-currency swap targeting SONIA + 2.85% all-in GBP.

All required data is presented in the attached file “Horizone_Target.csv”

Requirement:
1.	Compute the 4.5-month USD/GBP forward rate based on interest rates (ACT/365; t = 135/365)
2.	Calculate the total USD consideration payable at close, including locked‑box interest accrual on the headline equity value, the working capital true‑up (convert the BRL peg variance at the 5‑month USD/BRL forward rate), and any escrow specified in the data file.
3.	Calculate the total GBP consideration payable at close based on 4.5 month USD/GBP forward
4.	Determine the net GBP inflow at close from the permitted BRL 250m distribution, after applying WHT and IOF applicable for Option A
5.	Determine the net GBP inflow at close from the permitted BRL 250m distribution, after applying WHT and IOF applicable for Option B
6.	Size the USD Term Loan B so that net proceeds after 2.0% OID, together with available buyer cash (after minimum GBP buffer) and net GBP inflow at close from option A, fully fund the GBP outlay including the accrued ticking fee for 135 days. Assume 4.5 month forward EUR/GBP as 0.86.
7.	Size the USD Term Loan B so that net proceeds after 2.0% OID, together with available buyer cash (after minimum GBP buffer) and net GBP inflow at close from option B, fully fund the GBP outlay including the accrued ticking fee for 135 days. Assume 4.5 month forward EUR/ GBP as 0.86.
8.	For year 1, compute the maximum net GBP remitted to the UK under Option A vs Option B, respecting the quarterly BRL 300m cap, WHT/IOF, the 30% Brazil interest deductibility limit (using the provided tax‑EBITDA), and NL 25% tax on interest income. Use the provided 6‑month USD/BRL NDF for converting Year‑1 BRL cash flows, and use the USD/GBP spot from the data file for any USD to GBP Year‑1 conversions. Assume any non‑deductible Brazil interest increases tax and reduces distributable cash. If Option A net remittance is greater than Option B’s, show the answer as a negative value.

Formatting and precision:
All monetary values and ratios should be shown to 2 decimal places. Forex rates to 6 decimal places. 

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
