import pdfplumber
import re
import pandas as pd
import os
from typing import Dict

# Mapping for morphology values
MORPH_MAP = {
    '+': 1,
    '++': 2,
    '+++': 3,
    '++++': 4,
    'Few': 6,
    'few': 6,
    'Predominantly': 1,
}

# Known morphology labels (expanded)
MORPH_FIELDS = {
    'Anisocytosis': 'Anisocytosis',
    'Poikilocytosis': 'Poikilocytosis',
    'Microcytosis': 'Microcytosis',
    'Hypochromia': 'Hypochromia',
    'Macrocytosis': 'Macrocytosis',
    'Pencil_Cell': 'Pencil Cells',
    'Elliptocytosis': 'Elliptocytes',
    'Target_Cell': 'Target Cells',
    'Spehrocytosis': ['Spherocytosis', 'Spherocytes'],  # Handle both spellings
    'Fragmentation': 'Fragmentation',
    'Sickle_Cell': 'Sickle Cells',
    'Tear_Drop_Cell': 'Tear Drop Cells',
    'Dimorphism': 'Dimorphism',
    'N_N': 'Normocytic Normochromic',
    'NRBC': 'NRBC',
}

# Expanded location database
LOCATION_DB = {
    'C.C. Johar Town': ('Lahore', 'Punjab'),
    'Lahore Branch': ('Lahore', 'Punjab'),
    'STAT Lab': ('Peshawar', 'Khyber Pakhtunkhwa'),
    'Test Zone DC': ('Peshawar', 'Khyber Pakhtunkhwa'),
    'Test Zone Diagnostic Centre': ('Lahore', 'Punjab'),
    'TZDC Standard': ('Lahore', 'Punjab'),
    'TZL Dera Ismail Khan': ('Dera Ismail Khan', 'Khyber Pakhtunkhwa'),
    'Dera Ismail Khan': ('Dera Ismail Khan', 'Khyber Pakhtunkhwa'),
    'Collection Center Pak Pattan': ('Pakpattan', 'Punjab'),
    'Pak Pattan': ('Pakpattan', 'Punjab'),
    'TZDC-CC-Pakpattan': ('Pakpattan', 'Punjab'),
    'Naeem Surgical Hospital': ('Lahore', 'Punjab'),
    'GLOBAL DIAGNOSTIC LAB LAHORE': ('Lahore', 'Punjab'),
}


def short_month(month_name):
    """
    Convert full month name to 3-letter abbreviation.
    If already abbreviated or not found, returns first 3 characters.
    """
    months = {
        'January': 'Jan', 'February': 'Feb', 'March': 'Mar', 'April': 'Apr',
        'May': 'May', 'June': 'Jun', 'July': 'Jul', 'August': 'Aug',
        'September': 'Sep', 'October': 'Oct', 'November': 'Nov', 'December': 'Dec'
    }
    return months.get(month_name.capitalize(), month_name[:3] if len(month_name) >= 3 else month_name)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
        return text.strip()
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return ''


def get_hemoglobin_value(hb_type: str, text: str) -> str:
    """
    Extract hemoglobin fraction values (HbA, HbF, HbA2, etc.)
    Uses specific pattern to avoid false matches like "Hb Fractions"
    """
    # Pattern: Hb X (where X is A, F, A2, etc.) followed by numbers and percentage
    pattern = rf'\bHb\s+{re.escape(hb_type)}\b.*?%\s*([\d.]+)'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1)
    
    # Fallback: try simpler pattern
    pattern2 = rf'\bHb\s+{re.escape(hb_type)}\b\s+[\d.\s%-]+([\d.]+)$'
    match2 = re.search(pattern2, text, re.IGNORECASE | re.MULTILINE)
    if match2:
        # Get the last number on the line
        line = match2.group(0)
        numbers = re.findall(r'[\d.]+', line)
        return numbers[-1] if numbers else ''
    
    return ''


def get_value(label: str, text: str, use_word_boundary: bool = False) -> str:
    """
    Extract the last numeric value after a given label.
    """
    if use_word_boundary:
        # For labels like "Hb F" that might be part of "Hb Fractions"
        pattern = rf'\b{re.escape(label)}\b\s+[\d.]+'
    else:
        pattern = rf'{re.escape(label)}.*'
    
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        numbers = re.findall(r'[\d.]+', match.group(0))
        return numbers[-1] if numbers else ''
    return ''


