You are a professional analyst specializing in Consulting.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

I'm making a plan for our client’s next campaign cycle using the attached data, where Payment ($) is equivalent to the unit price associated with the payment method of the specific campaign. Could you calculate how much my client would save in $ if we discard 30% of their worst performing campaigns in terms of impressions per $? Could you also calculate the average impressions per $ for each payment method, assuming we don’t discard any of the current campaigns and that the average is taken using total impressions for each payment method? Based on this calculation, which payment method group performs the best? Finally, could you list the most significant benefit of moving our campaign plan away from variable cost over to fixed? Please report all numeric answers rounded to two decimal places.

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
