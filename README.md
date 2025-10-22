# AutoHours - Stroskovnik PDF Generator

[![Chrome Web Store](https://img.shields.io/badge/Chrome-Web%20Store-blue.svg)](https://chrome.google.com/webstore)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Chrome extension that automatically generates professional PDF timesheets from Stroskovnik (EDS) work tracking pages, with support for multiple employment scenarios.

## ✨ Features

- **Automatic PDF Generation**: Extracts work data from Stroskovnik timesheet pages and creates professional PDFs
- **Slovenian Language Support**: Full Unicode support for Slovenian characters (č, š, ž, Č, Š, Ž)
- **Flexible Time Calculations**: Configurable arrival times with scattering for realistic time entries
- **Secondary Work Support**: Generate PDFs for multiple employment scenarios (tailgate functionality)
- **Business Trip Handling**: Special formatting for business trip entries
- **Professional Output**: Clean, formatted PDF timesheets ready for submission

## 🚀 Quick Start

### Installation

1. **Download/Clone** this repository
2. **Open Chrome** and navigate to `chrome://extensions/`
3. **Enable Developer Mode** (toggle in top right)
4. **Click "Load unpacked"** and select the `chrome-extension` folder
5. **Navigate** to a Stroskovnik timesheet page and click the floating "📄 Generate PDF" button

### Basic Usage

1. Go to your Stroskovnik timesheet page (`https://eds.ijs.si/workflow/activity/`)
2. Click the blue floating button that appears
3. Configure your preferred arrival time and scattering in the extension popup
4. PDFs are automatically downloaded to your default downloads folder

## 📁 Project Structure

```
autoHours/
├── chrome-extension/          # Main extension files
│   ├── manifest.json         # Extension configuration
│   ├── popup.html           # Settings interface
│   ├── popup.js             # Popup functionality
│   ├── content.js           # Main PDF generation logic
│   ├── pdfmake.min.js       # PDF generation library
│   ├── vfs_fonts.js         # Font definitions
│   ├── styles.css           # Interface styling
│   └── README.md            # Detailed extension documentation
└── README.md                # This file
```

## 🔧 Advanced Features

### Secondary Work (Tailgate)
Generate PDFs for multiple employment scenarios:
- Set percentage of employment (e.g., 50% for part-time)
- Configure work name and break preferences
- Automatic time sequencing (secondary work starts after primary work ends)

### Settings
- **Arrival Time**: Base arrival time (HH:MM format)
- **Scattering**: Random variation in arrival times (± minutes)
- **Secondary Work**: Enable/disable additional work PDF generation

## 📖 Documentation

For detailed documentation including:
- Complete feature descriptions
- Configuration options
- Troubleshooting guide
- Technical implementation details

See [`chrome-extension/README.md`](chrome-extension/README.md)

## 🛠️ Development

### Prerequisites
- Chrome browser
- Access to Stroskovnik (EDS) system

### Setup
```bash
git clone https://github.com/vaskivskyiI/autoHours.git
cd autoHours
# Load chrome-extension folder as unpacked extension in Chrome
```

### Building
No build process required - the extension runs directly from source files.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This extension is designed for legitimate use with Stroskovnik time tracking systems. Users are responsible for ensuring compliance with their organization's policies and applicable regulations.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/vaskivskyiI/autoHours/issues)
- **Documentation**: See `chrome-extension/README.md` for detailed guides

---

**Made with ❤️ for efficient time tracking**</content>
<filePath>C:\Users\igorv\Desktop\repos\autoHours\README.md