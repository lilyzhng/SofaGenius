You are a professional analyst specializing in Consulting.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

One View Bank is a European card issuer with 3 flagship cards: "One View Standard", "One View Premium", and "One View Advantage". One View Standard has an annual fee of $0 per user in the first year and $39 per user every year after that; there is an average 25% APR with a 1.5% interchange fee. One View Premium has a standard annual fee of $350 per user; there is an average 20% APR with a 2.5% interchange fee. One View Advantage (their travel card) has an annual fee of $0 per user the first year and $150 per user every year after that; there is an average 25% APR with a 2.0% interchange fee. APR and interchange fees are levied as a percentage of spend.

Can you find out how much more the average One View Premium cardholder spends annually than the average One View Standard cardholder based on the attached data? In addition, how much more in average monthly spend does a One View Standard cardholder have that is subject to interest charges than a One View Premium cardholder and a One View Advantage cardholder? Next, what is the most likely reason the One View Advantage card is generating higher "Other Fees" than the other card offerings? Lastly, the bank is looking to convert One View Standard cardholders to one of the other two card offerings after their first year to generate more revenue per customer. Which card should One View be converting its One View Standard cardholders to? Assume that when a customer changes its card, they change their behavior to match the pool of their new card. Therefore, base this recommendation on average year 2 total revenue for each card type relative to One View Standard.

The attached dataset provided represents the total fees generated from each account for September 2025; the data is indicative of an average month. Keep in mind that each account in the sample set of data was initiated on January 1st, 2025 and annual fees are charged on the day of account initiation. In the dataset, Column E “Other Fees” typically refers to fees such as foreign transaction fees and miscellaneous transaction fees. Please round all final calculations to 2 decimal places. Show your calculations

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
