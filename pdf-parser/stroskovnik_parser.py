#!/usr/bin/env python3
"""
Stroskovnik PDF Parser - Standalone Tool
Extracts timesheet data from PDF files and generates processed PDFs
"""

import sys
import json
import argparse
import copy
from pathlib import Path
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Tuple

import pdfplumber
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pandas as pd


class StroskovnikPDFParser:
    """Standalone PDF parser for Stroskovnik timesheets"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self.load_config(config_path)
        self.styles = getSampleStyleSheet()

    def load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "arrival_time": "09:00",
            "scattering_minutes": 10,
            "enable_secondary": False,
            "secondary_name": "",
            "secondary_percent": 0,
            "secondary_include_breaks": True,
            "output_dir": "output"
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")

        return default_config

    def save_config(self, config_path: Optional[str] = None) -> None:
        """Save current configuration to file"""
        config_path = config_path or "config.json"
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save config to {config_path}: {e}")

    def parse_pdf(self, pdf_path: str) -> Optional[Dict]:
        """Parse PDF file and extract timesheet data"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_content = ""
                tables_data = []

                # Extract text from all pages
                for page in pdf.pages:
                    text_content += page.extract_text() + "\n"

                    # Try to extract tables
                    tables = page.extract_tables()
                    tables_data.extend(tables)

                # Parse the extracted data
                return self._parse_extracted_data(text_content, tables_data)

        except Exception as e:
            print(f"Error parsing PDF {pdf_path}: {e}")
            return None

    def _parse_extracted_data(self, text: str, tables: List) -> Optional[Dict]:
        """Parse extracted text and tables into structured data"""
        # Extract employee name
        name_match = re.search(r'Ime in priimek:\s*([^\n]+)', text)
        if not name_match:
            print("Could not extract employee name from PDF")
            return None

        name = name_match.group(1).strip()

        # Extract period
        period_match = re.search(r'STROŠKOVNIK ZA ODBOBJE:\s*([^\n]+)', text)
        if not period_match:
            print("Could not extract period from PDF")
            return None

        period_str = period_match.group(1).strip()
        # Parse period like "01.09.2025 - 30.09.2025"
        period_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})\s*-\s*(\d{2})\.(\d{2})\.(\d{4})', period_str)
        if period_match:
            start_day, start_month, start_year = period_match.groups()[:3]
            end_day, end_month, end_year = period_match.groups()[3:]
            month_name = self._get_month_name(int(start_month))
            period = f"{month_name} {start_year}"
        else:
            period = period_str

        # Parse working days from tables
        working_days = self._parse_stroskovnik_table(tables)

        if not working_days:
            print("No working days data found in PDF")
            return None

        return {
            "name": name,
            "period": period,
            "month": month_name.lower() if 'month_name' in locals() else "oktober",
            "year": start_year if 'start_year' in locals() else "2025",
            "working_days": len(working_days),
            "table_data": working_days
        }

    def _get_month_name(self, month_num: int) -> str:
        """Convert month number to Slovenian month name"""
        months = {
            1: 'januar', 2: 'februar', 3: 'marec', 4: 'april', 5: 'maj', 6: 'junij',
            7: 'julij', 8: 'avgust', 9: 'september', 10: 'oktober', 11: 'november', 12: 'december'
        }
        return months.get(month_num, 'oktober')

    def _parse_stroskovnik_table(self, tables: List) -> List[Dict]:
        """Parse the main Stroskovnik timesheet table"""
        working_days = []

        for table in tables:
            if not table or len(table) < 2:
                continue

            # Look for the main timesheet table (has "Dejanske ure" column)
            header = table[0] if table else []
            header_text = ' '.join(str(cell) for cell in header if cell)

            if 'Dejanske' not in header_text and 'ure' not in header_text:
                continue

            # Find day columns (they should be numbered 1-30 or similar)
            day_columns = {}
            for i, col in enumerate(header):
                col_str = str(col).strip()
                # Look for day numbers in column headers - they can be like "P 1", "T 2", "3", etc.
                day_match = re.search(r'(\d{1,2})', col_str)
                if day_match:
                    day_num = int(day_match.group(1))
                    if 1 <= day_num <= 31:
                        day_columns[day_num] = i

            if not day_columns:
                continue

            # Process each data row (skip header)
            for row in table[1:]:
                if len(row) <= max(day_columns.values()):
                    continue

                # Skip total/summary rows (Vsota, Total, etc.)
                first_cell = str(row[0]).strip().lower() if len(row) > 0 else ''
                if any(keyword in first_cell for keyword in ['vsota', 'total', 'skupaj', 'sum']):
                    continue

                # Get work type from column 3 (Šifra vrste dela)
                work_type_code = str(row[2]).strip() if len(row) > 2 else '001'
                if work_type_code == '001':
                    work_type = 'normal-work'
                elif work_type_code == '002':
                    work_type = 'business-trip'
                else:
                    work_type = 'other'  # Ignore other work types like 010 for time calculations

                # Get project code for reference
                project_code = str(row[0]).strip() if len(row) > 0 else ''

                # Collect hours for each day
                for day, col_idx in day_columns.items():
                    if col_idx >= len(row):
                        continue

                    hours_str = str(row[col_idx]).replace(',', '.').strip()
                    if not hours_str or hours_str in ['', '0', '0.0', '0,0']:
                        continue

                    try:
                        hours = float(hours_str)
                        if hours > 0:
                            # Check if we already have an entry for this day
                            existing_day = next((d for d in working_days if d["day"] == day), None)

                            if existing_day:
                                # Add to existing day
                                if work_type == 'business-trip':
                                    existing_day["totalHours002"] += hours
                                elif work_type == 'normal-work':
                                    existing_day["totalHours001"] += hours
                                # Ignore 'other' work types for time calculations
                                existing_day["totalHours"] = existing_day["totalHours001"] + existing_day["totalHours002"]
                                if existing_day["totalHours002"] > 0:
                                    existing_day["type"] = "business-trip"
                                    existing_day["hasBusinessTrip"] = True
                            else:
                                # Create new day entry
                                day_data = {
                                    "day": day,
                                    "totalHours001": hours if work_type == 'normal-work' else 0,
                                    "totalHours002": hours if work_type == 'business-trip' else 0,
                                    "hasBusinessTrip": work_type == 'business-trip',
                                    "type": work_type if work_type in ['business-trip', 'normal-work'] else 'normal-work',
                                    "totalHours": hours if work_type in ['business-trip', 'normal-work'] else 0,
                                    "projectCode": project_code
                                }
                                working_days.append(day_data)

                    except ValueError:
                        continue

        return sorted(working_days, key=lambda x: x["day"])

    def _determine_work_type(self, row: List) -> str:
        """Determine work type from row content"""
        row_text = ' '.join(str(cell) for cell in row if cell).lower()

        if '002' in row_text or 'business' in row_text or 'potovanje' in row_text:
            return '002'
        else:
            return '001'  # Default to regular work

    def calculate_times(self, total_hours: float) -> Dict:
        """Calculate arrival/departure times with scattering"""
        import random
        hours, minutes = map(int, self.config["arrival_time"].split(':'))
        base_minutes = hours * 60 + minutes

        scattering = self.config["scattering_minutes"]
        variation = random.randint(-scattering, scattering)

        arrival_minutes = base_minutes + variation
        break_minutes = round(30 * (total_hours / 8))
        work_minutes = round(total_hours * 60)
        departure_minutes = arrival_minutes + work_minutes

        return {
            "arrival": self._format_time(arrival_minutes),
            "departure": self._format_time(departure_minutes),
            "break_minutes": break_minutes
        }

    def _format_time(self, total_minutes: int) -> str:
        """Format minutes into HH:MM string"""
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"

    def generate_pdf(self, data: Dict, output_path: str, secondary_work: Optional[Dict] = None):
        """Generate PDF with processed timesheet data"""
        # Ensure times are calculated for consistency
        self._calculate_times_for_all_days(data)
        # Set up Unicode support
        import reportlab.rl_config
        reportlab.rl_config.warnOnMissingFontGlyphs = 0  # Suppress font warnings

        # Register Arial font for better Unicode support
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os

        try:
            fonts_dir = 'C:/Windows/Fonts'
            arial_path = os.path.join(fonts_dir, 'arial.ttf')
            if os.path.exists(arial_path):
                pdfmetrics.registerFont(TTFont('Arial', arial_path))
                pdfmetrics.registerFont(TTFont('Arial-Bold', os.path.join(fonts_dir, 'arialbd.ttf')))
                print("Arial fonts registered for Unicode support")
            else:
                print("Arial font not found, using default fonts")
        except Exception as e:
            print(f"Could not register Arial font: {e}")

        # Use built-in fonts with UTF-8 encoding
        doc = SimpleDocTemplate(output_path, pagesize=A4, encoding='utf-8')
        elements = []

        # Title with Unicode characters
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1,  # Center
            encoding='utf-8'
        )
        # Try to use Arial if available, otherwise use default
        if 'Arial-Bold' in pdfmetrics.getRegisteredFontNames():
            title_style.fontName = 'Arial-Bold'

        title_text = "Pregled delovnega časa"
        elements.append(Paragraph(title_text, title_style))

        # Employee info
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=1,
            encoding='utf-8'
        )
        if 'Arial' in pdfmetrics.getRegisteredFontNames():
            info_style.fontName = 'Arial'

        period_text = f"{data['period']} - {data['name']}"
        elements.append(Paragraph(period_text, info_style))

        # Create table data with Unicode characters
        table_data = [
            ["Datum", "Čas prihoda", "Čas odhoda", "Skupaj število ur", "Odmor med delovnim časom"]
        ]

        total_work_hours = 0
        total_break_minutes = 0

        for day_data in data["table_data"]:
            if day_data["type"] == "business-trip":
                table_data.append([
                    self._format_date(day_data["day"], data["period"]),
                    "-",
                    "-",
                    "Službeno potovanje",
                    "-"
                ])
            else:
                # Use pre-calculated times for consistency
                arrival_time = day_data["arrival"]
                departure_time = day_data["departure"]
                break_mins = day_data.get("breakMinutes", 0)
                work_hours = day_data["totalHours001"]

                table_data.append([
                    self._format_date(day_data["day"], data["period"]),
                    arrival_time,
                    departure_time,
                    f"{work_hours:.1f}",
                    f"{break_mins} min" if break_mins > 0 else "-"
                ])
                total_work_hours += work_hours
                total_break_minutes += break_mins

        # Add totals row
        table_data.append([
            "Skupaj:",
            "",
            "",
            f"{total_work_hours:.1f}",
            f"{total_break_minutes} min"
        ])

        # Create and style table
        # Determine available fonts
        header_font = 'Arial-Bold' if 'Arial-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
        body_font = 'Arial' if 'Arial' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), header_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('FONTNAME', (0, 1), (-1, -1), body_font),
        ]))

        elements.append(table)

        # Build PDF
        doc.build(elements)

    def _generate_filename(self, data: Dict) -> str:
        """Generate filename matching chrome extension format"""
        month_names = {
            'januar': 'Januar', 'februar': 'Februar', 'marec': 'Marec', 'april': 'April',
            'maj': 'Maj', 'junij': 'Junij', 'julij': 'Julij', 'avgust': 'Avgust',
            'september': 'September', 'oktober': 'Oktober', 'november': 'November', 'december': 'December'
        }

        # Extract month and year from period
        month_match = re.search(r'(\w+)\s+(\d{4})', data['period'])
        if month_match:
            month_name = month_names.get(month_match.group(1).lower(), 'Oktober')
            year = month_match.group(2)
        else:
            month_name = 'Oktober'
            year = '2025'

        # Clean name for filename
        clean_name = re.sub(r'[^a-zA-Z\s]', '', data['name'])
        clean_name = re.sub(r'\s+', '_', clean_name).strip()

        if not clean_name:
            clean_name = 'Timesheet'

        return f"{month_name}_{year}_{clean_name}"

    def _generate_secondary_filename(self, data: Dict, secondary_work: Dict) -> str:
        """Generate filename for secondary work PDF"""
        base_filename = self._generate_filename(data)
        work_name = secondary_work.get("name", "Secondary").replace(" ", "_")
        work_name = re.sub(r'[^a-zA-Z0-9_]', '', work_name)
        return f"{base_filename}_{work_name}"

    def _create_secondary_data(self, data: Dict, secondary_work: Dict) -> Dict:
        """Create secondary work data based on primary work times"""
        import random
        secondary_data = copy.deepcopy(data)

        # Calculate times for all days first to get concrete arrival/departure times
        extracted_times = []
        for day_data in data["table_data"]:
            if day_data["type"] == "business-trip":
                extracted_times.append({
                    "day": day_data["day"],
                    "type": "business-trip",
                    "arrival": "-",
                    "departure": "-",
                    "totalHours": day_data["totalHours001"] + day_data["totalHours002"],
                    "workHours": 0,
                    "breakMinutes": 0
                })
            else:
                times = self.calculate_times(day_data["totalHours001"])
                extracted_times.append({
                    "day": day_data["day"],
                    "type": "normal-work",
                    "arrival": times["arrival"],
                    "departure": times["departure"],
                    "totalHours": day_data["totalHours001"],
                    "workHours": day_data["totalHours001"],
                    "breakMinutes": times["break_minutes"]
                })

    def _calculate_times_for_all_days(self, data: Dict) -> None:
        """Calculate and store times for all days in the data for consistency"""
        for day_data in data["table_data"]:
            if day_data["type"] != "business-trip" and "arrival" not in day_data:
                times = self.calculate_times(day_data["totalHours001"])
                day_data["arrival"] = times["arrival"]
                day_data["departure"] = times["departure"]
                day_data["breakMinutes"] = times["break_minutes"]

    def _create_secondary_data(self, data: Dict, secondary_work: Dict) -> Dict:
        """Create secondary work data based on primary work times"""
        # Ensure times are calculated for primary work
        self._calculate_times_for_all_days(data)

        secondary_data = copy.deepcopy(data)

        # Create secondary work data
        secondary_table_data = []
        for day_data in data["table_data"]:
            if day_data["type"] == "business-trip":
                secondary_table_data.append({
                    "day": day_data["day"],
                    "type": "business-trip",
                    "totalHours001": 0,
                    "totalHours002": day_data["totalHours002"],
                    "hasBusinessTrip": True
                })
            else:
                # Parse departure time from primary work
                dep_parts = day_data["departure"].split(':')
                departure_minutes_primary = int(dep_parts[0]) * 60 + int(dep_parts[1])

                # Secondary work starts exactly at primary work end time (no additional scattering)
                arrival_minutes_secondary = departure_minutes_primary

                # Calculate work hours based on percentage
                percent = float(secondary_work.get("percent", 0)) / 100.0
                work_hours_secondary = percent * 8  # 8 hours is full day

                # Calculate break minutes if enabled
                break_minutes_secondary = 0
                if secondary_work.get("include_breaks", True):
                    break_minutes_secondary = round(30 * (work_hours_secondary / 8))

                # Calculate departure for secondary work
                work_minutes_secondary = round(work_hours_secondary * 60)
                departure_minutes_secondary = arrival_minutes_secondary + work_minutes_secondary

                secondary_table_data.append({
                    "day": day_data["day"],
                    "type": "normal-work",
                    "totalHours001": work_hours_secondary,
                    "totalHours002": 0,
                    "hasBusinessTrip": False,
                    "arrival": self._format_time(arrival_minutes_secondary),
                    "departure": self._format_time(departure_minutes_secondary),
                    "breakMinutes": break_minutes_secondary
                })

        secondary_data["table_data"] = secondary_table_data
        return secondary_data

    def _format_date(self, day: int, period: str) -> str:
        """Format date for PDF output"""
        month_match = re.search(r'(\w+)\s+(\d{4})', period)
        if month_match:
            month_name = month_match.group(1).lower()
            year = month_match.group(2)

            months = {
                'januar': '01', 'februar': '02', 'marec': '03', 'april': '04',
                'maj': '05', 'junij': '06', 'julij': '07', 'avgust': '08',
                'september': '09', 'oktober': '10', 'november': '11', 'december': '12'
            }

            month = months.get(month_name, '10')
            return f"{day:02d}.{month}.{year}"

        return f"{day:02d}.10.2025"  # Default fallback

    def process_file(self, input_path: str, output_path: Optional[str] = None, secondary_work: Optional[Dict] = None) -> bool:
        """Process a single PDF file"""
        print(f"Processing: {input_path}")

        # Parse PDF
        data = self.parse_pdf(input_path)
        if not data:
            print("Failed to parse PDF data")
            return False

        # Generate output path
        if not output_path:
            input_file = Path(input_path)
            output_dir = Path(self.config["output_dir"])
            output_dir.mkdir(exist_ok=True)

            base_name = self._generate_filename(data)
            output_path = output_dir / f"{base_name}.pdf"
        else:
            output_dir = Path(output_path).parent

        # Generate primary PDF
        try:
            self.generate_pdf(data, str(output_path))
            print(f"Generated: {output_path}")

            # Generate secondary PDF if configured
            if (secondary_work and secondary_work.get("enabled", False) and secondary_work.get("percent", 0) > 0) or \
               (self.config.get("enable_secondary", False) and self.config.get("secondary_percent", 0) > 0):
                # Use provided secondary_work or fall back to config
                if not secondary_work:
                    secondary_work = {
                        "enabled": self.config["enable_secondary"],
                        "name": self.config.get("secondary_name", "Secondary"),
                        "percent": self.config["secondary_percent"],
                        "include_breaks": self.config.get("secondary_include_breaks", True)
                    }
                secondary_data = self._create_secondary_data(data, secondary_work)
                secondary_filename = self._generate_secondary_filename(data, secondary_work)
                secondary_path = output_dir / f"{secondary_filename}.pdf"

                self.generate_pdf(secondary_data, str(secondary_path), secondary_work)
                print(f"Generated secondary: {secondary_path}")

            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False

    def process_folder(self, folder_path: str, secondary_work: Optional[Dict] = None) -> bool:
        """Process all PDF files in a folder"""
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            print(f"Error: {folder_path} is not a valid directory")
            return False

        # Find all PDF files in the folder
        pdf_files = list(folder.glob("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in {folder_path}")
            return False

        print(f"Found {len(pdf_files)} PDF files in {folder_path}")

        # Create output directory
        output_dir = Path(self.config["output_dir"])
        output_dir.mkdir(exist_ok=True)

        success_count = 0
        total_count = len(pdf_files)

        for pdf_file in sorted(pdf_files):
            print(f"\n--- Processing {pdf_file.name} ---")

            # Parse PDF to get period info for organizing output
            data = self.parse_pdf(str(pdf_file))
            if not data:
                print(f"Failed to parse {pdf_file.name}, skipping...")
                continue

            # Create month/year subfolder for organization
            month_year = f"{data['month'].capitalize()}_{data['year']}"
            month_output_dir = output_dir / month_year
            month_output_dir.mkdir(exist_ok=True)

            # Generate base filename
            base_name = self._generate_filename(data)
            output_path = month_output_dir / f"{base_name}.pdf"

            # Process the file
            if self.process_file(str(pdf_file), str(output_path), secondary_work):
                success_count += 1
            else:
                print(f"Failed to process {pdf_file.name}")

        print(f"\n--- Bulk processing complete ---")
        print(f"Successfully processed: {success_count}/{total_count} files")

        return success_count > 0


def main():
    parser = argparse.ArgumentParser(description="Stroskovnik PDF Parser - Extract and reformat timesheet data")
    parser.add_argument("input", help="Input PDF file path or folder containing PDF files")
    parser.add_argument("-o", "--output", help="Output PDF file path (ignored when processing folders)")
    parser.add_argument("-c", "--config", help="Configuration JSON file")
    parser.add_argument("--arrival-time", help="Arrival time (HH:MM)", default="09:00")
    parser.add_argument("--scattering", type=int, help="Scattering minutes", default=10)
    parser.add_argument("--secondary", action="store_true", help="Enable secondary work PDF generation")
    parser.add_argument("--secondary-name", help="Name for secondary work", default="")
    parser.add_argument("--secondary-percent", type=float, help="Percentage of full day for secondary work", default=0)
    parser.add_argument("--secondary-no-breaks", action="store_true", help="Don't include breaks in secondary work calculations")

    args = parser.parse_args()

    # Create parser instance
    pdf_parser = StroskovnikPDFParser(args.config)

    # Override config with command line args
    config_updated = False
    if args.arrival_time != "09:00":  # Only update if explicitly provided
        pdf_parser.config["arrival_time"] = args.arrival_time
        config_updated = True
    if args.scattering != 10:  # Only update if explicitly provided
        pdf_parser.config["scattering_minutes"] = args.scattering
        config_updated = True

    # Set up secondary work if enabled via command line or config
    secondary_work = None
    if args.secondary and args.secondary_percent > 0:
        # Command line secondary work settings
        secondary_work = {
            "enabled": True,
            "name": args.secondary_name or "Secondary",
            "percent": args.secondary_percent,
            "include_breaks": not args.secondary_no_breaks
        }
        # Update config
        pdf_parser.config["enable_secondary"] = True
        pdf_parser.config["secondary_name"] = args.secondary_name or "Secondary"
        pdf_parser.config["secondary_percent"] = args.secondary_percent
        pdf_parser.config["secondary_include_breaks"] = not args.secondary_no_breaks
        config_updated = True
    elif pdf_parser.config.get("enable_secondary", False) and pdf_parser.config.get("secondary_percent", 0) > 0:
        # Use config settings
        secondary_work = {
            "enabled": True,
            "name": pdf_parser.config.get("secondary_name", "Secondary"),
            "percent": pdf_parser.config["secondary_percent"],
            "include_breaks": pdf_parser.config.get("secondary_include_breaks", True)
        }

    # Process the file or folder
    input_path = Path(args.input)
    if input_path.is_dir():
        # Process folder
        success = pdf_parser.process_folder(str(input_path), secondary_work)
    else:
        # Process single file
        success = pdf_parser.process_file(args.input, args.output, secondary_work)

    # Save config if it was updated
    if config_updated:
        pdf_parser.save_config(args.config)

    if success:
        print("✅ PDF processing completed successfully!")
        return 0
    else:
        print("❌ PDF processing failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())