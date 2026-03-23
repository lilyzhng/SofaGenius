You are a professional analyst specializing in Medicine.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

Note: For the following clinical scenario, please refer to the most up to date American Academy of Pediatrics Immunizations schedule as of September 17, 2025.

A 13-month-old male presents to the clinic with his new foster mom. He was seen in the clinic last week for a well-child-check, but was unable to get vaccines because his foster mom had not received his shot records from the case worker prior to that appointment. She has his records now, but he is behind on immunizations.

Child’s date of birth - September 1, 2024
Today’s date - October 2, 2025

Immunization record
Hep B #1 - 9/1/24
Hep B #2 - 3/20/25
DTaP #1 - 3/20/25
PEDVAXHIB #1 - 3/20/25
Prevnar #1 - 3/20/25
IPV #1 - 3/20/25
Influenza #1 - 3/20/25
Hep B #3 - 4/24/25
DTaP #2 - 4/24/25
PEDVAXHIB #2 - 4/24/25
Prevnar #2 - 4/24/25
IPV #2 - 4/24/25
Influenza #2 - 4/24/25
DTaP #3 - 9/1/25
PEDVAXHIB #3 - 9/1/25
Prevnar #3 - 9/1/25
IPV #3 - 9/1/25
MMR #1 - 9/1/25
Varicella #1 - 9/1/25
HepA #1 - 9/1/25

Using the attachment "AAP-Immunization-Schedule.pdf", and assuming this child is healthy and has no contraindications to vaccines, what vaccinations should he receive today? 

What other vaccines should he receive by the end of this year? 

Briefly explain your clinical reasoning.


## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
