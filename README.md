# IMDb Top 250 Movies Scraper v9

A Python web scraper that extracts the complete IMDb Top 250 movies list and saves it to a CSV file. Uses multiple scraping strategies to ensure maximum data retrieval without requiring Selenium or browser automation.

## 🎬 Features

- **Pure Python**: No Selenium or browser dependencies required
- **Multiple Scraping Methods**: Uses various approaches to maximize data extraction
- **Complete Dataset**: Aims to extract all 250 movies from IMDb's Top 250 list
- **CSV Export**: Clean, structured data export
- **Error Handling**: Robust error handling and retry logic
- **Respectful Scraping**: Includes delays and proper headers

## 📊 Extracted Data

The scraper extracts the following information for each movie:

- **Rank**: Position in Top 250 (1-250)
- **Title**: Movie title
- **Year**: Release year
- **Rating**: IMDb rating (out of 10)
- **URL**: IMDb movie page URL

## 🚀 Quick Start

### Prerequisites

- Python 3.6 or higher
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/imdb-top250-scraper.git
cd imdb-top250-scraper
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

### Usage

Run the scraper:
```bash
python imdb_scraper.py
```

Enter a filename when prompted (default: `imdb_top250_movies.csv`)

## 📁 Output

The script generates a CSV file with the following structure:

```csv
rank,title,year,rating,url
1,The Shawshank Redemption,1994,9.3,https://www.imdb.com/title/tt0111161/
2,The Godfather,1972,9.2,https://www.imdb.com/title/tt0068646/
...
```

## 🔧 How It Works

The scraper uses multiple strategies to maximize data extraction:

1. **Classic Interface**: Attempts to access IMDb's classic table structure
2. **JSON Extraction**: Looks for embedded JSON data in page scripts
3. **Alternative Endpoints**: Tries mobile and alternative IMDb URLs
4. **HTML Parsing**: Multiple CSS selectors for different page structures

## 📋 Requirements

- `requests` - HTTP library for making web requests
- `beautifulsoup4` - HTML parsing and extraction
- `pandas` - Data manipulation and CSV export

## ⚙️ Configuration

The scraper includes several configurable options in the code:

- **Request timeout**: 15 seconds default
- **Retry attempts**: 3 attempts with exponential backoff
- **Request delays**: 1-2 seconds between requests
- **User-Agent**: Modern Chrome browser simulation

## 🚨 Important Notes

- **Respectful Usage**: The scraper includes delays between requests to respect IMDb's servers
- **Rate Limiting**: Built-in rate limiting to avoid being blocked
- **No Selenium**: Pure HTTP requests - no browser automation required
- **Dynamic Structure**: IMDb frequently changes their page structure, so results may vary

## 🐛 Troubleshooting

### Common Issues

**"No movies found"**
- IMDb may have changed their page structure
- Try running the script multiple times
- Check your internet connection

**"Request failed"**
- IMDb may be blocking requests temporarily
- Wait a few minutes and try again
- Check if IMDb is accessible in your region

**"Module not found"**
- Install requirements: `pip install -r requirements.txt`
- Ensure you're using Python 3.6+

## 📈 Version History

- **v9.0**: Simplified scraper, removed Selenium dependency, improved reliability
- **v8.x**: Previous versions with various scraping approaches

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add improvement'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Create a Pull Request

## ⚖️ Legal Disclaimer

This scraper is for educational and personal use only. Please respect IMDb's terms of service and robots.txt file. The authors are not responsible for any misuse of this tool.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- IMDb for providing the movie data
- Python community for the excellent libraries used in this project

---

**⭐ If you find this project useful, please give it a star!**
