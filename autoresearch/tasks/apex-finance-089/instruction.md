You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

As part of Lloyd's liquidity review in relation to a potential M&A transaction, you have been tasked with assessing the bank's balance sheet to evaluate post-transaction funding resilience and regulatory headroom under Basel III Net Stable Funding Ratio (NSFR) framework. 

You are provided with the following materials for your assessment:

- Lloyds Bank - 2025 HY Pillar 3 report
- LLoyds - Retail Deposit & Wholesale Funding Report (prepared by the Treasury team) - (Values in £ Millions)

The Treasury team has confirmed the following events occurring on 2 July 2025:

- Customer A1 (an individual retail depositor whose balances were previously within a personal account covered by the national deposit-insurance scheme) has transferred all their funds to an account used primarily to fund crypto-asset investments. The account remain retail, but the balance is held for investment rather than day‑to‑day transactional purposes i.e. rate or market-sensitive. 
- Stable Retail customers A3, A4, and A5 have had their accounts reclassified to Other Wholesale Funding due to changes in their activity profiles.

Assuming no other changes occur besides the reclassifications described above, complete the following tasks objectives:

1. Determine the total weighted Stable Retail Deposit as at 31 December 2025, rounded to the nearest whole number.
2. Determine the total weighted Less Stable Retail Deposit as at 31 December 2025, rounded to the nearest whole number.
3. Determine the total weighted Retail Deposit as at 31 December 2025, rounded to the nearest whole number.
4. Determine the total weighted Operational Deposits as at 31 December 2025, rounded to the nearest whole number.
5. Determine the total weighted Other Wholesale Funding as at 31 December 2025, rounded to the nearest whole number.
6. Determine the total weighted Wholesale Funding as at 31 December 2025, rounded to the nearest whole number.
7. Determine the total weighted ASF as at 31 December 2025, rounded to the nearest whole number.
8. Determine the Net Stable Funding Ratio (NSFR) as at 31 December 2025, rounded to the nearest percentage.
9. Assess whether the projected NSFR as at 31 December 2025 has changed materially (i.e., by more than +/- 5%) compared to 30 June 2025.
10. Determine if the bank will still be operating within Basel III's Net Stable Funding Ratio (NSFR) framework based on the projected NSFR as at 31 December 2025? 

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
