You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

The securitization capital markets team at SPO Capital has been actively working with rating agencies on an upcoming securitization issuance of a pool of performing residential transition loans ("RTL" or commonly known as "fix to flip" loans). RTL loans are short term loans issued to borrowers looking to acquire and rehab a residential property with the intent to then sell the property for a profit. The loan is structured as a bullet loan with no principal or interest payments until maturity. Interest pays in kind ("PIKs") monthly. Rating agencies have expressed certain reservations regarding this PIK structure and have requested the following diligence: 

1. Calculate the aggregate Loan Balance at Maturity ("LBM") for the pool. Use the Total Loan, Closing Date, Maturity Date, and Interest Rate fields.
2. Calculate the weighted average (by Total Loan) LBM-to-Purchase Price ("PP") (i.e. a loan-to-value calculation using the LBM) for the pool. Use the Total Loan, Purchase Price, Closing Date, Maturity Date, and Interest Rate fields.
3. Calculate the weighted average (by Total Loan) LBM-to-After Repair Value ("ARV") for the pool. Use the Total Loan, ARV, Closing Date, Maturity Date, and Interest Rate fields.
4. Calculate the concentration (as a percentage of aggregate Total Loan) of loans with LBM-to-PP greater than 100%. Use the Total Loan, Purchase Price, Closing Date, Maturity Date, and Interest Rate fields.
5. Calculate the concentration (as a percentage of aggregate Total Loan) of loans with LBM-to-ARV greater than 100%. Use the Total Loan, ARV, Closing Date, Maturity Date, and Interest Rate fields.

Rating agency has also requested a "stress" scenario wherein each loan is assumed to be extended for an additional 6 months after maturity to account for unforeseen delays in rehab projects. 

6. Calculate the aggregate Stressed Loan Balance at Maturity ("SLBM") for the pool. Use the Total Loan, Closing Date, Maturity Date, and Interest Rate fields.
7. Calculate the weighted average (by Total Loan) SLBM-to-Purchase Price ("PP") (i.e. a loan-to-value calculation using the SLBM) for the pool. Use the Total Loan, Purchase Price, Closing Date, Maturity Date, and Interest Rate fields.
8. Calculate the weighted average (by Total Loan) SLBM-to-After Repair Value ("ARV") for the pool. Use the Total Loan, ARV, Closing Date, Maturity Date, and Interest Rate fields.
9. Calculate the concentration (as a percentage of aggregate Total Loan) of loans with SLBM-to-PP greater than 100%. Use the Total Loan, Purchase Price, Closing Date, Maturity Date, and Interest Rate fields.
10. Calculate the concentration (as a percentage of aggregate Total Loan) of loans with SLBM-to-ARV greater than 100%. Use the Total Loan, ARV, Closing Date, Maturity Date, and Interest Rate fields.

Show all answers to two decimal places.  

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
