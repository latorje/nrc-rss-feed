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
    max_articles = 15 # Henter de 15 nyeste for at scriptet skal kjøre raskt
    
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
            
            # --- NYTT: Hent ingressen fra selve artikkelen ---
            try:
                # Laster ned selve artikkelen for å hente ut beskrivelsen
                art_response = requests.get(full_url, headers=headers, timeout=5)
                art_soup = BeautifulSoup(art_response.text, 'html.parser')
                
                # Finner 'meta description' som inneholder ingressen
                meta_desc = art_soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    intro_text = meta_desc['content']
                else:
                    # Fallback hvis meta mangler: Hent første avsnitt (<p>)
                    first_p = art_soup.find('p')
                    intro_text = first_p.get_text(strip=True) if first_p else "Les hele saken på nettsiden."
                    
            except Exception:
                intro_text = "Les hele saken på nettsiden."
            
            # Liten pause (0.5 sek) for ikke å overbelaste NRCs servere
            time.sleep(0.5) 
            # ------------------------------------------------
            
            fe = fg.add_entry()
            fe.title(title_text)
            fe.link(href=full_url)
            fe.description(intro_text) # Ingressen legges inn i RSS-feeden
            fe.pubDate(datetime.now(pytz.utc))
            
            count += 1
            
    fg.rss_file('rss.xml')
    print("Vellykket: rss.xml er opprettet med tittel og ingress!")

if __name__ == '__main__':
    create_rss()
