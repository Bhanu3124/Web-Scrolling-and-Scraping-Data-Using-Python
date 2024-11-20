from flask import Flask, request, jsonify
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, urlparse
import csv
import os

app = Flask(__name__)

def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  
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
    list_items = [li.get_text(strip=True) for ul in soup.find_all(['ul', 'ol']) for li in ul.find_all('li')]
    bold_tags = [bold.get_text() for bold in soup.find_all(['b', 'strong', 'span'], {'style': 'font-weight:bold'})]
    hidden_elements = [element.get_text(strip=True) for element in soup.find_all(style=re.compile(".*display\\s*:\\s*none.*"))]
    block_elements = [block.get_text(strip=True) for block in soup.find_all(['div', 'section', 'article', 'header', 'footer', 'main'])]

    return {
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

@app.route('/scrape', methods=['POST'])
def scrape_website():
    request_data = request.json
    url = request_data.get("url")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    driver = initialize_driver()
    try:
        driver.get(url)
        page_data = scrape_page_content(driver, url)

        csv_filename = generate_csv_filename(url)
        csv_filepath = os.path.join(os.getcwd(), csv_filename)
        with open(csv_filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=page_data.keys())
            writer.writeheader()
            writer.writerow(page_data)

        return jsonify({
            "message": "Scraping successful",
            "data": page_data,
            "csv_file": csv_filename
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        driver.quit()

if __name__ == "__main__":
    app.run(debug=True, port=5000)

