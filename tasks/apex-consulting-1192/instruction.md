# Task: Consulting Analysis

The client is a big food delivery app that is analyzing merchant loyalty and performance in the Mexican food industry. As part of their merchant strategy, they want to classify the merchants in their database based on their size (small, medium, big) and based on their loyalty (low, average, high). The attached file provides each merchant's revenue through our app and an estimate of our share of wallet within their total delivery revenue. 

To determine which category of size each merchant belongs to, we must use their estimated total delivery revenue. Merchants up to and including the 33rd percentile of total delivery revenue are considered small, and up to and including the 67th percentile are considered medium. The rest is big. State the cutoff revenues used rounded to the nearest cent and how many merchants are in each group. 

For  the loyalty categorization, merchants whose share of wallets are less than or equal to the 33rd percentile (unweighted, every merchant has the same weight) are considered low, and merchants whose share of wallets are less than or equal the 67th percentile are considered average. The rest is high. State the cutoff shares of wallet used with no decimal places and how many merchants are in each group.

The client considers balance an important element of the classification. It will consider a group balanced if it contains between 10% and 13% of the merchants (inclusive). Define a group as a pairing of a loyalty bucket with a size bucket. How many groups, if any, are unbalanced? If there is at least one, propose one change in the cutoffs used to make the groups balanced, keeping in mind that the cutoffs must apply to all merchants (i.e. the cutoff from low to average loyalty has to be the same for small, medium and big businesses). If every group is balanced, state that no cutoff changes are necessary.

## Instructions

- Your workspace has data files in `/app/data/`
- Use bash commands to explore, analyze, and solve the task
- Write your final answer to `/app/output/answer.txt`
- You can create Python scripts to help with analysis
- When done, respond with: done
