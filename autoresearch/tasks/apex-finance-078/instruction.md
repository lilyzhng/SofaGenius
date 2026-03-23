You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

To allocate funds to relatively low-risk investments while still achieving a decent return, refer to the ‘S&P500’ and ‘Nikkei225’ excel source files that contain the closing ETF prices from Yahoo Finance for these respective indexes for the five years leading up to April 15th, 2025.

Please identify the largest overall peak-to-trough drawdown (in % terms) within the five-year dataset for each index. For each largest drawdown movement from requested indices, please tell me how many calendar days the duration of each period with the largest drawdown movements are along with their start and end dates.

Please round all percentage values to two decimal places and round any day counts to the nearest whole number. For dates, use the format: MM/DD/YYYY.

Lastly, state which of the two indices should be avoided on account of it having the highest daily volatility during the largest drawdown period determined above.



## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
