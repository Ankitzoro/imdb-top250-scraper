#!/usr/bin/env python3
"""
IMDb Top 250 Movies Scraper (Pure Web Scraping)

This script scrapes the IMDb Top 250 movies list using requests and BeautifulSoup only.
Uses multiple HTTP requests to get all 250 movies from IMDb's various endpoints.

Requirements:
- requests
- beautifulsoup4
- pandas

Install with: pip install requests beautifulsoup4 pandas
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin, parse_qs, urlparse
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IMDbTop250Scraper:
    def __init__(self):
        self.base_url = "https://www.imdb.com"
        self.session = requests.Session()
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(self.headers)
        
        # Store cookies from the main page
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session by visiting main IMDb page to get cookies"""
        try:
            response = self.session.get("https://www.imdb.com", timeout=10)
            logger.info("Session initialized with IMDb cookies")
        except Exception as e:
            logger.warning(f"Failed to initialize session: {e}")
    
    def get_page_with_retries(self, url, retries=3):
        """Get page content with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        return None
    
    def try_classic_imdb_page(self):
        """Try the classic IMDb interface which might show all movies"""
        try:
            # Try classic/old IMDb interface
            classic_urls = [
                "https://www.imdb.com/chart/top/?view=simple",
                "https://www.imdb.com/chart/top/?sort=ir,desc&mode=simple&page=1",
                "https://www.imdb.com/chart/top"
            ]
            
            for url in classic_urls:
                logger.info(f"Trying classic interface: {url}")
                response = self.get_page_with_retries(url)
                
                if response:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    movies = self.extract_from_classic_page(soup)
                    
                    if len(movies) > 50:  # If we got a good number of movies
                        logger.info(f"Classic interface successful: {len(movies)} movies")
                        return movies
                
                time.sleep(1)
            
            return []
            
        except Exception as e:
            logger.error(f"Classic page method failed: {e}")
            return []
    
    def extract_from_classic_page(self, soup):
        """Extract movies from classic IMDb page structure"""
        movies = []
        
        try:
            # Look for the classic table structure
            tbody = soup.find('tbody', class_='lister-list')
            if tbody:
                rows = tbody.find_all('tr')
                logger.info(f"Found {len(rows)} rows in classic table")
                
                for row in rows:
                    movie_data = self.extract_from_classic_row(row)
                    if movie_data:
                        movies.append(movie_data)
            
            # Alternative: Look for movie containers in modern structure
            if not movies:
                containers = soup.find_all('li', class_='ipc-metadata-list-summary-item')
                logger.info(f"Found {len(containers)} containers in modern structure")
                
                for i, container in enumerate(containers, 1):
                    movie_data = self.extract_from_container(container, i)
                    if movie_data:
                        movies.append(movie_data)
            
            # Alternative: Look for any table rows
            if not movies:
                all_rows = soup.find_all('tr')
                logger.info(f"Found {len(all_rows)} total rows")
                
                for i, row in enumerate(all_rows):
                    if self.is_movie_row(row):
                        movie_data = self.extract_from_any_row(row, len(movies) + 1)
                        if movie_data:
                            movies.append(movie_data)
            
            return movies
            
        except Exception as e:
            logger.error(f"Error extracting from classic page: {e}")
            return []
    
    def extract_from_classic_row(self, row):
        """Extract movie data from classic table row"""
        try:
            # Rank
            rank_cell = row.find('td', class_='ratingColumn')
            rank = None
            if rank_cell:
                rank_text = rank_cell.get_text(strip=True)
                rank_match = re.search(r'(\d+)', rank_text)
                if rank_match:
                    rank = int(rank_match.group(1))
            
            # Title and Year
            title_cell = row.find('td', class_='titleColumn')
            if not title_cell:
                return None
            
            title_link = title_cell.find('a')
            title = title_link.get_text(strip=True) if title_link else "Unknown"
            
            # Year
            year = None
            year_span = title_cell.find('span', class_='secondaryInfo')
            if year_span:
                year_text = year_span.get_text(strip=True)
                year_match = re.search(r'(\d{4})', year_text)
                if year_match:
                    year = int(year_match.group(1))
            
            # Rating
            rating = None
            rating_cell = row.find('td', class_='ratingColumn')
            if rating_cell:
                strong = rating_cell.find('strong')
                if strong:
                    try:
                        rating = float(strong.get_text(strip=True))
                    except ValueError:
                        pass
            
            # URL
            movie_url = None
            if title_link and title_link.get('href'):
                movie_url = urljoin(self.base_url, title_link['href'])
            
            # If no rank found, try to extract from the row position
            if not rank:
                # Look for numbering in the title or nearby elements
                numbering = row.find('td', class_='numberColumn')
                if numbering:
                    rank_text = numbering.get_text(strip=True)
                    rank_match = re.search(r'(\d+)', rank_text)
                    if rank_match:
                        rank = int(rank_match.group(1))
            
            return {
                'rank': rank,
                'title': title,
                'year': year,
                'rating': rating,
                'url': movie_url
            }
            
        except Exception as e:
            logger.error(f"Error extracting from classic row: {e}")
            return None
    
    def extract_from_container(self, container, rank):
        """Extract movie data from modern container structure"""
        try:
            # Title
            title_elem = container.find('h3', class_='ipc-title__text')
            title = "Unknown"
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # Remove rank number if present (e.g., "1. Movie Title" -> "Movie Title")
                title_match = re.match(r'^\d+\.\s*(.*)', title_text)
                title = title_match.group(1) if title_match else title_text
            
            # Year
            year = None
            year_elem = container.find('span', class_='cli-title-metadata-item')
            if year_elem:
                year_text = year_elem.get_text(strip=True)
                year_match = re.search(r'(\d{4})', year_text)
                if year_match:
                    year = int(year_match.group(1))
            
            # Rating
            rating = None
            rating_elem = container.find('span', class_='ipc-rating-star--rating')
            if rating_elem:
                try:
                    rating = float(rating_elem.get_text(strip=True))
                except ValueError:
                    pass
            
            # URL
            movie_url = None
            link_elem = container.find('a', class_='ipc-title-link-wrapper')
            if link_elem and link_elem.get('href'):
                movie_url = urljoin(self.base_url, link_elem['href'])
            
            return {
                'rank': rank,
                'title': title,
                'year': year,
                'rating': rating,
                'url': movie_url
            }
            
        except Exception as e:
            logger.error(f"Error extracting from container: {e}")
            return None
    
    def is_movie_row(self, row):
        """Check if a table row contains movie data"""
        # Look for indicators that this is a movie row
        has_title_link = row.find('a', href=re.compile(r'/title/tt\d+/'))
        has_rating = row.find('strong') or row.find('span', class_='ipc-rating-star--rating')
        has_year = bool(re.search(r'\(\d{4}\)', row.get_text()))
        
        return bool(has_title_link and (has_rating or has_year))
    
    def extract_from_any_row(self, row, rank):
        """Extract movie data from any table row that contains movie info"""
        try:
            # Find title link
            title_link = row.find('a', href=re.compile(r'/title/tt\d+/'))
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            
            # Extract year
            year = None
            row_text = row.get_text()
            year_match = re.search(r'\((\d{4})\)', row_text)
            if year_match:
                year = int(year_match.group(1))
            
            # Extract rating
            rating = None
            rating_elem = row.find('strong') or row.find('span', class_='ipc-rating-star--rating')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    rating = float(rating_text)
                except ValueError:
                    pass
            
            # URL
            movie_url = urljoin(self.base_url, title_link['href']) if title_link.get('href') else None
            
            return {
                'rank': rank,
                'title': title,
                'year': year,
                'rating': rating,
                'url': movie_url
            }
            
        except Exception as e:
            logger.error(f"Error extracting from any row: {e}")
            return None
    
    def try_paginated_requests(self):
        """Try to get movies through paginated requests"""
        movies = []
        
        try:
            # Some sites use pagination parameters
            base_params = [
                {'start': 1, 'count': 250},
                {'page': 1, 'per_page': 250},
                {'offset': 0, 'limit': 250}
            ]
            
            for params in base_params:
                url = "https://www.imdb.com/chart/top/"
                response = self.session.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_movies = self.extract_from_classic_page(soup)
                    
                    if len(page_movies) > len(movies):
                        movies = page_movies
                        logger.info(f"Paginated request successful: {len(movies)} movies")
                
                time.sleep(1)
            
            return movies
            
        except Exception as e:
            logger.error(f"Paginated requests failed: {e}")
            return []
    
    def try_mobile_and_alternative_endpoints(self):
        """Try mobile version and other alternative endpoints"""
        movies = []
        
        try:
            # Try different IMDb endpoints
            endpoints = [
                "https://m.imdb.com/chart/top/",
                "https://www.imdb.com/chart/top/?ref_=nv_mv_250_6",
                "https://www.imdb.com/chart/top/?view=simple",
                "https://www.imdb.com/search/title/?groups=top_250&sort=user_rating,desc"
            ]
            
            for url in endpoints:
                logger.info(f"Trying endpoint: {url}")
                
                # Use mobile headers for mobile URLs
                if 'm.imdb.com' in url:
                    mobile_headers = self.headers.copy()
                    mobile_headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15'
                    response = self.session.get(url, headers=mobile_headers, timeout=15)
                else:
                    response = self.get_page_with_retries(url)
                
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try to extract movies from this page
                    endpoint_movies = self.extract_movies_from_any_page(soup)
                    
                    if len(endpoint_movies) > len(movies):
                        movies = endpoint_movies
                        logger.info(f"Endpoint {url} successful: {len(movies)} movies")
                
                time.sleep(2)  # Be respectful between requests
            
            return movies
            
        except Exception as e:
            logger.error(f"Alternative endpoints failed: {e}")
            return []
    
    def extract_movies_from_any_page(self, soup):
        """Extract movies from any IMDb page structure"""
        movies = []
        
        try:
            # Method 1: Look for JSON-LD structured data
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'itemListElement' in data:
                        for item in data['itemListElement']:
                            if 'item' in item:
                                movie_info = item['item']
                                movie_data = {
                                    'rank': item.get('position', len(movies) + 1),
                                    'title': movie_info.get('name', 'Unknown'),
                                    'year': None,
                                    'rating': movie_info.get('aggregateRating', {}).get('ratingValue'),
                                    'url': movie_info.get('url')
                                }
                                
                                # Extract year from date
                                if 'datePublished' in movie_info:
                                    year_match = re.search(r'(\d{4})', movie_info['datePublished'])
                                    if year_match:
                                        movie_data['year'] = int(year_match.group(1))
                                
                                movies.append(movie_data)
                                
                    if len(movies) >= 100:
                        logger.info(f"JSON-LD extraction successful: {len(movies)} movies")
                        return movies
                        
                except json.JSONDecodeError:
                    continue
            
            # Method 2: Look for embedded JSON in script tags
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and ('titleText' in script.string or 'movies' in script.string.lower()):
                    json_movies = self.extract_from_embedded_json(script.string)
                    if len(json_movies) > len(movies):
                        movies = json_movies
            
            # Method 3: Parse HTML structure
            if len(movies) < 100:
                html_movies = self.parse_html_for_movies(soup)
                if len(html_movies) > len(movies):
                    movies = html_movies
            
            return movies
            
        except Exception as e:
            logger.error(f"Error extracting movies from page: {e}")
            return []
    
    def extract_from_embedded_json(self, script_content):
        """Extract movie data from embedded JSON in script tags"""
        movies = []
        
        try:
            # Look for common JSON patterns that contain movie data
            patterns = [
                r'"titleText"\s*:\s*"([^"]+)"',
                r'"primaryText"\s*:\s*"([^"]+)"',
                r'"title"\s*:\s*"([^"]+)"'
            ]
            
            for pattern in patterns:
                titles = re.findall(pattern, script_content)
                if len(titles) > 50:  # If we found many titles, this might be our data
                    logger.info(f"Found {len(titles)} titles in embedded JSON")
                    
                    # Also look for years and ratings
                    years = re.findall(r'"releaseYear"\s*:\s*(\d{4})', script_content)
                    ratings = re.findall(r'"ratingValue"\s*:\s*(\d+\.?\d*)', script_content)
                    
                    for i, title in enumerate(titles[:250]):
                        year = int(years[i]) if i < len(years) else None
                        rating = float(ratings[i]) if i < len(ratings) else None
                        
                        movies.append({
                            'rank': i + 1,
                            'title': title,
                            'year': year,
                            'rating': rating,
                            'url': None
                        })
                    
                    if movies:
                        return movies
            
            return movies
            
        except Exception as e:
            logger.error(f"Error extracting from embedded JSON: {e}")
            return []
    
    def parse_html_for_movies(self, soup):
        """Parse HTML structure looking for movie data"""
        movies = []
        
        try:
            # Try multiple selectors to find movie elements
            selectors = [
                'li.ipc-metadata-list-summary-item',
                'tr[data-testid]',
                'li.titleColumn',
                '.lister-item',
                '.cli-item'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for i, element in enumerate(elements, 1):
                        movie_data = self.extract_movie_data_generic(element, i)
                        if movie_data and movie_data['title'] != "Unknown":
                            movies.append(movie_data)
                    
                    if len(movies) > 50:  # If we got a good number, use this selector
                        break
            
            return movies
            
        except Exception as e:
            logger.error(f"Error parsing HTML for movies: {e}")
            return []
    
    def extract_movie_data_generic(self, element, rank):
        """Generic movie data extraction that works with multiple HTML structures"""
        try:
            # Title - try multiple approaches
            title = "Unknown"
            title_selectors = [
                'h3.ipc-title__text',
                'a.titleColumn',
                'td.titleColumn a',
                'a[href*="/title/tt"]',
                '.cli-title a'
            ]
            
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    # Clean up title
                    title_clean = re.sub(r'^\d+\.\s*', '', title_text)  # Remove rank prefix
                    if title_clean and len(title_clean) > 1:
                        title = title_clean
                        break
            
            # Year - try multiple approaches
            year = None
            year_selectors = [
                '.cli-title-metadata-item',
                '.secondaryInfo',
                'span.secondaryInfo'
            ]
            
            for selector in year_selectors:
                year_elem = element.select_one(selector)
                if year_elem:
                    year_text = year_elem.get_text(strip=True)
                    year_match = re.search(r'(\d{4})', year_text)
                    if year_match:
                        year = int(year_match.group(1))
                        break
            
            # Rating - try multiple approaches
            rating = None
            rating_selectors = [
                '.ipc-rating-star--rating',
                'strong',
                '.ratingColumn strong',
                '.cli-rating'
            ]
            
            for selector in rating_selectors:
                rating_elem = element.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    try:
                        rating = float(rating_text)
                        break
                    except ValueError:
                        continue
            
            # URL
            movie_url = None
            link_elem = element.select_one('a[href*="/title/tt"]')
            if link_elem and link_elem.get('href'):
                movie_url = urljoin(self.base_url, link_elem['href'])
            
            # Try to extract rank from the element itself
            extracted_rank = rank
            rank_text = element.get_text()
            rank_match = re.search(r'^(\d+)\.', rank_text.strip())
            if rank_match:
                extracted_rank = int(rank_match.group(1))
            
            return {
                'rank': extracted_rank,
                'title': title,
                'year': year,
                'rating': rating,
                'url': movie_url
            }
            
        except Exception as e:
            logger.error(f"Error in generic extraction: {e}")
            return None
    
    def scrape_top250(self):
        """Main scraping method that tries multiple approaches"""
        logger.info("🎬 Starting comprehensive IMDb Top 250 scraping...")
        
        all_movies = []
        
        # Method 1: Try classic IMDb interface
        logger.info("Method 1: Trying classic IMDb interface...")
        classic_movies = self.try_classic_imdb_page()
        if len(classic_movies) > len(all_movies):
            all_movies = classic_movies
            logger.info(f"✅ Classic interface: {len(all_movies)} movies")
        
        # Method 2: Try paginated requests
        if len(all_movies) < 200:
            logger.info("Method 2: Trying paginated requests...")
            paginated_movies = self.try_paginated_requests()
            if len(paginated_movies) > len(all_movies):
                all_movies = paginated_movies
                logger.info(f"✅ Paginated requests: {len(all_movies)} movies")
        
        # Method 3: Try mobile and alternative endpoints
        if len(all_movies) < 200:
            logger.info("Method 3: Trying mobile and alternative endpoints...")
            alt_movies = self.try_mobile_and_alternative_endpoints()
            if len(alt_movies) > len(all_movies):
                all_movies = alt_movies
                logger.info(f"✅ Alternative endpoints: {len(all_movies)} movies")
        
        # Clean and validate the movie list
        valid_movies = []
        seen_titles = set()
        
        for movie in all_movies:
            if (movie and movie.get('title') and movie['title'] != "Unknown" 
                and movie['title'] not in seen_titles):
                seen_titles.add(movie['title'])
                valid_movies.append(movie)
        
        # Sort by rank and ensure we have sequential ranks
        valid_movies.sort(key=lambda x: x.get('rank', 999))
        for i, movie in enumerate(valid_movies, 1):
            movie['rank'] = i
        
        logger.info(f"Final movie count: {len(valid_movies)}")
        
        return valid_movies[:250]  # Return max 250 movies
    
    def get_additional_details(self, movie_url):
        """Get additional movie details"""
        try:
            response = self.get_page_with_retries(movie_url)
            if not response:
                return {'director': 'Unknown', 'runtime_minutes': None, 'genres': 'Unknown'}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Director
            director = "Unknown"
            director_selectors = [
                'a[class*="ipc-metadata-list-item__list-content-item--link"]',
                '.credit_summary_item a',
                '[data-testid="title-pc-principal-credit"] a'
            ]
            
            for selector in director_selectors:
                director_elem = soup.select_one(selector)
                if director_elem:
                    director = director_elem.get_text(strip=True)
                    break
            
            # Runtime
            runtime = None
            runtime_text = soup.get_text()
            runtime_match = re.search(r'(\d+)\s*min', runtime_text)
            if runtime_match:
                runtime = int(runtime_match.group(1))
            
            # Genres
            genres = []
            genre_selectors = [
                '[data-testid="genres"] a',
                '.see-more.inline a[href*="genre"]',
                '.subtext a[href*="genre"]'
            ]
            
            for selector in genre_selectors:
                genre_elems = soup.select(selector)
                if genre_elems:
                    genres = [elem.get_text(strip=True) for elem in genre_elems[:3]]
                    break
            
            return {
                'director': director,
                'runtime_minutes': runtime,
                'genres': ', '.join(genres) if genres else "Unknown"
            }
            
        except Exception as e:
            logger.error(f"Error getting details for {movie_url}: {e}")
            return {'director': 'Unknown', 'runtime_minutes': None, 'genres': 'Unknown'}
    
    def save_to_csv(self, movies, filename='imdb_top250_movies.csv'):
        """Save movies to CSV"""
        if not movies:
            logger.error("No movies to save")
            return False
        
        try:
            df = pd.DataFrame(movies)
            
            # Basic columns only - no additional details
            columns = ['rank', 'title', 'year', 'rating', 'url']
            
            # Keep only existing columns
            columns = [col for col in columns if col in df.columns]
            df = df[columns]
            
            # Sort by rank
            df = df.sort_values('rank')
            
            # Save to CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"✅ Saved {len(df)} movies to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return False
    
    def display_summary(self, movies, top_n=10):
        """Display summary of scraped movies"""
        if not movies:
            print("❌ No movies found")
            return
        
        print(f"\n{'='*60}")
        print(f"📊 SCRAPING RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"Total movies scraped: {len(movies)}")
        
        if len(movies) >= 200:
            print("✅ Successfully got most/all of the Top 250!")
        elif len(movies) >= 100:
            print("⚠️  Got a good portion of the Top 250 movies")
        else:
            print("⚠️  Limited results due to IMDb's dynamic loading")
        
        print(f"\n🎬 Top {min(top_n, len(movies))} Movies:")
        print("-" * 60)
        
        for i, movie in enumerate(sorted(movies, key=lambda x: x.get('rank', 999))[:top_n]):
            print(f"{movie.get('rank', i+1):3d}. {movie.get('title', 'Unknown')} ({movie.get('year', 'Unknown')}) - {movie.get('rating', 'N/A')}/10")
        
        # Statistics
        df = pd.DataFrame(movies)
        if 'rating' in df.columns and df['rating'].notna().any():
            print(f"\n📈 Average Rating: {df['rating'].mean():.2f}")
        if 'year' in df.columns and df['year'].notna().any():
            print(f"📅 Year Range: {int(df['year'].min())} - {int(df['year'].max())}")
        
        print(f"{'='*60}")

def main():
    """Main function"""
    print("🎬 IMDb Top 250 Movies Scraper")
    print("=" * 50)
    print("✅ No Selenium required - Pure web scraping!")
    print("📡 Uses multiple methods to get all 250 movies")
    print()
    
    scraper = IMDbTop250Scraper()
    
    # Simple filename input only
    filename = input("📁 Enter CSV filename (default: imdb_top250_movies.csv): ").strip()
    if not filename:
        filename = 'imdb_top250_movies.csv'
    
    print(f"\n🚀 Starting scraping process...")
    print("⏳ This may take a few minutes...")
    
    try:
        # Scrape movies (no additional details to avoid errors)
        movies = scraper.scrape_top250()
        
        if movies:
            # Save to CSV
            success = scraper.save_to_csv(movies, filename)
            
            if success:
                scraper.display_summary(movies, top_n=15)
                print(f"\n💾 Data saved to: {filename}")
                print(f"📊 Total movies in CSV: {len(movies)}")
                
                if len(movies) < 200:
                    print("\n💡 Tips for better results:")
                    print("   • Try running the script multiple times")
                    print("   • IMDb's structure changes frequently")
                
            else:
                print("❌ Failed to save data to CSV")
                
        else:
            print("❌ No movie data could be scraped")
            print("🔧 This might be due to:")
            print("   • IMDb blocking requests")
            print("   • Changed website structure") 
            print("   • Network connectivity issues")
            
    except KeyboardInterrupt:
        print("\n⏹️  Scraping stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()