import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz
from urllib.parse import urljoin
import time

def create_rss():
    base_url = 'https://www.nrc.no'
    news_url = f'{base_url}/latest-news/'
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(news_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Feil ved henting av nettside. Status: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    fg = FeedGenerator()
    fg.title('NRC Latest News')
    fg.link(href=news_url, rel='alternate')
    fg.description('Automatisk generert RSS-feed for Flyktninghjelpen (NRC).')
    fg.language('en')
    
    articles = soup.find_all('a', href=True)
    seen_urls = set()
    count = 0
    max_articles = 15
    
    for article in articles:
        if count >= max_articles:
            break
            
        url = article['href']
        
        if any(keyword in url for keyword in ['/news/', '/press-releases/', '/perspectives/']) and url not in seen_urls:
            seen_urls.add(url)
            
            title_text = article.get_text(strip=True)
            if len(title_text) < 10:
                continue
                
            full_url = urljoin(base_url, url)
            
            # Variabler for ingress og bilde
            intro_text = "Les hele saken på nettsiden."
            image_url = None
            
            try:
                art_response = requests.get(full_url, headers=headers, timeout=5)
                art_soup = BeautifulSoup(art_response.text, 'html.parser')
                
                # 1. Hent ingress (meta description)
                meta_desc = art_soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    intro_text = meta_desc['content']
                else:
                    first_p = art_soup.find('p')
                    if first_p:
                        intro_text = first_p.get_text(strip=True)
                        
                # 2. --- NYTT: Hent bilde (Open Graph Image) ---
                meta_image = art_soup.find('meta', attrs={'property': 'og:image'})
                if meta_image and meta_image.get('content'):
                    image_url = meta_image['content']
                    # Pass på at URL-en er komplett
                    image_url = urljoin(base_url, image_url)
                    
            except Exception:
                pass # Ignorerer feil hvis siden ikke laster, bruker standardtekst
            
            time.sleep(0.5) 
            
            fe = fg.add_entry()
            fe.title(title_text)
            fe.link(href=full_url)
            
            # --- NYTT: Legg til bilde i RSS-leseren ---
            if image_url:
                # Metode A: Standard RSS enclosure (for avanserte lesere som Feedly)
                # Vi bruker 'image/jpeg' som en universell standard
                fe.enclosure(image_url, '0', 'image/jpeg')
                
                # Metode B: HTML-bilde direkte i teksten (for enkle lesere/nettlesere)
                html_content = f'<img src="{image_url}" alt="{title_text}" style="max-width:100%; border-radius:8px; margin-bottom:12px;"/><br>{intro_text}'
                fe.description(html_content)
            else:
                fe.description(intro_text)
                
            fe.pubDate(datetime.now(pytz.utc))
            
            count += 1
            
    fg.rss_file('rss.xml')
    print("Vellykket: rss.xml er opprettet med tittel, ingress og bilde!")

if __name__ == '__main__':
    create_rss()
