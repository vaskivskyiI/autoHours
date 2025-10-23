# Stroskovnik PDF Parser

A standalone Python tool for parsing Stroskovnik timesheet PDFs and generating processed timesheets with calculated arrival/departure times.

## Features

- **PDF Parsing**: Extracts timesheet data from existing PDF files
- **Time Calculation**: Automatically calculates arrival and departure times based on working hours
- **Secondary Work Support**: Handles business trips and secondary work types
- **Configurable Settings**: Customizable arrival times, scattering, and output options
- **PDF Generation**: Creates formatted PDF reports with processed data

## Installation

1. Ensure Python 3.8+ is installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
python stroskovnik_parser.py input.pdf
```

This will parse `input.pdf` and generate `output/input_processed.pdf`

### Advanced Usage

```bash
# Specify output file
python stroskovnik_parser.py input.pdf -o custom_output.pdf

# Use custom configuration
python stroskovnik_parser.py input.pdf -c my_config.json

# Override settings via command line
python stroskovnik_parser.py input.pdf --arrival-time 08:30 --scattering 15
```

## Configuration

Create a `config.json` file to customize behavior:

```json
{
  "arrival_time": "09:00",
  "scattering_minutes": 10,
  "enable_secondary": false,
  "secondary_name": "",
  "secondary_percent": 0,
  "secondary_include_breaks": true,
  "output_dir": "output"
}
```

### Configuration Options

- `arrival_time`: Default arrival time (HH:MM format)
- `scattering_minutes`: Minutes to add for time variation
- `enable_secondary`: Enable secondary work type processing
- `secondary_name`: Name for secondary work type
- `secondary_percent`: Percentage for secondary work calculations
- `secondary_include_breaks`: Include breaks in secondary work calculations
- `output_dir`: Directory for generated PDFs

## Command Line Options

- `input`: Input PDF file path (required)
- `-o, --output`: Output PDF file path (optional)
- `-c, --config`: Configuration JSON file path (optional)
- `--arrival-time`: Override arrival time (HH:MM)
- `--scattering`: Override scattering minutes

## Input PDF Format

The tool expects PDFs containing:
- Employee name
- Period (month and year)
- Timesheet table with dates and hours
- Work type indicators (001 for regular work, 002 for business trips)

## Output

Generates a formatted PDF with:
- Employee information
- Processed working days
- Calculated arrival and departure times
- Break time calculations
- Total hours summary

## Dependencies

- PyPDF2: PDF text extraction
- pdfplumber: Advanced PDF table parsing
- reportlab: PDF generation
- pandas: Data manipulation
- python-dateutil: Date handling

## Troubleshooting

### Common Issues

1. **PDF parsing fails**: Ensure the PDF contains extractable text and tables
2. **No data extracted**: Check that the PDF format matches expected structure
3. **Import errors**: Make sure all dependencies are installed correctly

### Debug Mode

For detailed processing information, check the console output when running the tool.

## License

This tool is provided as-is for processing Stroskovnik timesheet PDFs.