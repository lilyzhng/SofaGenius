You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

A Real Estate Private Equity company (LP) is teaming up with a real estate developer to acquire a property for $25 million with a mix of debt and equity at the end of 2024. 

Acquisition Assumptions:
The project will be financed with a mix of senior and mezzanine debt.
Senior Debt:
Senior Loan-to-Value (LTV) Ratio: 50.0% 
Senior Loan Interest Rate: 5.00% 
Senior Loan Amortization Period: 25 years
Senior Loan Maturity: End of year 5 (FY29)

Mezzanine Debt:
Mezzanine Loan-to-Value (LTV) Ratio: 10.0% 
Mezzanine Cash Interest Rate: 7.00% 
Mezzanine Paid-in-Kind (PIK) Interest Rate: 3.00% 
Mezzanine Amortization Period: None. It is an interest-only loan with no principal repayment until maturity
Mezzanine Maturity: End of year 5 (FY29)

The developer (Operating Partner) will cover 10% of the remaining acquisition costs, and the LP will cover the other 90%.

The property currently has three tenants. The developer plans to hold the property for five years (FY25–FY29) and sell it at the end of the fifth year based on the forward twelve-month NOI. Additional assumptions for acquisition, exit, and operating drivers are provided in the attached file.

Tenant #1 has a Full Service (FS) lease, Tenant #2 has a Single Net (N) lease, and Tenant #3 has a Triple Net (NNN) lease. None of the tenants are expected to renew their leases after expiration. New leases signed following the termination of the current tenants will maintain the same lease type and rental area and follow the rental growth rates outlined in the file.

Other Assumptions:
• Tenant Improvements (TIs) and Leasing Commissions (LCs) are charged in the year the new lease is signed (LCs on total lease value, i.e., Y1 rent * term).
• In each period, replacement reserves can be applied toward capital costs, but the amount drawn cannot exceed the lower of (i) the capital costs incurred in that period or (ii) the reserves available at the beginning of the period plus replacement reserve growth during that period.
• Assume the replacement reserve allocated to the use of funds is based on the historical FY24 operating assumption.
• For Single Net (N) leases, tenants are responsible for their proportional share of property taxes.
• For Triple Net (NNN) leases, tenants are responsible for their proportional share of operating expenses (Common Area Maintenance, Common Area Utilities, and Insurance) as well as property taxes.
• The rentable area not leased by the three tenants (vacant rental area) will follow the same baseline rent as Tenant #1.
• TIs and LCs are included in the Capital Costs.
• Any shortfall to cover the debt will be pro-rata funded by the equity investors. 

Project the company's cash flows based on the assumptions laid out in the files and output the following:
1.	The forward twelve-month (FY30) Net Operating Income (NOI)
2.	Gross proceeds from the sale of the property in FY29, excluding selling costs
3.	Total selling costs associated with the sale of the property
4.	Principal balance of the senior debt repaid at maturity (FY29)
5.	Principal balance of the mezzanine debt repaid at maturity (FY29)


Rounding: keep full precision in calculations; present dollar amounts to the nearest whole number. Round percentages and multiples to two decimal points.

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
