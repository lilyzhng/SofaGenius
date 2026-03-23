You are a professional analyst specializing in Consulting.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

I'm working to optimize the distribution of marketing spend for my client for the next cycle to better fit their Family Man target group. They want to focus on campaigns that they have experience with, meaning only Partner + Category combos that they’ve done more than 2 campaigns with, previously. Among those, disregard campaigns where Family Man is not in top 2 in the attached dataset. The ones left are our campaigns of interest for this analysis. First off, what is the total campaign cost and total impressions of the campaigns of interest? 

Next, assume for SoMe and Online campaigns, that if only target group 1 is marked, then that group gets 90% of impressions. If 1 & 2 are marked, then group 1 gets 70% and group 2 gets 30%. If all three are marked, then group 1 gets 60%, group 2 gets 25%, and group 3 gets 15%. Assume for TV campaigns, that if only target group 1 is marked, then that group gets 75% of impressions. If 1 & 2 are marked, then group 1 gets 65% and group 2 gets 25%. If all three are marked, then group 1 gets 60%, group 2 gets 20%, and group 3 gets 10%. How many Family Man impressions does that yield in campaigns of interest and does Family Man get more impressions than Single Man in the campaigns of interest? What is ultimately the number of Family Man impressions per $ in campaigns of interest? 

Please list at least one downside that I can share with my client about using campaign channels with less control on ultimate recipient (multiple groups are exposed to the campaign). Please include all underlying calculations, report two decimal points for Family Man Impressions per $ and for the rest, report with zero decimals. Please note that Payment ($) is equivalent to the unit price associated with the payment method of the specific campaign.

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
