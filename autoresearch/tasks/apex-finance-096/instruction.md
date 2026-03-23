You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

An Equity Capital Markets (ECM) syndicate desk of a major investment bank is exploring a pro rata allocation or an allocation aimed at reducing flips on an upcoming equity offering. The desk is looking to assess allocation sizing by account, expected flipping behavior, aftermarket volume, and the impact of re-allocating between investor groups.
The total deal size is 500 million. Flips are assumed to hit the market immediately.  Management has provided a file containing the demand profile. The file contains Account, Account Group, Allocation dollars, estimated Flip% and estimated Holding Days.

Using the data and holdings provided, do the following:
Compute the % the deal is over- or undersubscribed.
If allocations are given pro rata, compute the allocation for each investor group in dollars. 
In the pro rata slicing, determine the total aftermarket selling volume implied by flips and the weighted overall holding period for the book.
To limit flips, management is also considering allocating full demand based on lowest estimated flips until deal size is met. Compute the allocation for each investor group in dollars as well as the total aftermarket selling volume implied by flips and the weighted overall holding period for the book.
For both allocation strategies, calculate the percentage of the original expected to be flipped and state which investor group is driving the most flips.

Report all results rounded to 2 decimals, and dollar amounts in full rounded to 2 decimals.

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
