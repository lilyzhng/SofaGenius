You are a professional analyst specializing in Consulting.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

My client, a small airline company, is looking to expand its geographic reach. Based on the enclosed data, could you recommend the top 2 most attractive geo regions for them to enter, providing your selections in ranked order within a table that includes the total passenger volume and average big mac price for each selected geo region? Please also state the biggest downside risk of choosing a region based on these two factors.

Please select the top 2 regions by ranking all regions according to total enplaned passengers from 2015 as well as by average big mac prices (a simple average of dollar prices for relevant countries), where a higher value is better for both metrics and enplanment volume ranking is weighted 3x as much as big mac prices when combining these two metric rankings to determine which region is most attractive. Please exclude regions that are not represented in the passenger data as well as data from the airlines Frontier and Sun Country. Please also assume that the pound is worth more than the dollar at the time of this analysis and use the supplied geo region definitions. Include all underlying calculations, round passenger volume to the nearest integer and the big mac average price to the nearest cent.

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
