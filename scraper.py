import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz
from urllib.parse import urljoin

def create_rss():
    base_url = 'https://www.nrc.no'
    news_url = f'{base_url}/latest-news/'
    
    # Vi utgir oss for å være en vanlig nettleser for ikke å bli blokkert
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(news_url, headers=headers)
    
    # Sjekk at nettsiden lastes inn riktig
    if response.status_code != 200:
        print(f"Feil ved henting av nettside. Status: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Sett opp RSS-feeden
    fg = FeedGenerator()
    fg.title('NRC Latest News')
    fg.link(href=news_url, rel='alternate')
    fg.description('Automatisk generert RSS-feed for Flyktninghjelpen (NRC).')
    fg.language('en')
    
    # Finn alle lenker på siden
    articles = soup.find_all('a', href=True)
    seen_urls = set()
    
    for article in articles:
        url = article['href']
        
        # Filtrer kun lenker som peker til typiske nyhetsartikler eller pressemeldinger
        # (Ekskluderer navigasjonsmenyer og donasjonssider)
        if any(keyword in url for keyword in ['/news/', '/press-releases/', '/perspectives/']) and url not in seen_urls:
            seen_urls.add(url)
            
            # Prøv å finne tittelen på artikkelen. NRC bruker ofte h2, h3 eller bare tekst inni lenken.
            title_text = article.get_text(strip=True)
            
            # Hopp over tomme lenker (f.eks. bilde-lenker uten alt-tekst)
            if len(title_text) < 10:
                continue
                
            full_url = urljoin(base_url, url)
            
            # Legg til artikkelen i RSS-feeden
            fe = fg.add_entry()
            fe.title(title_text)
            fe.link(href=full_url)
            fe.pubDate(datetime.now(pytz.utc)) # Setter dagens dato
            
    # Lagre som en XML-fil
    fg.rss_file('rss.xml')
    print("Vellykket: rss.xml er opprettet!")

if __name__ == '__main__':
    create_rss()