def extract_morphology_value(label, text):
    """Extract morphology value and map to number"""
    # Handle if label is a list (for alternative names)
    labels_to_try = [label] if isinstance(label, str) else label
    
    for lbl in labels_to_try:
        # Try different patterns
        patterns = [
            rf'{re.escape(lbl)}\s*(\++|Few|few|Predominantly)',  # Standard pattern
            rf'{re.escape(lbl)}\s+(\++|Few|few|Predominantly)',  # With space
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                return str(MORPH_MAP.get(val, ''))
    
    return ''


def extract_data_from_pdf(pdf_path: str) -> Dict[str, str]:
    """Extract all required data from a PDF file"""
    filename = os.path.basename(pdf_path)
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print(f"Warning: No text extracted from {filename}")
        return {'Source_File': filename}
    
    data = {'Source_File': filename}
    
    # Patient_ID: Last part after last '-' in Specimen ID
    match = re.search(r'Specimen ID:\s*([A-Z0-9-]+)', text, re.IGNORECASE)
    if match:
        spec_id = match.group(1)
        data['Patient_ID'] = spec_id.split('-')[-1]
    else:
        data['Patient_ID'] = ''
    
    # Age and Gender - try multiple patterns
    data['Age'] = ''
    data['Gender'] = ''
    
    # Primary pattern
    age_gender_match = re.search(
        r'Age/Gender:\s*([\d.]+)\s*(Year\(s\)|Month\(s\)|Day\(s\))/(\w+)',
        text, re.IGNORECASE
    )
    
    if age_gender_match:
        age_value = float(age_gender_match.group(1))
        unit = age_gender_match.group(2).lower()
        if 'month' in unit:
            age_value /= 12
        elif 'day' in unit:
            age_value /= 365
        data['Age'] = f'{age_value:.1f}'
        data['Gender'] = age_gender_match.group(3)
    else:
        # Fallback pattern (Age and Gender might be separate)
        age_match = re.search(r'Age[:\s]+([\d.]+)\s*(Year|Month|Day)', text, re.IGNORECASE)
        gender_match = re.search(r'Gender[:\s]+(\w+)', text, re.IGNORECASE)
        
        if age_match:
            age_value = float(age_match.group(1))
            unit = age_match.group(2).lower()
            if 'month' in unit:
                age_value /= 12
            elif 'day' in unit:
                age_value /= 365
            data['Age'] = f'{age_value:.1f}'
        
        if gender_match:
            data['Gender'] = gender_match.group(1)
    
    # City and Province from location
    data['City'] = ''
    data['Province'] = ''
    
    # Try to find location from multiple sources
    search_text = ''
    
    # Check "Registered At"
    center_match = re.search(r'Registered At\s*(.+?)(?=\n|Consultant)', text, re.IGNORECASE)
    if center_match:
        search_text += ' ' + center_match.group(1).strip()
    
    # Check "Center:" field
    center_field = re.search(r'Center:\s*(.+?)(?=\n|Ref)', text, re.IGNORECASE)
    if center_field:
        search_text += ' ' + center_field.group(1).strip()
    
    # Clean up the search text
    search_text = search_text.replace('Test Zone Diagnostic Centre, Lahore.', 'Test Zone Diagnostic Centre')
    
    # Match against location database
    for location, (city, province) in LOCATION_DB.items():
        if location.lower() in search_text.lower():
            data['City'] = city
            data['Province'] = province
            break
    
    # If still not found, try searching entire text for city names
    if not data['City']:
        city_keywords = {
            'Lahore': ('Lahore', 'Punjab'),
            'Karachi': ('Karachi', 'Sindh'),
            'Islamabad': ('Islamabad', 'Islamabad Capital Territory'),
            'Rawalpindi': ('Rawalpindi', 'Punjab'),
            'Faisalabad': ('Faisalabad', 'Punjab'),
            'Multan': ('Multan', 'Punjab'),
            'Peshawar': ('Peshawar', 'Khyber Pakhtunkhwa'),
            'Quetta': ('Quetta', 'Balochistan'),
            'Sialkot': ('Sialkot', 'Punjab'),
            'Gujranwala': ('Gujranwala', 'Punjab'),
            'Dera Ismail Khan': ('Dera Ismail Khan', 'Khyber Pakhtunkhwa'),
            'Pakpattan': ('Pakpattan', 'Punjab'),
            'Pak Pattan': ('Pakpattan', 'Punjab'),
        }
        
        for city_name, (city, province) in city_keywords.items():
            if city_name.lower() in text.lower():
                data['City'] = city
                data['Province'] = province
                break
    
    # Month and Year from Date Collected
    date_match = (
        re.search(r'Collected On:\s*(\d+)-(\w+)-(\d{4})', text) or
        re.search(r'Date Collected:\s*(\d+)-(\w+)-(\d{4})', text) or
        re.search(r'Reported On:\s*(\d+)-(\w+)-(\d{4})', text)
    )
    if date_match:
        month_raw = date_match.group(2)
        data['Month'] = short_month(month_raw)
        data['Year'] = date_match.group(3)
    else:
        data['Month'] = ''
        data['Year'] = ''
    
    # Hematology values
    data['RBC'] = get_value('Total RBCs', text) or get_value('Total RBC', text) or get_value('RBC', text)
    data['Hb'] = get_value('Hemoglobin (HB)', text) or get_value('Hemoglobin', text)
    data['MCV'] = get_value('MCV', text)
    data['MCH'] = get_value('MCH', text)
    data['MCHC'] = get_value('MCHC', text)
    data['RDW'] = get_value('RDW', text)
    
    # Hemoglobin fractions - use specific function to avoid false matches
    data['HbA'] = get_hemoglobin_value('A', text)
    data['HbA2'] = get_hemoglobin_value('A2', text)
    data['HbF'] = get_hemoglobin_value('F', text)
    data['HbD'] = get_hemoglobin_value('D', text)
    data['HbS'] = get_hemoglobin_value('S', text)
    data['HbE'] = get_hemoglobin_value('E', text)
    data['HbC'] = get_hemoglobin_value('C', text)
    
    # Diagnosis - always blank as per original code
    data['Diagnosis'] = ''
    
    # Morphology fields
    for key, label in MORPH_FIELDS.items():
        data[key] = extract_morphology_value(label, text)
    
    return data


def process_pdfs(input_dir: str, output_csv: str = None) -> pd.DataFrame:
    """Process all PDFs in a directory and create CSV"""
    if output_csv is None:
        output_csv = os.path.join(input_dir, 'output.csv')
    
    # Get all PDF files
    if os.path.isdir(input_dir):
        pdf_files = [
            os.path.join(input_dir, f) 
            for f in os.listdir(input_dir) 
            if f.lower().endswith('.pdf')
        ]
    else:
        # Single file
        pdf_files = [input_dir]
    
    print(f"Found {len(pdf_files)} PDF file(s)")
    
    # Extract data from all PDFs
    data_list = []
    for i, pdf in enumerate(pdf_files, 1):
        print(f"Processing {i}/{len(pdf_files)}: {os.path.basename(pdf)}")
        data = extract_data_from_pdf(pdf)
        data_list.append(data)
    
    # Create DataFrame
    df = pd.DataFrame(data_list)
    
    # Define column order
    all_columns = [
        'Source_File', 'Patient_ID', 'Age', 'Gender', 'City', 'Province', 'Month', 'Year',
        'RBC', 'Hb', 'MCV', 'MCH', 'MCHC', 'RDW',
        'HbA', 'HbA2', 'HbF', 'HbD', 'HbS', 'HbE', 'HbC',
        'Diagnosis',
        'Anisocytosis', 'Poikilocytosis', 'Microcytosis', 'Hypochromia', 'Macrocytosis',
        'Pencil_Cell', 'Elliptocytosis', 'Target_Cell', 'Spehrocytosis', 'Fragmentation',
        'Sickle_Cell', 'Tear_Drop_Cell', 'Dimorphism', 'N_N', 'NRBC'
    ]
    
    # Reindex with all columns
    for col in all_columns:
        if col not in df.columns:
            df[col] = ''
    df = df[all_columns]
    
    # Save to CSV
    df.to_csv(output_csv, index=False)
    print(f'\nData extracted to {output_csv}')
    print(f'Total records: {len(df)}')
    
    return df


if __name__ == '__main__':
    # Default directory - update this path as needed
    input_directory = 'C:\\Users\\Faisal\\Downloads\\installation media\\data january'
    
    # Check if directory exists, otherwise use current directory
    if not os.path.exists(input_directory):
        input_directory = os.getcwd()
        print(f"Default directory not found. Using: {input_directory}")
    
    process_pdfs(input_directory)