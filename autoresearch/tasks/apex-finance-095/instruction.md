You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

Prepare a five-year forecast of the company's balance sheet that will be used to perform a Free Cash Flow to Firm (FCFF) valuation. The forecast should be based on the existing five years of historical financial statements, including the income statement and selected cash flow items. Using standard forecasting techniques and the assumptions below, project the next five years of balance sheet items.

Use the following forecasting assumptions: 
1) Net Debt Issued (Repaid): forecast as the fixed average of the past 5 years’ values.
2) Take Net Capex = Capital Expenditures - Sale of Property, Plant & Equipment 
3) Annual Net Capex is forecasted in line with revenue by taking the average proportion over past 5 actual years. Forecast Gross PPE for each year using the Net Capex.
4) Depreciation is forecasted in line with the year end Gross PPE by taking the average proportion of the past 5 years’ values.
5) No amortization is present.
6) Total Receivables grows in line with Revenue in average proportion of total receivables to revenue in the past 5 actual years.
7) Inventory grows in line with Cost of Revenue in average proportion of Inventory to cost of revenue in the past 5 actual years.
8) Prepaid Expenses grows in line with SG&A in average proportion of prepaid expenses in the past 5 years.
9) Restricted cash and other current assets remain flat at the most recent year value.
10) Long-Term Investments, Goodwill, Other Intangible Assets, Long-Term Deferred Charges, Other Long-Term Assets remain at the most recent actual year value.
11) Accounts Payable grows with cost of revenue in the average proportion of accounts payable to cost of revenue in the past 5 actual years.
12) Accrued Expenses grows in line with SG&A in the average proportion of accrued expenses to SG&A for the past 5 actual years.
13) Short term debt is 5% of the Total Debt.
14) Current Income tax payable and Other Current liabilities are flat at the most recent year value.
15) Current Unearned Revenue grows in line with Revenue in the average proportion of Unearned Revenue to Revenue for the past 5 years.
16) Long term debt is 95% of the Total Debt.
17) Long term Deferred Tax liabilities remains at the most recent actual year value.
18) Other Long-term Liabilities and Other Long-Term Liabilities (Adj.) take the fixed average value of the past 5 years.
19) Common Stock, Additional Paid-In Capital, Treasury Stock, Comprehensive Income & Other and Minority Interest remain at the most recent actual year value.
20) Cash is the balancing figure in the balance sheet.
21) All values in Million USD.

Assume a terminal growth of 1.5% and a WACC of 6.365%.

Find the following: 
1) Cash and Equivalents in 2025
2) Cash and Equivalents in 2029
3) FCFF for 2025
4) FCFF for 2029
5) Terminal Value of FCFF
6) PV of terminal value of FCFF
7) Enterprise Value
8) Equity Value
9) Implied Share Price
10) State if the firm is undervalued or overvalued in comparison to the most recent market price. 

Assumptions:
1)	No preferred stock is present.
2)	No Amortization is present.
3)    Use a tax rate derived from the 2024 effective tax rate (Tax Expense / Pretax Income from historical data), for all forecast years.
4)    Calculate Equity Value by subtracting Net Debt as of the end of the last historical year (2024) and Minority Interest as of the end of the last historical year (2024) from the calculated Enterprise Value.
5)    Perform the Discounted Cash Flow valuation using an End-of-Year discounting convention for all cash flows, including the terminal value.

Round the final outputs to the nearest 2 decimal places. Perform all intermediate calculations to full precision. Show your work and rationale for each answer.



## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
