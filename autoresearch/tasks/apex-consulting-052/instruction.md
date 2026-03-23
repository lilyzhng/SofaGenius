You are a professional analyst specializing in Consulting.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

The COO of my client, an apparel e-commerce website, has raised questions about the high turnaround time reported by multiple customers and is requesting a review of the enclosed last nine months of data to help understand the magnitude of the problem. Could you calculate the percentage of orders that were delivered in the same month as order placement? Then, could you determine the average days taken to complete each of the following order milestones: from ordered to processed, processed to shipped and shipped to delivered? Could you then determine which of these milestones have room to improve compared to industry benchmarks, which are 2.0 days from ordered to processed, 2.5 days from processed to shipped and 4 days from shipped to delivered? For any stages that have room to improve, could you provide the percentage of orders that have a turnaround time that exceeds the market benchmark? For these same lower-performing stages, could you recommend to the client how they could bring their performance in line with industry standards? Round all percentages to the nearest whole percentage and round all days output to one decimal place.

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
