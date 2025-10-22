# Stroskovnik PDF Generator

Chrome extension that automatically generates PDF timesheets from Stroskovnik pages with proper Slovenian character support.

## Features

- Automatically detects Stroskovnik timesheet pages
- **Floating button** appears only on valid Stroskovnik pages (`https://eds.ijs.si/workflow/activity/`)
- Parses work data and calculates appropriate arrival/departure times
- Handles business trips (002 work type) vs regular work (001 work type)
- Calculates breaks based on total working hours (30 min × hours/8)
- Generates professional PDF timesheet with proper Slovenian Unicode characters (č, š, ž, Č, Š, Ž)
- **Configurable arrival time and scattering** that persists across browser restarts
- **Secondary work (tailgate) support**: Generate two PDFs - primary and secondary work with configurable percentage and break inclusion
- Clean, production-ready extension without debug code

## Installation

1. Download or clone this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top right
4. Click "Load unpacked" and select the `chrome-extension` folder
5. The extension will be installed and ready to use

## Usage

### Method 1: Floating Button (Recommended)
1. Navigate to a Stroskovnik timesheet page (e.g., `https://eds.ijs.si/workflow/activity/`)
2. **A blue floating button "📄 Generate PDF" will appear** in the top-right corner of the page
3. Click the floating button to instantly generate and download your PDF

### Method 2: Extension Popup
1. Navigate to a Stroskovnik timesheet page
2. Click the extension icon in the Chrome toolbar
3. **Configure Settings** (optional):
   - **Arrival Time**: Set your base arrival time (default: 09:00)
   - **Scattering**: Set random variation in minutes (default: ±10 minutes)
   - **Secondary Work**: Enable and configure additional work PDF generation
   - Settings are automatically saved and persist across browser restarts
4. Use the popup interface to generate or preview the PDF
5. The PDF(s) will be automatically downloaded to your default downloads folder

**Note:** The floating button only appears on pages within `https://eds.ijs.si/workflow/activity/`

## Settings

The extension allows you to customize arrival times and enable secondary work generation:

- **Arrival Time**: Base time when you arrive at work (format: HH:MM)
- **Scattering**: Random variation applied to arrival time (± minutes)
  - Example: Arrival Time = 09:00, Scattering = 10 → Arrival between 08:50-09:10

### Secondary Work (Tailgate) Settings:
- **Enable Secondary Work**: Toggle to generate a second PDF for additional employment
- **Work Name**: Custom name for the secondary work (appears in PDF title and filename)
- **Percentage of Employment**: Percentage of full-time work (100% = 8 hours per day)
- **Include Breaks**: Whether to calculate and include break times in secondary work PDF

When secondary work is enabled, the extension generates two PDFs:
1. **Primary PDF**: Uses your configured arrival time and scattering
2. **Secondary PDF**: Arrival time equals the departure time from the primary PDF, working hours calculated from the percentage setting

Settings are stored using Chrome's sync storage and will persist across browser sessions and device sync.

## PDF Output

The generated PDF(s) include:
- Employee name and period from the webpage
- Professional table with Slovenian headers:
  - **Datum** (Date)
  - **Čas prihoda** (Arrival Time) - calculated based on your configured arrival time ± scattering
  - **Čas odhoda** (Departure Time) - calculated based on arrival + working hours
  - **Skupaj število ur** (Total Hours)
  - **Odmor med delovnim časom** (Break Duration in minutes)
- Monthly total hours summary
- Special handling for business trips ("Službeno potovanje" instead of times)

When secondary work is enabled, two separate PDF files are generated with different filenames:
- Primary PDF: `Oktober_2025_YourName.pdf`
- Secondary PDF: `Oktober_2025_YourName_SecondaryWorkName.pdf`

## Calculation Logic

### Regular Work Days (001 type):
- Arrival time: Configured base time ± scattering minutes (randomly varied)
- Departure time: Arrival + total hours for that day
- Break time: 30 minutes × (total hours ÷ 8 hours)

### Business Trips (002 type):
- Shows "Službeno potovanje" instead of specific times
- No time calculations performed

### Secondary Work (when enabled):
- Arrival time: Equals the departure time from the primary PDF for each day
- Working hours: (Percentage ÷ 100) × 8 hours
- Departure time: Arrival + calculated working hours
- Break time: 30 minutes × (working hours ÷ 8 hours) if "Include Breaks" is enabled, otherwise 0
- Employee name: Same as primary PDF (original name and surname)
- Filename: Primary filename with work name appended (e.g., `Oktober_2025_Name_SecondaryWork.pdf`)

### Example:
- Primary Settings: Arrival Time = 08:30, Scattering = 15
- For 8 hours work: Arrival = 08:30 ± 15min, Break = 30min, Departure = Arrival + 8 hours
- Secondary Settings: Percentage = 50%, Include Breaks = true
- Secondary PDF: Arrival = Primary Departure, Working Hours = 4 hours, Break = 15min, Departure = Arrival + 4 hours

## Compatibility

- Works on Stroskovnik pages (EDS system)
- Compatible with Chrome and Chromium-based browsers
- Uses PDFMake library for reliable Unicode support
- Works offline once loaded

## Files Structure

```
chrome-extension/
├── manifest.json          # Extension configuration and permissions
├── popup.html            # Extension popup interface with settings
├── popup.js              # Popup logic and settings management
├── content.js            # Main functionality, PDF generation, and floating button
├── pdfmake.min.js        # PDF generation library with Unicode support
├── vfs_fonts.js          # Font definitions for PDFMake
├── styles.css            # Popup interface styling
├── INSTALL.md            # Installation instructions
└── README.md             # This file
```

## Development

To modify or extend the extension:

1. Edit the source files
2. Reload the extension in `chrome://extensions/`
3. Test on a Stroskovnik page

### Key Functions:
- `parsePageData()`: Extracts data from timesheet table
- `extractWorkingDays()`: Processes work hours by day and type
- `generatePDF()`: Creates and downloads the PDF(s) (reloads latest settings, generates secondary PDF if enabled)
- `calculateTimes()`: Computes arrival/departure times and breaks using user settings
- `createPDFMakeDocument()`: Creates PDF document from raw data
- `createPDFMakeDocumentFromCalculatedData()`: Creates PDF document from pre-calculated data (for secondary work)
- `loadSettings()`: Loads user preferences from Chrome storage
- `addFloatingButton()`: Creates floating button on valid pages

## Troubleshooting

**Floating button not appearing:**
- The button only appears on pages within `https://eds.ijs.si/workflow/activity/`
- Make sure you're on a valid Stroskovnik timesheet page
- Try refreshing the page if the button doesn't appear
- Use the extension popup as an alternative method

**No data detected:**
- Make sure the timesheet table has data
- Check that work entries have proper work types (001/002)

**Slovenian characters not displaying:**
- The extension uses PDFMake which has native Unicode support
- If characters still don't display, check that the webpage encoding is correct

**Times look wrong:**
- Arrival times vary according to your configured settings (default: ±10 minutes around 09:00 AM)
- Departure times are calculated as arrival + working hours
- Break times are calculated as 30 minutes × (hours ÷ 8)
- Check your settings in the extension popup if times don't match expectations

## License

MIT License - feel free to modify and distribute.