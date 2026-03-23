You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

Investment Banking firm BLT is advising fund ART with a whole loan bid for a pool of reperforming ("RPL") and nonperforming ("NPL") non-agency mortgage loans. The loans are segmented across six different sub-pools. ART has shared with BLT the data tape for the pool and has requested assistance with the following diligence:

1. Calculate the Weighted Average (by Total Balance) Bankruptcy Date for bankruptcy flagged loans. Use Bankruptcy Flag and BK Filing Date fields. 
2. Calculate the concentration of bankruptcy flagged loans where the Borrower filed for bankruptcy within 5 years of the loan's origination date. Use Bankruptcy Flag field, BK Filing Date, and Origination or Note Date fields.
3. Calculate the Weighted Average Market Value (by Total Balance) for Pools 1 through 3 based on the loan's current cash flow and a 10% discount rate. Use Current Maturity Date, Current P&I, Due Date, and Total Balance fields. Market Value should be expressed as a percentage of Total Balance for task item #3.
4. Calculate the aggregate loan balance write-off at maturity for Pools 1 through 3 based on current contracted terms. Use Current Maturity Date, Current P&I, Due Date, Current Interest Rate %, and Total Balance fields. 
5. Calculate the implied borrowing base for Pools 1 through 3 based on an 80% advance rate to market value. Market value should be based on the loan's current cash flow and a 10% discount rate. Use Current Maturity Date, Current P&I, Due Date, and Total Balance fields. Market Value should be expressed as a nominal dollar amount for task item #5.

Format requirements:
- Express all dollar amounts in whole dollars, no decimal places
- Express percentages to 2 decimal places
- Express dates in MM/DD/YYYY format


## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
