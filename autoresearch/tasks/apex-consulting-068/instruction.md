You are a professional analyst specializing in Consulting.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

A European supermarket chain is considering expanding into Africa and wants your help choosing the target countries using 2022 data. Could you help me with the following please? 

First, determine cultural fit: Calculate and list the cultural fit scores for the countries we have household data on, determined by looking, for each country, at the similarity score of language, brands, diet, religion, climate and holidays, multiplying those scores by their weights, and summing them up. The weights are determined as follows: If less than 30% of African countries have that characteristic in common with Europe, assign a weight of 3. If 30% to 60% (inclusive) of African countries have that characteristic in common with Europe, assign a weight of 2. Otherwise, assign a weight of 1. 

To come up with the short list of countries to analyze, include the top scoring country/countries until their combined GDP represents at least a third of the GDP of the regions for to which the countries being analyzed belong to. Just let me know the country/countries that were removed from the original list. 

For the countries still standing, recommend the top 2 countries based on TAM (total grocery market size) for further market analysis.

Round every number to the nearest integer.

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
