# PDF Hematology Extractor

A Python script (`t22_1.py`) that extracts hematology and morphology information from PDF lab reports and exports structured data to CSV.

## Features

- Extracts patient details (Patient ID, Age, Gender)
- Extracts location details (City, Province)
- Extracts date details (Month, Year)
- Extracts CBC values:
  - RBC
  - Hemoglobin (Hb)
  - MCV
  - MCH
  - MCHC
  - RDW
- Extracts hemoglobin fractions:
  - HbA, HbA2, HbF, HbD, HbS, HbE, HbC
- Extracts morphology findings and maps grades to numeric values
- Processes multiple PDF files in a folder and generates one CSV output

## Requirements

- Python 3.8+
- Install dependencies:

```bash
pip install -r requirements.txt