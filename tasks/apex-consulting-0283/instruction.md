# Task: Consulting Analysis

Our client, a food delivery app focused on Mexican food, is requesting assistance using the enclosed dataset on all of their merchants to determine which Size category of merchant they should focus their efforts on to try and increase their share of merchant revenue and, as a consequence, their overall app revenue. Could you determine the potential revenue increase (in $M to one decimal) associated with targeting each category of merchant by Size and then recommend which Size category the client should focus on for their efforts, assuming this is based purely on the revenue potential? Could you also include at least one reason why that may not be the best choice, based only on the provided data set and associated analysis?

For the purpose of this analysis, the client has categorized each of their merchants by merchant Size (which reflects the scale of each merchants' Estimated Total Delivery Revenue, both within and outside of the app) as well as by merchant Loyalty to the client's app (which reflects the app's Estimated Share of Revenue from each merchant's Total Delivery Revenue). The client considers Size and Loyalty to be their two essential merchant categories, and views any combination of the merchant Size category and Loyalty category to be a segment.

To calculate the potential revenue increase associated with targeting each category by merchant Size, please follow the client's assumptions: Merchants with an estimated total delivery revenue above $75M are all considered outliers and should be excluded fully from the analysis. The app cannot increase the share of merchant revenue for merchants in the high Loyalty-Big Size segment. Other high Loyalty merchants can realize an increase in their share of merchant revenue up to the highest current average share of merchant revenue (per segment) of any segment. For low and average Loyalty merchants: merchants in the small, medium and big Size categories can realize an increase in their share of merchant revenue of 20, 10 and 1 percentage points above the current average share of merchant revenue of the segment they belong to, respectively. The average share of merchant revenue to be used in these calculations is always weighted by total estimated delivery revenue and rounded to the nearest percentage point. 

## Instructions

- Your workspace has data files in `/app/data/`
- Use bash commands to explore, analyze, and solve the task
- Write your final answer to `/app/output/answer.txt`
- You can create Python scripts to help with analysis
- When done, respond with: done
