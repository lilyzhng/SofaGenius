You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

Produce an EV to Equity Bridge that would be used in a Locked Box Paper for a regulated, asset and wealth management company based in the UK with £1bn of assets under management with the key assumptions in the pdf provided (labelled "Mercor - EV to Equity Bridge - Test Version"). Assume there are no adjustments from the reported source numbers. Assume the Locked Box Date is 31 March 2025 and the date of completion is 30 September 2025. Assume EV is £10 million. Ignore Leakage and Profit Ticker's in the analysis. Use the last 12 months from Mar-25 as an average for the target net working capital, with Mar-25 being the "actual" working capital. For clarity, corporation tax is the same as income tax payable. 

Include the following line items in the EV to Equity Bridge (report to the nearest £):
- Enterprise Value
- Excess Cash
- Debt/Debt-like Items
- WC Adjustments
- Equity Value at Locked Box Date

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
