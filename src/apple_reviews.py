import requests
import json
import pandas as pd
import time
from datetime import datetime
import os

class AppleReviewScraper:
    def __init__(self, country='us'):
        """
        Initialize the Apple Review Scraper for AllTrails
        
        Args:
            country (str): App Store country code (e.g., 'us', 'gb', 'ca')
        """
        self.country = country
        self.base_url = f"https://itunes.apple.com/{country}/rss/customerreviews"
        
    def get_reviews_page(self, app_id, page_no=1):
        """
        Get reviews for a specific page
        
        Args:
            app_id (str): Apple App Store app ID
            page_no (int): Page number to retrieve
            
        Returns:
            dict: JSON response from API
        """
        url = f"{self.base_url}/page={page_no}/id={app_id}/sortBy=mostRecent/json"
        
        print(f"  -> Fetching page {page_no}...")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"    Error fetching page {page_no}: {e}")
            return None
    
    def extract_review_from_entry(self, review_entry):
        """
        Extract review data from a single API entry
        
        Args:
            review_entry (dict): Single review from API response
            
        Returns:
            dict: Clean review data
        """
        try:
            # Extract basic info with safe navigation
            review_data = {
                'review_id': review_entry.get('id', {}).get('label', ''),
                'title': review_entry.get('title', {}).get('label', ''),
                'content': review_entry.get('content', {}).get('label', ''),
                'rating': review_entry.get('im:rating', {}).get('label', ''),
                'version': review_entry.get('im:version', {}).get('label', ''),
                'author': review_entry.get('author', {}).get('name', {}).get('label', ''),
                'updated': review_entry.get('updated', {}).get('label', ''),
                'vote_sum': review_entry.get('im:voteSum', {}).get('label', ''),
                'vote_count': review_entry.get('im:voteCount', {}).get('label', '')
            }
            
            return review_data
            
        except Exception as e:
            print(f"    Warning: Error extracting review: {e}")
            return None
    
    def scrape_alltrails_reviews(self, pages=5):
        """
        Scrape AllTrails reviews specifically
        
        Args:
            pages (int): Number of pages to scrape (max 10)
            
        Returns:
            list: List of review dictionaries
        """
        ALLTRAILS_APP_ID = "405075943"  # AllTrails app ID
        
        print(f"Scraping AllTrails reviews from Apple App Store...")
        print(f"   App ID: {ALLTRAILS_APP_ID}")
        print(f"   Country: {self.country}")
        print(f"   Pages: {min(pages, 10)}")
        print()
        
        all_reviews = []
        
        for page in range(1, min(pages + 1, 11)):  # Max 10 pages per Apple's limit
            data = self.get_reviews_page(ALLTRAILS_APP_ID, page)
            
            if data is None:
                continue
                
            try:
                # Navigate the nested JSON structure
                feed = data.get('feed', {})
                entries = feed.get('entry', [])
                
                if not entries:
                    print(f"    No reviews found on page {page}")
                    continue
                
                # Skip the first entry (it's app info, not a review)
                review_entries = entries[1:] if len(entries) > 1 else []
                
                page_reviews = 0
                for entry in review_entries:
                    review = self.extract_review_from_entry(entry)
                    if review and review['content']:  # Only keep reviews with content
                        all_reviews.append(review)
                        page_reviews += 1
                
                print(f"    Found {page_reviews} reviews on page {page}")
                        
            except Exception as e:
                print(f"    Error processing page {page}: {e}")
                continue
            
            # Be respectful to Apple's servers
            time.sleep(1)
        
        print(f"\nTotal reviews collected: {len(all_reviews)}")
        return all_reviews
    
    def save_reviews_to_csv(self, reviews, filename=None):
        """
        Save reviews to CSV file
        
        Args:
            reviews (list): List of review dictionaries
            filename (str): Output filename (optional)
            
        Returns:
            pandas.DataFrame: Reviews as DataFrame
        """
        if not reviews:
            print("No reviews to save")
            return None
        
        # Create DataFrame
        df = pd.DataFrame(reviews)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"alltrails_reviews_{timestamp}.csv"
        
        # Ensure data directory exists
        os.makedirs('data/raw', exist_ok=True)
        
        # Save to CSV
        filepath = f"data/raw/{filename}"
        df.to_csv(filepath, index=False)
        
        print(f"Saved {len(reviews)} reviews to: {filepath}")
        
        # Show a preview
        print(f"\nSample of collected data:")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Sample review:")
        if len(df) > 0:
            sample = df.iloc[0]
            print(f"     Title: {sample['title'][:50]}...")
            print(f"     Rating: {sample['rating']}/5")
            print(f"     Content: {sample['content'][:100]}...")
        
        return df

# Main function for testing
def test_scraper():
    """Test the scraper with a small number of pages"""
    print("Testing AllTrails Review Scraper...")
    print("=" * 50)
    
    # Create scraper
    scraper = AppleReviewScraper(country='us')
    
    # Scrape 2 pages for testing
    reviews = scraper.scrape_alltrails_reviews(pages=2)
    
    if reviews:
        # Save to CSV
        df = scraper.save_reviews_to_csv(reviews)
        return df
    else:
        print("No reviews collected during test")
        return None

if __name__ == "__main__":
    test_scraper()