import pandas as pd
import numpy as np
from textblob import TextBlob
from collections import Counter, defaultdict
import glob
import os
from datetime import datetime, timedelta
import re
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class EnhancedAllTrailsAnalyzer:
    def __init__(self):
        """Initialize the enhanced analyzer"""
        self.df = None
        self.stop_words = set(stopwords.words('english'))
        # Add app-specific stop words
        self.stop_words.update(['app', 'alltrails', 'trail', 'trails', 'hiking', 'hike', 'use', 'using', 'used'])
        
    def load_latest_reviews(self):
        """Load the most recent reviews CSV file"""
        csv_files = glob.glob('data/raw/alltrails_reviews_*.csv')
        if not csv_files:
            print("No review files found in data/raw/")
            return None
            
        latest_file = max(csv_files, key=os.path.getctime)
        print(f"Loading reviews from: {latest_file}")
        
        self.df = pd.read_csv(latest_file)
        
        # Perform basic sentiment analysis
        self.df['full_text'] = self.df['title'].fillna('') + ' ' + self.df['content'].fillna('')
        
        sentiments = []
        for text in self.df['full_text']:
            blob = TextBlob(str(text))
            sentiments.append(blob.sentiment.polarity)
        
        self.df['sentiment_polarity'] = sentiments
        
        def categorize_sentiment(polarity):
            if polarity > 0.1:
                return 'Positive'
            elif polarity < -0.1:
                return 'Negative'
            else:
                return 'Neutral'
        
        self.df['sentiment_category'] = self.df['sentiment_polarity'].apply(categorize_sentiment)
        self.df['rating_numeric'] = pd.to_numeric(self.df['rating'], errors='coerce')
        
        # Parse dates for version release timing analysis
        self.df['updated_parsed'] = pd.to_datetime(self.df['updated'], errors='coerce')
        
        print(f"Loaded {len(self.df)} reviews with enhanced features")
        return self.df
    
    
    def _preprocess_text(self, text):
        """Clean and preprocess text for analysis"""
        if pd.isna(text):
            return []
        
        # Convert to lowercase
        text = str(text).lower()
        
        # Remove punctuation and numbers
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        
        # Tokenize
        words = word_tokenize(text)
        
        # Remove stop words and short words
        words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        return words
    
    def analyze_word_frequency_by_sentiment(self):
        """Analyze most common words in positive vs negative reviews"""
        print("\n" + "="*60)
        print("WORD FREQUENCY ANALYSIS BY SENTIMENT")
        print("="*60)
        
        # Separate reviews by sentiment
        positive_reviews = self.df[self.df['sentiment_category'] == 'Positive']['full_text']
        negative_reviews = self.df[self.df['sentiment_category'] == 'Negative']['full_text']
        
        # Get word frequencies
        positive_words = []
        negative_words = []
        
        for text in positive_reviews:
            positive_words.extend(self._preprocess_text(text))
        
        for text in negative_reviews:
            negative_words.extend(self._preprocess_text(text))
        
        # Count frequencies
        positive_freq = Counter(positive_words)
        negative_freq = Counter(negative_words)
        
        print(f"\nTOP 15 WORDS IN POSITIVE REVIEWS ({len(positive_reviews)} reviews):")
        for word, count in positive_freq.most_common(15):
            print(f"   {word}: {count} times")
        
        print(f"\nTOP 15 WORDS IN NEGATIVE REVIEWS ({len(negative_reviews)} reviews):")
        for word, count in negative_freq.most_common(15):
            print(f"   {word}: {count} times")
        
        # Find words that appear significantly more in one sentiment vs another
        print(f"\nWORDS MORE COMMON IN NEGATIVE REVIEWS:")
        negative_distinctive = []
        for word, neg_count in negative_freq.most_common(20):
            pos_count = positive_freq.get(word, 0)
            if neg_count > 2 and (neg_count / (pos_count + 1)) > 2:  # At least 2x more common in negative
                negative_distinctive.append((word, neg_count, pos_count))
        
        for word, neg_count, pos_count in negative_distinctive[:10]:
            ratio = neg_count / (pos_count + 1)
            print(f"   {word}: {neg_count} negative vs {pos_count} positive (ratio: {ratio:.1f}x)")
        
        print(f"\nWORDS MORE COMMON IN POSITIVE REVIEWS:")
        positive_distinctive = []
        for word, pos_count in positive_freq.most_common(20):
            neg_count = negative_freq.get(word, 0)
            if pos_count > 5 and (pos_count / (neg_count + 1)) > 3:  # At least 3x more common in positive
                positive_distinctive.append((word, pos_count, neg_count))
        
        for word, pos_count, neg_count in positive_distinctive[:10]:
            ratio = pos_count / (neg_count + 1)
            print(f"   {word}: {pos_count} positive vs {neg_count} negative (ratio: {ratio:.1f}x)")
    
    def analyze_sentiment_by_version(self):
        """Analyze how sentiment varies by app version"""
        print("\n" + "="*60)
        print("SENTIMENT ANALYSIS BY APP VERSION")
        print("="*60)
        
        # Group by version
        version_analysis = self.df.groupby('version').agg({
            'sentiment_polarity': ['mean', 'count'],
            'rating_numeric': 'mean',
            'sentiment_category': lambda x: x.value_counts().to_dict()
        }).round(3)
        
        # Flatten column names
        version_analysis.columns = ['avg_sentiment', 'review_count', 'avg_rating', 'sentiment_dist']
        
        # Sort by review count (most reviewed versions first)
        version_analysis = version_analysis.sort_values('review_count', ascending=False)
        
        print(f"\nSENTIMENT BY VERSION (showing versions with 3+ reviews):")
        print(f"{'Version':<12} {'Reviews':<8} {'Avg Rating':<12} {'Avg Sentiment':<15} {'Pos%':<6} {'Neg%':<6}")
        print("-" * 70)
        
        for version, row in version_analysis.iterrows():
            if row['review_count'] >= 3:  # Only show versions with meaningful sample size
                sentiment_dist = row['sentiment_dist']
                total = row['review_count']
                pos_pct = (sentiment_dist.get('Positive', 0) / total) * 100
                neg_pct = (sentiment_dist.get('Negative', 0) / total) * 100
                
                print(f"{version:<12} {int(row['review_count']):<8} {row['avg_rating']:<12.2f} {row['avg_sentiment']:<15.3f} {pos_pct:<6.1f} {neg_pct:<6.1f}")
        
        # Check for version-specific issues
        print(f"\nVERSION-SPECIFIC INSIGHTS:")
        
        # Find versions with unusually low sentiment
        low_sentiment_versions = version_analysis[
            (version_analysis['avg_sentiment'] < 0.2) & 
            (version_analysis['review_count'] >= 3)
        ]
        
        if len(low_sentiment_versions) > 0:
            print(f"   Versions with lower sentiment:")
            for version, row in low_sentiment_versions.iterrows():
                print(f"     {version}: {row['avg_sentiment']:.3f} sentiment, {int(row['review_count'])} reviews")
        
        # Find versions with high negative percentage
        for version, row in version_analysis.iterrows():
            if row['review_count'] >= 3:
                sentiment_dist = row['sentiment_dist']
                neg_pct = (sentiment_dist.get('Negative', 0) / row['review_count']) * 100
                if neg_pct > 20:  # More than 20% negative
                    print(f"     {version}: {neg_pct:.1f}% negative reviews")
    
    def analyze_complaint_categories(self):
        """Analyze different categories of complaints in negative reviews"""
        print("\n" + "="*60)
        print("COMPLAINT CATEGORY ANALYSIS")
        print("="*60)
        
        # Focus on negative reviews
        negative_reviews = self.df[self.df['sentiment_category'] == 'Negative']
        
        if len(negative_reviews) == 0:
            print("No negative reviews found.")
            return
        
        print(f"\nANALYZING {len(negative_reviews)} NEGATIVE REVIEWS:")
        
        # Define complaint categories with keywords
        complaint_categories = {
            'Battery/Performance': ['battery', 'drain', 'power', 'slow', 'crash', 'freeze'],
            'Pricing/Billing': ['price', 'cost', 'expensive', 'billing', 'subscription', 'charge', 'money', 'year'],
            'Features/Functionality': ['feature', 'work', 'broken', 'bug', 'issue', 'problem', 'error'],
            'User Experience': ['interface', 'confusing', 'difficult', 'hard', 'complicated', 'usability']
        }
        
        # Count complaints by category
        category_counts = {}
        category_examples = {}
        
        for category, keywords in complaint_categories.items():
            count = 0
            examples = []
            
            for _, review in negative_reviews.iterrows():
                text = str(review['full_text']).lower()
                if any(keyword in text for keyword in keywords):
                    count += 1
                    if len(examples) < 2:  # Keep up to 2 examples
                        examples.append({
                            'title': review['title'][:50],
                            'rating': review['rating_numeric'],
                            'content': review['content'][:80]
                        })
            
            if count > 0:
                category_counts[category] = count
                category_examples[category] = examples
        
        # Display results
        print(f"\nCOMPLAINT CATEGORIES:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(negative_reviews)) * 100
            print(f"   {category}: {count} reviews ({percentage:.1f}%)")
            
            # Show examples
            if category in category_examples:
                for i, example in enumerate(category_examples[category][:1], 1):
                    print(f"     Example: \"{example['title']}...\" ({example['rating']}/5)")
                    print(f"              \"{example['content']}...\"")
            print()
    
    def generate_comprehensive_report(self):
        """Generate a comprehensive analysis report"""
        if self.df is None:
            print("No data loaded. Please run load_latest_reviews() first.")
            return
        
        print("COMPREHENSIVE ALLTRAILS REVIEW ANALYSIS")
        print("="*80)
        
        # Run all analyses
        self.analyze_word_frequency_by_sentiment()
        self.analyze_sentiment_by_version()
        self.analyze_complaint_categories()
        
        # Save detailed results
        os.makedirs('results', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save enhanced dataset
        enhanced_file = f"results/enhanced_analysis_{timestamp}.csv"
        self.df.to_csv(enhanced_file, index=False)
        print(f"\nEnhanced dataset saved to: {enhanced_file}")

def main():
    """Main function to run the enhanced analysis"""
    print("Starting Enhanced AllTrails Analysis...")
    
    analyzer = EnhancedAllTrailsAnalyzer()
    
    if analyzer.load_latest_reviews() is not None:
        analyzer.generate_comprehensive_report()
    else:
        print("No review data found. Please run apple_reviews.py first.")

if __name__ == "__main__":
    main()