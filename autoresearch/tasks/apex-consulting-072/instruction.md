You are a professional analyst specializing in Consulting.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

Titan Capital Partners is preparing to launch a late-stage PE fund targeting high-growth unicorns and has asked our firm to identify which regions and industries offer the best combination of scale, depth, and growth momentum for allocation. 

Based on the enclosed dataset, could you provide the total combined valuation of all unicorns worldwide, which country produced the most unicorns and the number of unicorns it produced, which country contributed the largest share (%) of the total combined global valuation of all unicorns and the country’s percentage share of valuation dollars, which industry has the highest average valuation per unicorn and the average valuation for the industry as well as what percentage of unicorns became unicorns since 2021 (inclusive of 2021) as a share of total unicorns? Can you also calculate the ratio of the average valuation of the most valuable 10% of unicorns by count (round up if needed) vs. the bottom 90%? If we decide to choose based only on these numbers that you just calculated, which country-industry combination should Titan Capital focus its next fund on? Taking into account the full dataset, but only the dataset, explain why that industry might not be the best choice for that chosen country. Please provide underlying calculations, do not round intermediate calculations, round all monetary figure outputs to the nearest $B and provide percentage and ratio figure outputs rounded to one decimal place.

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
