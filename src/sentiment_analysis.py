import pandas as pd
import numpy as np
from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import glob
import os
from datetime import datetime
import re

class AllTrailsSentimentAnalyzer:
    def __init__(self):
        """Initialize the sentiment analyzer"""
        self.df = None
        self.sentiment_results = None
        
    def load_latest_reviews(self):
        """Load the most recent reviews CSV file"""
        # Find the most recent CSV file
        csv_files = glob.glob('data/raw/alltrails_reviews_*.csv')
        if not csv_files:
            print("No review files found in data/raw/")
            return None
            
        # Get the most recent file
        latest_file = max(csv_files, key=os.path.getctime)
        print(f"Loading reviews from: {latest_file}")
        
        # Load the data
        self.df = pd.read_csv(latest_file)
        print(f"Loaded {len(self.df)} reviews")
        
        return self.df
    
    def analyze_sentiment(self):
        """Perform sentiment analysis on the reviews"""
        if self.df is None:
            print("No data loaded. Call load_latest_reviews() first.")
            return None
            
        print("Analyzing sentiment...")
        
        # Combine title and content for analysis
        self.df['full_text'] = self.df['title'].fillna('') + ' ' + self.df['content'].fillna('')
        
        # Calculate sentiment scores
        sentiments = []
        for text in self.df['full_text']:
            blob = TextBlob(str(text))
            sentiments.append({
                'polarity': blob.sentiment.polarity,  # -1 (negative) to 1 (positive)
                'subjectivity': blob.sentiment.subjectivity  # 0 (objective) to 1 (subjective)
            })
        
        # Add sentiment data to dataframe
        self.df['sentiment_polarity'] = [s['polarity'] for s in sentiments]
        self.df['sentiment_subjectivity'] = [s['subjectivity'] for s in sentiments]
        
        # Categorize sentiment
        def categorize_sentiment(polarity):
            if polarity > 0.1:
                return 'Positive'
            elif polarity < -0.1:
                return 'Negative'
            else:
                return 'Neutral'
        
        self.df['sentiment_category'] = self.df['sentiment_polarity'].apply(categorize_sentiment)
        
        # Convert rating to numeric
        self.df['rating_numeric'] = pd.to_numeric(self.df['rating'], errors='coerce')
        
        print("Sentiment analysis complete!")
        return self.df
    
    def generate_summary_stats(self):
        """Generate summary statistics"""
        if self.df is None:
            return None
            
        stats = {
            'total_reviews': len(self.df),
            'avg_rating': self.df['rating_numeric'].mean(),
            'avg_sentiment_polarity': self.df['sentiment_polarity'].mean(),
            'sentiment_distribution': self.df['sentiment_category'].value_counts().to_dict(),
            'rating_distribution': self.df['rating_numeric'].value_counts().sort_index().to_dict()
        }
        
        return stats
    
    def print_analysis_results(self):
        """Print detailed analysis results"""
        if self.df is None:
            print("No data to analyze")
            return
            
        stats = self.generate_summary_stats()
        
        print("\n" + "="*60)
        print("ALLTRAILS SENTIMENT ANALYSIS RESULTS")
        print("="*60)
        
        print(f"\nOVERVIEW:")
        print(f"   Total Reviews: {stats['total_reviews']}")
        print(f"   Average Rating: {stats['avg_rating']:.2f}/5.0")
        print(f"   Average Sentiment: {stats['avg_sentiment_polarity']:.3f} (-1=negative, +1=positive)")
        
        print(f"\nSENTIMENT DISTRIBUTION:")
        for sentiment, count in stats['sentiment_distribution'].items():
            percentage = (count / stats['total_reviews']) * 100
            print(f"   {sentiment}: {count} reviews ({percentage:.1f}%)")
        
        print(f"\nRATING DISTRIBUTION:")
        for rating, count in stats['rating_distribution'].items():
            if not pd.isna(rating):
                percentage = (count / stats['total_reviews']) * 100
                stars = "*" * int(rating)
                print(f"   {stars} ({rating}): {count} reviews ({percentage:.1f}%)")
        
        # Show examples of each sentiment category
        print(f"\nSAMPLE REVIEWS:")
        
        for sentiment in ['Positive', 'Neutral', 'Negative']:
            sample_reviews = self.df[self.df['sentiment_category'] == sentiment].head(2)
            if len(sample_reviews) > 0:
                print(f"\n   {sentiment.upper()} EXAMPLES:")
                for idx, review in sample_reviews.iterrows():
                    print(f"   • Rating: {review['rating_numeric']}/5")
                    print(f"     Title: {review['title'][:60]}...")
                    print(f"     Sentiment Score: {review['sentiment_polarity']:.3f}")
                    print(f"     Content: {review['content'][:100]}...")
                    print()
        
        # Correlation analysis
        correlation = self.df['rating_numeric'].corr(self.df['sentiment_polarity'])
        print(f"RATING vs SENTIMENT CORRELATION: {correlation:.3f}")
        print("   (1.0 = perfect positive correlation, -1.0 = perfect negative correlation)")
        
    def save_results(self):
        """Save the analysis results"""
        if self.df is None:
            return
            
        # Create results directory
        os.makedirs('results', exist_ok=True)
        
        # Save enhanced dataset
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"results/sentiment_analysis_{timestamp}.csv"
        self.df.to_csv(output_file, index=False)
        
        print(f"\nResults saved to: {output_file}")
        
        # Save summary statistics
        stats = self.generate_summary_stats()
        summary_file = f"results/sentiment_summary_{timestamp}.txt"
        
        with open(summary_file, 'w') as f:
            f.write("ALLTRAILS SENTIMENT ANALYSIS SUMMARY\n")
            f.write("="*50 + "\n\n")
            f.write(f"Total Reviews: {stats['total_reviews']}\n")
            f.write(f"Average Rating: {stats['avg_rating']:.2f}/5.0\n")
            f.write(f"Average Sentiment: {stats['avg_sentiment_polarity']:.3f}\n\n")
            f.write("Sentiment Distribution:\n")
            for sentiment, count in stats['sentiment_distribution'].items():
                percentage = (count / stats['total_reviews']) * 100
                f.write(f"  {sentiment}: {count} ({percentage:.1f}%)\n")
            f.write("\nRating Distribution:\n")
            for rating, count in stats['rating_distribution'].items():
                if not pd.isna(rating):
                    percentage = (count / stats['total_reviews']) * 100
                    f.write(f"  {rating} stars: {count} ({percentage:.1f}%)\n")
        
        print(f"Summary saved to: {summary_file}")

def main():
    """Main function to run the sentiment analysis"""
    print("Starting AllTrails Sentiment Analysis...")
    
    # Initialize analyzer
    analyzer = AllTrailsSentimentAnalyzer()
    
    # Load and analyze data
    if analyzer.load_latest_reviews() is not None:
        analyzer.analyze_sentiment()
        analyzer.print_analysis_results()
        analyzer.save_results()
    else:
        print("No review data found. Please run apple_reviews.py first.")

if __name__ == "__main__":
    main()