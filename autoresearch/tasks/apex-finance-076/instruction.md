You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

Mariner Cloud plc (acquirer) plans to acquire Orion Metrics AG (Target). All figures and inputs are in the CSV “Orion_Target.csv”. 

Requirements:
Purchase price allocation and opening balance sheet impacts
a.	Compute the following opening impacts of identifiable intangibles (in USD):
a.	Annual book amortization - Technology IP 
b.	Annual book amortization - Customer relationships
c.	After tax impacts of Inventory step-up – amortize to COGS evenly over the specified months
d.	After tax NI reduction from deferred revenue fair value hair cut – recognize evenly over 12 months 

b.	Compute Opening fair value of net assets and goodwill (in USD)

c.	Year 1 Diluted EPS (all in USD)
a.	NOL benefit from 382 annual limitation
b.	338 step-up year 1 tax shield (60% of (Tech IP + Goodwill) over 15 years
c.	After tax interest effect of the convertible notes (for if converted)
d.	NCI share of target net income
e.	Build forecasted net income to common shares 
f.	US GAAP diluted EPS – ignore purchased call
g.	Economic diluted EPS – offset conversion shares with the purchased call up to the cap using provided average share price
h.	Accretion/ dilution % vs. Acquirer standalone diluted EPS (approx. basic shares provided)

Formatting:
- 2 decimal rounding throughout
- monetary values in USD millions with two decimal places 
- EPS values to cents


## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
