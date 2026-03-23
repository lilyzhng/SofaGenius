You are a professional analyst specializing in Consulting.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

The CHRO of a multinational investment bank wants to determine which employee grade levels (M1, M2, M3, M4, M5) give them the best returns based on the enclosed dataset. Can you calculate the weighted average of the ratio of average lifetime revenue to average lifetime pay for every grade, assuming Total Pay in the dataset represents the constant annual pay per employee and each employee’s lifetime should be defined as the duration since their date of joining to 10/25/2025? Can you identify the top two grades with the best ratios? What will be the additional cost in terms of total annual pay if we increase the number of employees for these two grades by 20%, assuming these employees will receive the average annual pay for their grades? Given the results of the analysis, which employee grade levels would you recommend the bank focus on for its expansion plans? Please include all underlying calculations, do not round interim calculations, round all ratio outputs to two decimal places and round dollar and employee outputs to the nearest whole number.

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
