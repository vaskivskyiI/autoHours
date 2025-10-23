#!/usr/bin/env python3
"""
PDF Analysis Tool - Examine PDF structure and content
"""

import sys
import pdfplumber
from pathlib import Path

def analyze_pdf(pdf_path: str):
    """Analyze PDF structure and extract all available data"""
    print(f"Analyzing: {pdf_path}")
    print("=" * 50)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}")
            print()

            for i, page in enumerate(pdf.pages):
                print(f"Page {i+1}:")
                print("-" * 20)

                # Extract text
                text = page.extract_text()
                if text:
                    print("Text content:")
                    print(text[:500] + "..." if len(text) > 500 else text)
                    print()

                # Extract tables
                tables = page.extract_tables()
                if tables:
                    print(f"Found {len(tables)} table(s):")
                    for j, table in enumerate(tables):
                        print(f"  Table {j+1}:")
                        # Show first few rows
                        for k, row in enumerate(table[:5]):
                            print(f"    Row {k}: {row}")
                        if len(table) > 5:
                            print(f"    ... and {len(table) - 5} more rows")
                        print()
                else:
                    print("No tables found on this page.")

                print()

    except Exception as e:
        print(f"Error analyzing PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_pdf.py <pdf_file>")
        sys.exit(1)

    pdf_file = sys.argv[1]
    if not Path(pdf_file).exists():
        print(f"File not found: {pdf_file}")
        sys.exit(1)

    analyze_pdf(pdf_file)