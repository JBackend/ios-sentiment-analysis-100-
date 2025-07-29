# iOS App Sentiment Analysis

Analyze user sentiment from Apple App Store reviews using natural language processing.

## Installation

```bash
git clone https://github.com/JBackend/ios-sentiment-analysis-100-.git
cd ios-sentiment-analysis-100-
pip install -r requirements.txt
```

## Usage

1. Find your target app's ID from its App Store URL:
   ```
   https://apps.apple.com/us/app/app-name/id123456789
   App ID: 123456789
   ```

2. Edit `src/apple_reviews.py` and change the App ID:
   ```python
   ALLTRAILS_APP_ID = "123456789"  # Replace with your app ID
   ```

3. Run the analysis:
   ```bash
   python src/apple_reviews.py        # Collect reviews
   python src/enhanced_analysis.py    # Analyze sentiment
   ```

## Output

The tool generates:
- CSV files with review data and sentiment scores
- Text summary with sentiment distribution
- Word frequency analysis for positive vs negative reviews
- App version comparison

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## License

MIT
