from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import csv
from urllib.parse import urljoin, urlparse

def initialize_driver():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)  
    driver.maximize_window()
    return driver

def generate_csv_filename(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    domain = re.sub(r'\W+', '_', domain)
    return f"{domain}.csv"


def scrape_page_content(driver, url):
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')
    
    
    title = soup.title.string if soup.title else "No title"
    
    
    paragraphs = soup.find_all('p')
    text_content = "\n".join([p.get_text() for p in paragraphs])
    
    
    headers = [header.get_text() for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
    
    
    images = [urljoin(url, img.get('src')) for img in soup.find_all('img', src=True)]
    
    
    links = [urljoin(url, a.get('href')) for a in soup.find_all('a', href=True)]
    
    
    list_items = []
    for ul in soup.find_all(['ul', 'ol']):
        for li in ul.find_all('li'):
            list_items.append(li.get_text(strip=True))
    
    
    bold_tags = [bold.get_text() for bold in soup.find_all(['b', 'strong', 'span', {'style': 'font-weight:bold'}])]
    
    
    hidden_elements = [element.get_text(strip=True) for element in soup.find_all(style=re.compile(".*display\\s*:\\s*none.*"))]
    
    
    block_elements = [block.get_text(strip=True) for block in soup.find_all(['div', 'section', 'article', 'header', 'footer', 'main'])]
    
    
    page_data = {
        "url": url,
        "title": title,
        "content": text_content,
        "headers": ", ".join(headers),
        "images": ", ".join(images),
        "links": ", ".join(links),
        "list_items": ", ".join(list_items),
        "bold_tags": ", ".join(bold_tags),
        "hidden_elements": ", ".join(hidden_elements),
        "block_elements": ", ".join(block_elements)
    }
    
    return page_data


def save_data_to_csv(data, csv_filename):
    fieldnames = ["url", "title", "content", "headers", "images", "links", "list_items", "bold_tags", "hidden_elements", "block_elements"]
    with open(csv_filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerow(data)
    print(f"Data saved for URL: {data['url']}")


def observe_and_scrape(url):
    driver = initialize_driver()
    driver.get(url)
    
    csv_filename = generate_csv_filename(url)
    
    
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["url", "title", "content", "headers", "images", "links", "list_items", "bold_tags", "hidden_elements", "block_elements"])
        writer.writeheader()
    
    visited_content = set()  

    try:
        print("Start scrolling the page. The script will capture data periodically.")
        while True:
            
            page_data = scrape_page_content(driver, url)
            
            content_hash = hash(page_data["content"])
            if content_hash not in visited_content:
                visited_content.add(content_hash)
                save_data_to_csv(page_data, csv_filename)
                print("New content scraped and saved.")
            else:
                print("Duplicate content detected, skipping.")
            
            time.sleep(5)  

    except KeyboardInterrupt:
        print("Manual interruption received. Ending script.")
    finally:
        driver.quit()
        print(f"Data saved to '{csv_filename}'.")

if __name__ == "__main__":
    start_url = "https://www.envigo.co.in/"
    observe_and_scrape(start_url)

