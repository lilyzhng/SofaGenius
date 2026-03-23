You are a professional analyst specializing in Consulting.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

The attached file contains the data of a sedan manufacturing firm. The sedan assembly line consists of five dedicated workstations (Tasks 1-5) operating in a continuous flow configuration to produce a car in a single assemble line. All tasks operate simultaneously on different cars in sequence (i.e., while one car is in Task 3, others are in Tasks 1, 2, 4, and 5). The slowest task determines the overall throughput of the line.

Please calculate the average time taken for each task (Task 1, 2, 3, 4, 5) across the data provided. Also calculate the average time taken between produced cars when production is in steady-state. What will be the annual production capacity of an assembly line, assuming 24 hours of work per day & 300 working days per year? 

The CEO of an automotive maker that currently produces hatchbacks wants to explore sedan production and has set a target revenue of INR 1400 Million by the end of 2026 (starting production January 2026). Given that one car is priced at INR 1 Million, how many assembly lines do we need to achieve this target? What is the headcount of employees currently placed for the reference assembly line & how many total employees are required? Finally, share one risk involved if the CEO goes ahead with this plan.

Please round off the time to one decimal place and other numbers to the nearest whole number. 

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
