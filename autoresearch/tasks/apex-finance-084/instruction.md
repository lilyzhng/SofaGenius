You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

On 08 October 2025, rating agency upgraded its rating on Dutch beer maker Heineken (Ticker: HEIANA) from BBB+ to A- by S&P. Heineken has one EUR 1.5bn 3.250% 17/09/2034 bond outstanding and the treasury team wants to know if the rating upgrade had any material impact on the bond's credit spread. Our trading desk spotted the bond at 89.467 on 01 October 2025 (t-7), and at 90.749 on 15 October 2025 (t+7). The file attached includes the EUR mid-swap rates on both dates.

I need to know:
- the bond's YTM and credit spread (i-spread) on 01 October 2025
- the bond's YTM and credit spread (i-spread) on 15 October 2025
- the movement in credit spreads between the two dates

Did the credit spread move materially? Consider any move of more than 20bps as material.

For YTM calculation, use the following inputs:
- Redemption Value: 100
- Coupon: Fixed, annual frequency.
- Day Count: Act/Act
- Linear interpolation if needed

State yields in percent, rounded to three decimal places, and spreads in basis points, rounded to one decimal place.

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
