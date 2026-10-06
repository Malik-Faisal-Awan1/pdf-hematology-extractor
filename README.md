<div align="center">

# 🩸 PDF Hematology Extractor

**Turn hematology lab report PDFs into clean, structured CSV data.**

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Output](https://img.shields.io/badge/Output-CSV-2E7D32)
![Input](https://img.shields.io/badge/Input-PDF-D32F2F)

<br>

<img width="800" alt="Hematology Output" src="https://github.com/user-attachments/assets/7b8c51c2-e36d-4c7f-8efb-a3a9ac273455" />

<sub>Sample CSV output generated from a folder of lab reports</sub>

</div>

---

## 📖 Overview

`t22_1.py` reads hematology and morphology information from PDF lab reports and exports it as one structured CSV file. It can process a whole folder of PDFs in a single run.

## ✨ Features

| Category | Extracted Fields |
|---|---|
| 🧑 **Patient** | Patient ID, Age, Gender |
| 📍 **Location** | City, Province |
| 📅 **Date** | Month, Year |
| 🧪 **CBC** | RBC, Hemoglobin (Hb), MCV, MCH, MCHC, RDW |
| 🧬 **Hb Fractions** | HbA, HbA2, HbF, HbD, HbS, HbE, HbC |
| 🔬 **Morphology** | Findings, with grades mapped to numeric values |

**Plus:** batch processing of multiple PDFs into a single CSV.

## ⚙️ Requirements

- Python 3.8+
- Dependencies:

```bash
pip install -r requirements.txt
```

## 🚀 Usage

```bash
python t22_1.py
```
