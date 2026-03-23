You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

Objective: Assess whether a sponsor should pursue a Nasdaq Global Market IPO or a same-day underwritten Term Loan B (TLB).
Sources: Nasdaq Initial Listing Guide (March 2025) (Nasdaq); U.S. Leveraged Loan Primer (PitchBook LCD). These materials are publicly available and searchable online.
Jurisdiction and basis: U.S., USD, U.S. GAAP.
Rely only on the definitions and numbers provided in the two documents above. Treat the IPO as common stock only (no units, ADS, or warrants). Treat the TLB as a single, underwritten institutional term loan.
Starting input: Bridge Size (par): $516,912,553.13. Use this fixed par amount wherever “bridge size” is referenced.
Show percentages and basis-point (bp) figures to 1 bp (for example, 3.47%). For dollar amounts, round as follows: amounts at or above $10mm to the nearest $100k; amounts from $1mm to $10mm to the nearest $10k; and amounts below $1mm to the nearest $1k. Round only for final display. 

When discounting future cash flows, derive the discount rate from LCD’s “spread-to-expected-life (STC)” convention using (i) the example margin specified in the LCD primer, (ii) OID mechanics per LCD applied to an issue price consistent with a 1-point discount, and (iii) an expected life equal to the midpoint of LCD’s stated “three- or four-year” assumption. Use simple annual compounding.

Using only the LCD primer, determine the STC discount rate for this case by (i) taking the example institutional loan margin in the primer, (ii) applying OID per LCD to an issue price consistent with a 1-point discount, and (iii) using the midpoint expected life from LCD’s stated range. Report the resulting annual STC (bp over the base) and the corresponding decimal discount rate you will use for PV in subsequent tasks. Do not add any base rate.

Analyze an underwritten TLB sized to the Bridge Size (given), with the LCD arranger fee at the midpoint of the stated range and with OID using the same LCD mechanics described above. Calculate and report (i) issuer day-one net cash, (ii) the day-one “all-in discount” in % of par and in dollars (arranger fee + OID), and (iii) the PV (using your STC rate) of the soft-call payment for a full refinancing at 18 months, using LCD’s standard two-year soft-call schedule.

From the Nasdaq guide, determine for the Global Market (i) the flat entry fee for a common stock listing and (ii) the annual fee range midpoint (ignore ADS/units footnotes and assume no proration for this case). Then calculate the IPO gross spread (%) that equalizes the issuer’s economics with the TLB in two ways: (A) day-one (no PV adjustments; assume annual fee paid day-one) and (B) PV-adjusted, subtracting the PV of the TLB soft-call from the prior task but not discounting Nasdaq cash fees (treat those as day-one). Report both gross-spread thresholds to 1 bp, 

Using the LCD ABL borrowing-base guidance, determine the minimum eligible collateral needed to fully secure a facility equal to the Bridge Size (given) under the case: A/R-only at the LCD A/R advance rate.

Show your work

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
