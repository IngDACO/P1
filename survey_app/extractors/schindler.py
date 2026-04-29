import pdfplumber
import re

PARAMS = [
    "BS", "BT", "BK", "BKS", "TK", "TKA", "TKS",
    "TSW", "TKSW", "TS", "SF1", "SF2", "SG", "TG",
    "BGS", "BKF1", "BKF2"
]

def extract_from_pdf(pdf_file) -> dict:
    found = {p: None for p in PARAMS}
    try:
        with pdfplumber.open(pdf_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += "\n" + text

        for param in PARAMS:
            pattern = rf'\b{re.escape(param)}\s*=\s*(\d+(?:\.\d+)?)'
            match = re.search(pattern, full_text)
            if match:
                found[param] = float(match.group(1))

    except Exception as e:
        print(f"Error leyendo PDF: {e}")

    return found
