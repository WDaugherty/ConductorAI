"""
largest number in PDF finder

This script finds the largest number in a PDF document, considering both raw numbers
and numbers with contextual scaling (e.g., "in millions").

It handles table structures separately and provides both base and NLP-enhanced number extraction.
"""

import re
import PyPDF2
import time
from collections import defaultdict
from prettytable import PrettyTable

def extract_all_numbers(text: str) -> list:
    """
    Extracts all numbers from the given text, including those with commas.

    Args:
        text (str): The input text to extract numbers from.

    Returns:
        list: A list of floats representing all numbers found in the text.
    """
    # Use regex to find all number-like patterns in the text
    numbers = re.findall(r'(?:[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)', text)

    # Convert found numbers to floats, removing commas
    return [float(num.replace(',', '')) for num in numbers]

def extract_scale_factor(text: str) -> float:
    """
    Determines the scale factor based on keywords in the text.

    Args:
        text (str): The input text to search for scale indicators.

    Returns:
        float: The scale factor (e.g., 1e6 for millions).
    """

    # Define scale factors for different magnitudes
    scale_factors = {
        'thousand': 1e3,
        'million': 1e6,
        'billion': 1e9,
        'trillion': 1e12
    }

    # Check for scale indicators in the text
    for word, factor in scale_factors.items():
        if f"in {word}" in text.lower() or f"(${word[0]})" in text.lower():
            return factor
    return 1  # Default scale factor if no indicators are found

def detect_table_boundaries(text: str) -> list:
    """
    Detects potential table boundaries in the text.

    Args:
        text (str): The input text to search for table indicators.

    Returns:
        list: A list of indices where new tables potentially start.
    """
    # Find potential start points of tables based on fiscal year indicators
    return [m.start() for m in re.finditer(r'\n\s*(?:FY\s*\d{4}|Fiscal Year)\s*', text)]

def extract_numbers_with_context(text: str) -> list:
    """
    Extracts numbers from the text, applying contextual scaling.

    Args:
        text (str): The input text to process.

    Returns:
        list: A list of tuples (original_number, scaled_number, scale_word, position).
    """
    numbers = []
    table_boundaries = detect_table_boundaries(text)
    current_scale = 1
    last_boundary = 0

    # Find all number-like patterns with potential scale words
    matches = list(re.finditer(r'([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(\w+)?', text.lower()))
    
    for i, match in enumerate(matches):
        try:
            original_number = float(match.group(1).replace(',', ''))
        except ValueError:
            print(f"Debug: Unable to convert to float - {match.group(1)}")
            continue  # Skip if we can't convert to float
        scale_word = match.group(2)
        position = match.start()

        # Update scale if a new table boundary is encountered
        if table_boundaries and position > table_boundaries[0]:
            current_scale = extract_scale_factor(text[last_boundary:position])
            last_boundary = table_boundaries.pop(0)

        scaled_number = original_number * float(current_scale)
        
        # Apply additional scaling based on scale words
        if scale_word in ['thousand', 'million', 'billion', 'trillion']:
            scaled_number *= float(extract_scale_factor(scale_word))
        elif scale_word and scale_word.endswith('s') and scale_word[:-1] in ['thousand', 'million', 'billion', 'trillion']:
            scaled_number *= float(extract_scale_factor(scale_word[:-1]))
        
        numbers.append((float(original_number), float(scaled_number), scale_word or 'N/A', int(position)))
    
    return numbers

def process_pdf(file_path: str) -> tuple:
    """
    Processes a PDF file, extracting numbers using both base and NLP methods.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        tuple: Two elements - list of base numbers and dict of NLP results.
    """
    all_numbers = []
    nlp_results = defaultdict(list)
    
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            
            # Extract numbers using base method
            all_numbers.extend([(float(num), int(page_num)) for num in extract_all_numbers(text)])
            
            # Extract numbers using NLP method
            nlp_numbers = extract_numbers_with_context(text)
            if nlp_numbers:
                nlp_results[int(page_num)] = nlp_numbers
    
    return all_numbers, nlp_results

