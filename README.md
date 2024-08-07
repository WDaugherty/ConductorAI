# ConductorAI

## Purpose:
To find the largest number in this document regardless of the unit metrics as a base case. Additionally, there is a challenge to NLP for context and to find the largest number in the document with this in mind.


## Setup:
To create the virtual environment, run the following commands:
```bash
python -m venv venv
source venv/bin/activate
```

Afterwards install the required packages:
```bash
pip install -r requirements.txt
```

## Running the script:

First, you must input the correct file path in the main.py file on line 247 of main.py.


To run the script, run the following command:
```bash
python main.py
```
## Output:

You will find the base case and bonus cases results with locations in the PDF attached in the command line output. Additionally, I have included tabels for each method and the runtime of the script.


## Future Considerations:
In its current state, the script runs well, however this could be further improved in the following manner:

- Optimized for performance in a faster langauge. 
- Use of more optimal python pdf libraiies to extract the text from the pdf (PYDF is the most known to me).
- Verifications for the numbers extracted to ensure that they are really the largest numbers. 
- Enahnce PDF input to better allow the users to input the file path or choose a file from the directory.