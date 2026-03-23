You are a professional analyst specializing in Finance.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

Italian bank UniCredit S.p.A. (Ticker: UCGIM) is evaluating a cash tender offer for one of its outstanding EUR senior unsecured notes due 2029. The objective is to optimize funding costs and smooth the maturity profile without paying unnecessary premium versus hold-to-maturity economics. The Head of Funding requests a curve-consistent valuation of tender vs hold on the settlement date.

The attached file includes: full bond terms (coupon, frequency, last & next coupon dates, maturity), today’s clean price, the proposed tender price, the ESTR par swap curve at 3y/4y/5y/6y tenors, and the settlement date at T+30 calendar days (today is 13-Oct-2025).
- The proposed tender price in the file is DIRTY (includes accrued interest up to the settlement date).
- For bond cash flows, accrued interest, and YTM/PRICE, use the bond’s coupon frequency and day-count convention from the attached terms; if not specified, use Actual/Actual (ICMA). In Excel, set frequency per terms and set basis to match the bond day-count.
- For curve construction, use the provided rules (annual compounding; ACT/365 for time fractions).

I need to know:
> The yield to maturity at Tender Price (T+30)
> Curve-consistent yield to maturity (T+30) (YTM_Hold). Reprice the bond on T+30 using the attached €STR par curve with the following curve construction rules:
Flat-front zero assumption to the first pillar (3y); linear interpolation in zero-rate space between 3y/4y/5y/6y; build discount factors with annual compounding; time fractions in ACT/365
> Delta_Yield (YTM_Tender - YTM_Hold), expressed in basis points
> Decision if to proceed with the tender (internal rule is Delta YTM > 5bps)
> If decision not to tender, break-even tender prices that would exactly meet the hurdle

Rounding & Unit Rules
> YTM: percent, 3 decimals
> Delta yield in basis points, 1 decimal

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
