# 📚 Past Paper Vault - Streamlit Application

A modern, searchable vault for past examination papers with Telegram integration for file downloads.

## Features

- 🔍 **Fuzzy Search**: Find papers using RapidFuzz for intelligent matching
- 📱 **Mobile Responsive**: Clean UI that works on all devices
- 🔗 **URL Integration**: Search via URL query parameters (`?q=physics+2025`)
- 📥 **Telegram Integration**: Direct download links from Telegram Bot API
- ⚡ **Performance Optimized**: Cached data loading for fast searches

## Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (get one from [@BotFather](https://t.me/BotFather))

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure `master_index.csv` is in the project root**
   - The CSV should have columns: `File Name` and `File ID`
   - `File ID` should contain Telegram file IDs

## Configuration

### Local Development

Create a `.streamlit/secrets.toml` file in your project root:

```toml
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"
```

**Note**: Never commit this file to version control! Add `.streamlit/` to your `.gitignore`.

### Streamlit Cloud Deployment

1. **Push your code to GitHub**

2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Set the main file path to `app.py`

3. **Configure Secrets**:
   - In your Streamlit Cloud app settings, go to "Secrets"
   - Add your Telegram Bot Token:
     ```toml
     TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"
     ```

## Running Locally

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

## Usage

1. **Search**: Enter keywords in the search bar (e.g., "physics 2021", "mathematics")
2. **View Results**: Top 5 matching papers will be displayed
3. **Generate Link**: Click "Generate Link" button to get a direct download URL
4. **Download**: Click the download link to access the file

### URL Search

You can also search via URL query parameters:
```
http://localhost:8501/?q=physics+2025
```

## File Structure

```
ExamLankaVaultApp/
├── app.py                 # Main Streamlit application
├── master_index.csv       # Index file with File Name and File ID
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── .streamlit/
    └── secrets.toml      # Local secrets (not in git)
```

## Security Notes

- ✅ Bot tokens are stored in Streamlit secrets (never hardcoded)
- ✅ Error handling for invalid tokens and network issues
- ✅ Secure file access through Telegram Bot API

## Troubleshooting

### "Telegram Bot Token not configured"
- Ensure you've created `.streamlit/secrets.toml` locally
- Or configured secrets in Streamlit Cloud

### "Telegram Error" when generating links
- Verify your bot token is correct
- Ensure the file IDs in `master_index.csv` are valid
- Check that your bot has access to the files

### "master_index.csv file not found"
- Ensure the CSV file is in the same directory as `app.py`
- Check the file name matches exactly (case-sensitive)

## License

This project is provided as-is for educational purposes.

