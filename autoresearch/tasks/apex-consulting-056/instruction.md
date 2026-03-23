You are a professional analyst specializing in Consulting.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

A US-based private medical practice business would like to understand the financial performance of the 'Offices of Physicians' industry. The attached dataset contains a summary of aggregated tax return information across a sample of ‘Offices of Physicians' businesses across the US, with the number of firms included in the sample for each year found in row 3. Assume that ‘business receipts’ refers to revenue and ‘net income’ refers to earnings before tax.

First, the company wants to know what were the 3 fastest growing Income Statement items for the average firm in the sample between 2014 and 2022 as measured by CAGR, and what were each of their CAGRs, as a percentage to two decimal places

Next, the client is concerned about its Cost of Goods sold, and would like to explore developing an analytics platform that forecasts Cost of Goods Sold based on revenue. However, the client would only like to invest in building this platform if it believes that it can achieve strong forecast accuracy. Specifically, the client believes that if the correlation between the average firm's Cost of Goods Sold and the average firm's revenue is at least 0.90, then it can achieve strong forecast accuracy for its pool of offices. Calculate the correlation between the average firm's Cost of Goods Sold and the average firm's Revenue between 2014 and 2022, as a percentage to two decimal places. Should the client invest in developing this analytics platform?

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
