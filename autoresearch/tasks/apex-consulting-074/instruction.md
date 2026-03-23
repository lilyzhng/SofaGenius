You are a professional analyst specializing in Consulting.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

Our Healthcare system client’s internal analytics team is reporting strong performance from its CDI pilot, indicating benchmark achievement across all KPIs with a recommendation to proceed with enterprise rollout. The executive board wants us to perform an independent validation and help with a strategy for their next steps. 

I sent you the pilot results. Please give that a review and let me know the average percentage reduction in clinician documentation time per encounter following the implementation of the AI-assisted CDI tool (unweighted per-encounter average). Now, give me the percentage increase in documentation throughput per encounter after AI implementation, based on average documentation time reduction across all encounters(unweighted.)  Next, how much did the accuracy of coded documentation improve after the AI implementation (unweighted per-encounter average). Then calculate the percentage reduction in claim denial rate between manual and AI-assisted workflows, using the aggregate averages for each.

Now to wrap things up, their internal team said they were 4 for 4 on document time reduction (25.00% or higher), throughput gain (35.00% or higher), Coding accuracy improvement (3.00% or higher) and denial rate reduction (30.00% or higher). Give me one recommendation to take to the board meeting next week regarding readiness for the desired enterprise rollout, and don't forget your underlying reasoning. 

We need all calculated values with two decimal places. 


## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
