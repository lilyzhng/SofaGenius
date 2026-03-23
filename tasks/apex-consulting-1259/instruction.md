# Task: Consulting Analysis

Our client is a health insurance payer in the US looking to reprice their insurance policy for this subset of existing customers with dependents to account for the impact of having dependents on a customer’s health: (1) Customers aged under 25, with a BMI of over 25, (2) Customers aged between 25 to 50 (including both ends), with a BMI of over 25, (3) Customers aged over 50, with a BMI of over 25, and (4) Customers aged over 50, with a BMI of under (or equal to) 25. Could you provide the new proposed monthly premium for each of these segments with dependents, along with at least 1 potential risk associated with this price increase methodology (not the overall implications of increasing prices)?

The client has shared the attached data on the charges incurred by their existing customers (i.e., the amount paid out in medical costs by our client) over the last year. Note that these charges are associated with the customer themselves, not their dependents. To reprice each segment, please use the difference between the average per customer charges incurred by each segment mentioned above vs. the corresponding segment without dependents, divided by 12 to get the monthly difference. Then, round up the monthly difference to the next highest multiple of 10. This yields the amount by which our client will raise their monthly premiums for the corresponding customer segment. If the difference is negative, the monthly premium will remain unchanged. The current monthly premium for each of the above segments are: (1) $450, (2) $600, (3) $1000, and (4) $800, respectively. Please include all interim calculations, round all reported numbers to the nearest whole number but do not round interim calculations.

## Instructions

- Your workspace has data files in `/app/data/`
- Use bash commands to explore, analyze, and solve the task
- Write your final answer to `/app/output/answer.txt`
- You can create Python scripts to help with analysis
- When done, respond with: done
