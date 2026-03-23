You are a professional analyst specializing in Consulting.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

We want to optimize workforce deployment, compensation, and retention. Leadership wants a fact-based analysis to answer which employee segments drive the most business value, where pay and performance are misaligned, and which interventions will reduce attrition cost-effectively. Based on the dataset, answer for the following questions:

Can you answer which city contributes the highest total business value, and what share (%) of total business value do they represent? Also, which education level of employees shows the highest average quarterly rating and report the rating to two decimal places. What is the average salary difference between employees who left (Attrition = Yes) vs. those who stayed? Report the difference to the nearest whole number. If we rank existing employees by (Total Business Value / Salary), which employee had the lowest ratio (in 2 d.p)? Help me with one way to decrease attrition from the employer perspective please. 

Note: All percentages should be rounded to the nearest whole number

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