def display_results(base_numbers: list, nlp_results: dict):
    """
    Displays the results in a formatted table.

    Args:
        base_numbers (list): List of (number, page) tuples from base extraction.
        nlp_results (dict): Dictionary of NLP results.
    """
    print("\nBase Results (top 10 largest numbers):")
    base_table = PrettyTable()
    base_table.field_names = ["Number", "Page"]
    for num, page in sorted(base_numbers, key=lambda x: float(str(x[0])), reverse=True)[:10]:
        base_table.add_row([str(num), str(page)])
    print(base_table)
    
    print("\nNLP Results (top 10 largest numbers):")
    nlp_table = PrettyTable()
    nlp_table.field_names = ["Page", "Original", "Scaled", "Scale Word", "Position"]
    all_nlp_numbers = [(original, scaled, word, position, page) 
                       for page, numbers in nlp_results.items() 
                       for original, scaled, word, position in numbers]
    
    for page, original, scaled, word, position in sorted(all_nlp_numbers, key=lambda x: float(str(x[1])), reverse=True)[:10]:
        nlp_table.add_row([str(page), str(original), str(scaled), str(word), str(position)])
    
    print(nlp_table)

    

def find_largest_number(numbers: list) -> tuple:
    """
    Finds the largest number in the given list.

    Args:
        numbers (list): List of (number, page) tuples.

    Returns:
        tuple: The largest number and its page, or None if the list is empty.
    """
    return max(numbers, key=lambda x: x[0]) if numbers else None

def find_largest_nlp_number(nlp_results: dict) -> tuple:
    """
    Finds the largest number in the NLP results.

    Args:
        nlp_results (dict): Dictionary of NLP results.

    Returns:
        tuple: The largest number info (original, scaled, word, position, page), or None.
    """
    if not nlp_results:
        return None
    largest = max((max(page, key=lambda x: x[1]) for page in nlp_results.values() if page), key=lambda x: x[1], default=None)
    if largest:
        page = next(page for page, numbers in nlp_results.items() if largest in numbers)
        return (*largest, page)
    return None


# def verify_number(number: float, context: str, pdf_path: str) -> bool:
#     """
#     Verifies if a number exists in the PDF with its surrounding context.

#     Args:
#         number (float): The number to verify.
#         context (str): The expected surrounding context.
#         pdf_path (str): Path to the PDF file.

#     Returns:
#         bool: True if the number is verified, False otherwise.
#     """
#     with open(pdf_path, 'rb') as file:
#         reader = PyPDF2.PdfReader(file)
#         for page in reader.pages:
#             text = page.extract_text()
#             if str(number) in text and context in text:
#                 return True
#     return False

def main(pdf_path: str):
    """
    Main function to process the PDF and display results.

    Args:
        pdf_path (str): Path to the PDF file to process.
    """

    #Track the runtime of the program 
    start_time = time.time()

    base_numbers, nlp_results = process_pdf(pdf_path)

    largest_base = find_largest_number(base_numbers)
    largest_nlp = find_largest_nlp_number(nlp_results)

   
    
    if largest_base:
        print(f"The largest number found (base functionality): {largest_base[0]:,.2f} ")
        print(f"Found on page: {largest_base[1]}")
    else:
        print("No numbers found using base functionality.")

    if largest_nlp:
        print(f"The largest number found (with NLP): {largest_nlp[1]:,.2f}")
        print(f"Original value: {largest_nlp[0]:,.2f}")
        print(f"Found on page: {largest_nlp[4]}")
    else:
        print("No numbers found using NLP functionality.")

    display_results(base_numbers, nlp_results)

    #End of the runtime tracking
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"\nTotal execution time: {execution_time:.2f} seconds")

    #TODO: Work on this improvement 
    # # Verify the largest numbers
    # if largest_base:
    #     verified = verify_number(largest_base[0], "", pdf_path)
    #     print(f"\nLargest base number verified: {verified}")

    # if largest_nlp:
    #     verified = verify_number(largest_nlp[0], largest_nlp[2], pdf_path)
    #     print(f"Largest NLP number verified: {verified}")

#MOdify the PDF path for your use case
if __name__ == "__main__":
    pdf_path = '/Users/wdaugherty/Downloads/FY25 Air Force Working Capital Fund.pdf'
    main(pdf_path)