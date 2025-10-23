// Stroskovnik PDF Generator - Production version

class StroskovnikPDFGenerator {
    constructor() {
        this.settings = {
            arrivalTime: '09:00',
            scatteringMinutes: 10
        };
        this.loadSettings();
        this.init();
    }

    init() {
        this.addFloatingButton();

        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            if (message.action === 'getPreview') {
                try {
                    const data = this.parsePageData();
                    sendResponse({ success: !!data, data });
                } catch (error) {
                    sendResponse({ success: false, error: error.message });
                }
            } else if (message.action === 'generatePDF') {
                this.generatePDF()
                    .then(() => {
                        sendResponse({ success: true });
                    })
                    .catch(error => {
                        sendResponse({ success: false, error: error.message });
                    });
                return true;
            }
        });
    }

    async loadSettings() {
        try {
            const result = await chrome.storage.sync.get({
                arrivalTime: '09:00',
                scatteringMinutes: 10,
                enableSecondary: false,
                secondaryName: '',
                secondaryPercent: 0,
                secondaryIncludeBreaks: true
            });
            
            // Ensure numeric values are properly parsed
            this.settings = {
                ...result,
                scatteringMinutes: parseInt(result.scatteringMinutes) || 10,
                secondaryPercent: parseFloat(result.secondaryPercent) || 0
            };
        } catch (error) {
            // Keep default settings
            this.settings = {
                arrivalTime: '09:00',
                scatteringMinutes: 10,
                enableSecondary: false,
                secondaryName: '',
                secondaryPercent: 0,
                secondaryIncludeBreaks: true
            };
        }
    }

    addFloatingButton() {
        const currentUrl = window.location.href;
        const isValidPage = currentUrl.startsWith('https://eds.ijs.si/workflow/activity/');

        if (!isValidPage) {
            return;
        }

        const existingBtn = document.getElementById('stroskovnik-pdf-btn');
        if (existingBtn) {
            existingBtn.remove();
        }

        const button = document.createElement('button');
        button.id = 'stroskovnik-pdf-btn';
        button.className = 'pdf-generator-btn';
        button.innerHTML = '📄 Generate PDF';
        button.title = 'Generate PDF timesheet';

        button.style.cssText = `
            position: fixed !important;
            top: 90px !important;
            right: 20px !important;
            z-index: 10000 !important;
            background: #1976d2 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            font-size: 14px !important;
            font-weight: bold !important;
            cursor: pointer !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
            transition: all 0.3s ease !important;
        `;

        button.addEventListener('click', async () => {
            await this.generatePDF();
        });

        document.body.appendChild(button);
    }

    parsePageData() {
        const selectors = [
            'h2.pagetitle .title',
            '.pagetitle .title',
            'h2 .title',
            '.title',
            'h1',
            'h2'
        ];

        let titleElement = null;
        let titleText = '';

        for (const selector of selectors) {
            titleElement = document.querySelector(selector);
            if (titleElement) {
                titleText = titleElement.textContent || '';
                break;
            }
        }

        if (!titleElement) {
            return null;
        }

        const cleanedTitle = this.cleanTitle(titleText);

        const table = document.getElementById('timeentrytable');
        if (!table) {
            return null;
        }

        const workingDays = this.extractWorkingDays(table);

        return {
            name: cleanedTitle.name,
            period: cleanedTitle.period,
            month: cleanedTitle.month,
            year: cleanedTitle.year,
            workingDays: workingDays.length,
            tableData: workingDays
        };
    }

    extractWorkingDays(table) {
        const workingDays = [];
        const headerCells = table.querySelectorAll('thead th');
        const dayColumns = [];

        headerCells.forEach((cell, index) => {
            const headerText = cell.textContent.trim();
            const headerHTML = cell.innerHTML;

            let dayMatch = headerText.match(/^(\d{1,2})\s*[\w\u00C0-\u017F]{3}$/);
            if (!dayMatch) {
                dayMatch = headerText.match(/^(\d{1,2})\s+[\w\u00C0-\u017F]{3}$/);
            }
            if (!dayMatch) {
                dayMatch = headerHTML.match(/^(\d{1,2})<br>[\w\u00C0-\u017F]{3}$/);
            }
            if (!dayMatch) {
                dayMatch = headerText.match(/^(\d{1,2}).{3}$/);
            }
            if (!dayMatch) {
                dayMatch = headerText.match(/^(\d{1,2})/);
                if (dayMatch && headerText.length > 6) dayMatch = null;
            }

            if (dayMatch) {
                const dayNumber = parseInt(dayMatch[1]);
                if (dayNumber >= 1 && dayNumber <= 31) {
                    dayColumns.push({ index, day: dayNumber });
                }
            }
        });

        const rows = table.querySelectorAll('tbody tr:not(:last-child)');

        dayColumns.forEach(({ index, day }) => {
            let dayTotal001 = 0;
            let dayTotal002 = 0;

            rows.forEach((row) => {
                let workTypeCell = row.querySelector('td:nth-child(5) span.ijsworktypecode');
                if (!workTypeCell) {
                    workTypeCell = row.querySelector('td:nth-child(5) span');
                }
                if (!workTypeCell) {
                    workTypeCell = row.querySelector('td:nth-child(5)');
                }

                const hourCell = row.querySelector(`td:nth-child(${index + 1}) input[type="text"]`);

                if (hourCell) {
                    const hourValue = hourCell.value || '0';
                    const hours = parseFloat(hourValue.replace(',', '.'));

                    let workType = '';
                    if (workTypeCell) {
                        workType = workTypeCell.textContent.trim();
                    }

                    if (!isNaN(hours) && hours > 0) {
                        if (workType === '001') {
                            dayTotal001 += hours;
                        } else if (workType === '002') {
                            dayTotal002 += hours;
                        }
                    }
                }
            });

            if (dayTotal001 > 0 || dayTotal002 > 0) {
                const hasBusinessTrip = dayTotal002 > 0;
                const dayData = {
                    day: day,
                    totalHours001: dayTotal001,
                    totalHours002: dayTotal002,
                    hasBusinessTrip: hasBusinessTrip,
                    type: hasBusinessTrip ? 'business-trip' : 'normal-work',
                    totalHours: dayTotal001 + dayTotal002
                };
                workingDays.push(dayData);
            }
        });

        return workingDays.sort((a, b) => a.day - b.day);
    }
    
    cleanTitle(rawTitle) {
        let workingText = rawTitle;

        workingText = workingText.replace(/^Stroškovnik:\s*/, '');

        workingText = workingText.replace(/[bB]WorkflowActivity.*$/, '');
        workingText = workingText.replace(/IJSTimeEntry.*$/, '');

        workingText = workingText.replace(/,\s*\d+\s*-\s*/, ' - ');

        const monthMatch = workingText.match(/(januar|februar|marec|april|maj|junij|julij|avgust|september|oktober|november|december)\s+(\d{4})/i);
        let month = 'oktober';
        let month_num = '10';
        let year = '2025';

        if (monthMatch) {
            month = monthMatch[1].toLowerCase();
            year = monthMatch[2];
            
            const months = {
                'januar': '01', 'februar': '02', 'marec': '03', 'april': '04',
                'maj': '05', 'junij': '06', 'julij': '07', 'avgust': '08',
                'september': '09', 'oktober': '10', 'november': '11', 'december': '12'
            };
            month_num = months[month] || '10';
        }

        const nameParts = workingText.split(' - ');
        let personName = nameParts.length > 1 ? nameParts[nameParts.length - 1].trim() : '';

        personName = personName.replace(/[bB]WorkflowActivity.*$/, '');
        personName = personName.replace(/IJSTimeEntry.*$/, '');
        personName = personName.trim();

        if (!personName && nameParts.length > 0) {
            personName = nameParts[0].replace(/\d{4}.*$/, '').trim();
        }

        return {
            name: personName,
            period: `${month} ${year}`,
            month: month,
            month_num: month_num,
            year: year
        };
    }

    async generatePDF() {
        try {
            // Reload settings before generating PDF to get latest values
            await this.loadSettings();

            const data = this.parsePageData();
            if (!data) {
                throw new Error('No timesheet data found');
            }

            if (!(await this.checkPDFMakeAvailability())) {
                throw new Error('PDFMake library not available');
            }

            // Calculate times for all days to get concrete arrival/departure times (used for both primary and secondary)
            const extracted = this.calculateTimesForAllDays(data);

            // First PDF using the calculated times
            const docDefinition1 = this.createPDFMakeDocumentFromCalculatedData(data, extracted);
            const filename1 = this.generateFilename(data);
            pdfMake.createPdf(docDefinition1).download(filename1);

            // If secondary work is enabled, create second PDF based on first PDF times
            if (this.settings.enableSecondary && this.settings.secondaryPercent > 0) {
                // Build second data copy and modify as per secondary settings
                const secondData = JSON.parse(JSON.stringify(data));
                secondData.name = data.name; // Keep the same name and surname as original

                // For each day, shift times: arrival = first.departure, compute new departure based on percent
                secondData.tableData = extracted.map(day => {
                    if (day.type === 'business-trip') {
                        return Object.assign({}, day, {
                            arrival: '-',
                            departure: '-',
                            totalHours: day.totalHours,
                            workHours: 0,
                            breakMinutes: 0,
                            type: 'business-trip'
                        });
                    }

                    // Parse departure time of first PDF to minutes
                    const depParts = day.departure.split(':').map(Number);
                    const departureMinutesFirst = depParts[0] * 60 + depParts[1];

                    // Arrival for second PDF equals departure of first
                    const arrivalMinutesSecond = departureMinutesFirst;

                    // Compute work minutes from percentage: percent / 100 * 8h
                    const percent = parseFloat(this.settings.secondaryPercent) || 0;
                    const workHoursSecond = isNaN(percent) || percent <= 0 ? 0 : (percent / 100) * 8;
                    const workMinutesSecond = Math.round(workHoursSecond * 60);

                    // Breaks: either included or skipped
                    let breakMinutesSecond = 0;
                    if (this.settings.secondaryIncludeBreaks) {
                        breakMinutesSecond = Math.round(30 * (workHoursSecond / 8));
                    }

                    const departureMinutesSecond = arrivalMinutesSecond + workMinutesSecond;

                    return {
                        day: day.day,
                        type: 'normal-work',
                        arrival: this.formatTime(arrivalMinutesSecond),
                        departure: this.formatTime(departureMinutesSecond),
                        totalHours: workHoursSecond || 0,
                        workHours: workHoursSecond || 0,
                        breakMinutes: breakMinutesSecond || 0
                    };
                });

                const docDefinition2 = this.createPDFMakeDocumentFromCalculatedData(secondData, secondData.tableData);
                // Generate filename based on original data but append work name
                const baseFilename = this.generateFilename(data);
                const workName = this.settings.secondaryName || 'Secondary';
                const cleanWorkName = workName.replace(/[^a-zA-Z0-9\s]/g, '').replace(/\s+/g, '_').trim();
                const filename2 = baseFilename.replace('.pdf', `_${cleanWorkName}.pdf`);
                pdfMake.createPdf(docDefinition2).download(filename2);
            }

            alert('PDF generated successfully! Check your downloads folder.');

        } catch (error) {
            alert('Error: ' + error.message);
            throw error;
        }
    }

    async checkPDFMakeAvailability() {
        if (typeof pdfMake !== 'undefined' && pdfMake.createPdf) {
            return true;
        }

        await new Promise(resolve => setTimeout(resolve, 500));
        return typeof pdfMake !== 'undefined' && pdfMake.createPdf;
    }

    createPDFMakeDocument(data) {
        const extractedData = this.calculateTimesForAllDays(data);

        const tableBody = [
            [
                { text: 'Datum', style: 'tableHeader' },
                { text: 'Čas prihoda', style: 'tableHeader' },
                { text: 'Čas odhoda', style: 'tableHeader' },
                { text: 'Skupaj število ur', style: 'tableHeader' },
                { text: 'Odmor med delovnim časom', style: 'tableHeader' }
            ]
        ];

        let totalWorkHours = 0;
        let totalBreakMinutes = 0;

        extractedData.forEach((dayData) => {
            if (dayData.type === 'business-trip') {
                tableBody.push([
                    this.formatDate(dayData.day, data.period),
                    '-',
                    '-',
                    { text: 'Službeno potovanje', italics: true },
                    '-'
                ]);
            } else {
                const totalHours = parseFloat(dayData.totalHours) || 0;
                const workHours = parseFloat(dayData.workHours) || 0;
                const breakMinutes = parseInt(dayData.breakMinutes) || 0;
                
                tableBody.push([
                    this.formatDate(dayData.day, data.period),
                    dayData.arrival,
                    dayData.departure,
                    totalHours.toFixed(1) + ' ur',
                    breakMinutes + ' min'
                ]);
                totalWorkHours += workHours;
                totalBreakMinutes += breakMinutes;
            }
        });

        tableBody.push([
            { text: 'Skupaj:', style: 'tableHeader' },
            '',
            '',
            { text: totalWorkHours.toFixed(1) + ' ur', style: 'tableHeader' },
            { text: totalBreakMinutes + ' min', style: 'tableHeader' }
        ]);

        return {
            content: [
                {
                    text: 'Pregled delovnega časa',
                    style: 'title',
                    alignment: 'center',
                    margin: [0, 0, 0, 10]
                },
                {
                    text: `${data.period} - ${data.name}`,
                    style: 'subtitle',
                    alignment: 'center',
                    margin: [0, 0, 0, 20]
                },
                {
                    table: {
                        headerRows: 1,
                        widths: ['auto', 'auto', 'auto', 'auto', 'auto'],
                        body: tableBody
                    },
                    layout: {
                        fillColor: function (rowIndex, node, columnIndex) {
                            return (rowIndex % 2 === 0) ? '#f5f5f5' : null;
                        },
                        hLineWidth: function (i, node) {
                            return (i === 0 || i === node.table.body.length) ? 2 : 1;
                        },
                        vLineWidth: function (i, node) {
                            return (i === 0 || i === node.table.widths.length) ? 2 : 1;
                        },
                        hLineColor: function (i, node) {
                            return (i === 0 || i === node.table.body.length) ? 'black' : 'gray';
                        },
                        vLineColor: function (i, node) {
                            return (i === 0 || i === node.table.widths.length) ? 'black' : 'gray';
                        }
                    }
                }
            ],
            styles: {
                title: {
                    fontSize: 16,
                    bold: true,
                    margin: [0, 0, 0, 10]
                },
                subtitle: {
                    fontSize: 12,
                    italics: true,
                    margin: [0, 0, 0, 20]
                },
                tableHeader: {
                    bold: true,
                    fontSize: 10,
                    color: 'black',
                    fillColor: '#e0e0e0'
                }
            },
            defaultStyle: {
                fontSize: 9
            },
            pageOrientation: 'portrait',
            pageSize: 'A4'
        };
    }

    createPDFMakeDocumentFromCalculatedData(data, extractedData) {
        const tableBody = [
            [
                { text: 'Datum', style: 'tableHeader' },
                { text: 'Čas prihoda', style: 'tableHeader' },
                { text: 'Čas odhoda', style: 'tableHeader' },
                { text: 'Skupaj število ur', style: 'tableHeader' },
                { text: 'Odmor med delovnim časom', style: 'tableHeader' }
            ]
        ];

        let totalWorkHours = 0;
        let totalBreakMinutes = 0;

        extractedData.forEach((dayData) => {
            if (dayData.type === 'business-trip') {
                tableBody.push([
                    this.formatDate(dayData.day, data.period),
                    '-',
                    '-',
                    { text: 'Službeno potovanje', italics: true },
                    '-'
                ]);
            } else {
                const totalHours = parseFloat(dayData.totalHours) || 0;
                const workHours = parseFloat(dayData.workHours) || 0;
                const breakMinutes = parseInt(dayData.breakMinutes) || 0;
                
                tableBody.push([
                    this.formatDate(dayData.day, data.period),
                    dayData.arrival,
                    dayData.departure,
                    totalHours.toFixed(1) + ' ur',
                    breakMinutes + ' min'
                ]);
                totalWorkHours += workHours;
                totalBreakMinutes += breakMinutes;
            }
        });

        tableBody.push([
            { text: 'Skupaj:', style: 'tableHeader' },
            '',
            '',
            { text: totalWorkHours.toFixed(1) + ' ur', style: 'tableHeader' },
            { text: totalBreakMinutes + ' min', style: 'tableHeader' }
        ]);

        return {
            content: [
                {
                    text: 'Pregled delovnega časa',
                    style: 'title',
                    alignment: 'center',
                    margin: [0, 0, 0, 10]
                },
                {
                    text: `${data.period} - ${data.name}`,
                    style: 'subtitle',
                    alignment: 'center',
                    margin: [0, 0, 0, 20]
                },
                {
                    table: {
                        headerRows: 1,
                        widths: ['auto', 'auto', 'auto', 'auto', 'auto'],
                        body: tableBody
                    },
                    layout: {
                        fillColor: function (rowIndex, node, columnIndex) {
                            return (rowIndex % 2 === 0) ? '#f5f5f5' : null;
                        },
                        hLineWidth: function (i, node) {
                            return (i === 0 || i === node.table.body.length) ? 2 : 1;
                        },
                        vLineWidth: function (i, node) {
                            return (i === 0 || i === node.table.widths.length) ? 2 : 1;
                        },
                        hLineColor: function (i, node) {
                            return (i === 0 || i === node.table.body.length) ? 'black' : 'gray';
                        },
                        vLineColor: function (i, node) {
                            return (i === 0 || i === node.table.widths.length) ? 'black' : 'gray';
                        }
                    }
                }
            ],
            styles: {
                title: {
                    fontSize: 16,
                    bold: true,
                    margin: [0, 0, 0, 10]
                },
                subtitle: {
                    fontSize: 12,
                    italics: true,
                    margin: [0, 0, 0, 20]
                },
                tableHeader: {
                    bold: true,
                    fontSize: 10,
                    color: 'black',
                    fillColor: '#e0e0e0'
                }
            },
            defaultStyle: {
                fontSize: 9
            },
            pageOrientation: 'portrait',
            pageSize: 'A4'
        };
    }

    
    calculateTimesForAllDays(data) {
        return data.tableData.map(dayData => {
            if (dayData.totalHours002 > 0 && dayData.totalHours001 === 0) {
                return {
                    day: dayData.day,
                    type: 'business-trip',
                    arrival: '-',
                    departure: '-',
                    totalHours: dayData.totalHours002,
                    workHours: 0,
                    breakMinutes: 0
                };
            } else if (dayData.totalHours001 > 0) {
                const times = this.calculateTimes(dayData.totalHours001);
                return {
                    day: dayData.day,
                    type: 'normal-work',
                    arrival: times.arrival,
                    departure: times.departure,
                    totalHours: dayData.totalHours001,
                    workHours: dayData.totalHours001,
                    breakMinutes: times.breakMinutes
                };
            } else {
                const times = this.calculateTimes(dayData.totalHours001);
                return {
                    day: dayData.day,
                    type: 'normal-work',
                    arrival: times.arrival,
                    departure: times.departure,
                    totalHours: dayData.totalHours001,
                    workHours: dayData.totalHours001,
                    breakMinutes: times.breakMinutes
                };
            }
        });
    }
    
    calculateTimes(totalHours) {
        const [hours, minutes] = this.settings.arrivalTime.split(':').map(Number);
        const baseMinutes = hours * 60 + minutes;

        const scattering = this.settings.scatteringMinutes;
        const variation = Math.floor(Math.random() * (scattering * 2 + 1)) - scattering;
        const arrivalMinutes = baseMinutes + variation;

        const breakMinutes = Math.round(30 * (totalHours / 8));

        const workMinutes = totalHours * 60;
        const departureMinutes = arrivalMinutes + workMinutes;

        return {
            arrival: this.formatTime(arrivalMinutes),
            departure: this.formatTime(departureMinutes),
            breakMinutes: breakMinutes
        };
    }
    
    formatTime(totalMinutes) {
        const hours = Math.floor(totalMinutes / 60);
        const minutes = totalMinutes % 60;
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    }
    
    formatDate(day, period) {
        // Extract month and year from period string
        // Assuming period format like "Stroškovnik: oktober 2025, 0226 - VASKIVSKYI IGOR"
        const monthMatch = period.match(/(januar|februar|marec|april|maj|junij|julij|avgust|september|oktober|november|december)/i);
        const yearMatch = period.match(/20\d{2}/);
        
        let month = '10'; // Default to October
        let year = '2025'; // Default year
        
        if (monthMatch) {
            const months = {
                'januar': '01', 'februar': '02', 'marec': '03', 'april': '04',
                'maj': '05', 'junij': '06', 'julij': '07', 'avgust': '08',
                'september': '09', 'oktober': '10', 'november': '11', 'december': '12'
            };
            month = months[monthMatch[1].toLowerCase()] || '10';
        }
        
        if (yearMatch) {
            year = yearMatch[0];
        }
        
        return `${day.toString().padStart(2, '0')}.${month}.${year}`;
    }
    
    generateFilename(data) {
        // Use month number for better sorting
        const monthNum = data.month_num || '10';
        const year = data.year || '2025';

        let cleanName = data.name
            .replace(/[^a-zA-Z\s]/g, '')
            .replace(/\s+/g, '_')
            .trim();

        if (!cleanName) {
            cleanName = 'Timesheet';
        }

        return `${monthNum}_${year}_${cleanName}.pdf`;
    }
}

// Initialize the extension
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new StroskovnikPDFGenerator();
    });
} else {
    new StroskovnikPDFGenerator();
}