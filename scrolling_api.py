from flask import Flask, request, jsonify, send_file
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin, urlparse
import os

app = Flask(__name__)


def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)  
    driver.maximize_window()
    return driver


def scrape_page_with_scrolling(driver, url):
    driver.get(url)
    time.sleep(3)

    last_height = driver.execute_script("return document.body.scrollHeight")
    page_data = []

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    
    soup = BeautifulSoup(driver.page_source, 'lxml')
    title = soup.title.string if soup.title else "No title"
    paragraphs = soup.find_all('p')
    text_content = "\n".join([p.get_text() for p in paragraphs])
    headers = [header.get_text() for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
    images = [urljoin(url, img.get('src')) for img in soup.find_all('img', src=True)]
    links = [urljoin(url, a.get('href')) for a in soup.find_all('a', href=True)]

    page_data.append({
        "url": url,
        "title": title,
        "content": text_content,
        "headers": ", ".join(headers),
        "images": ", ".join(images),
        "links": ", ".join(links)
    })

    driver.quit()
    return page_data


def generate_csv_filename(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    domain = re.sub(r'\W+', '_', domain)
    return f"{domain}.csv"


@app.route('/start_scrolling', methods=['POST'])
def start_scrolling():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL is required"}), 400

    driver = initialize_driver()
    page_data = scrape_page_with_scrolling(driver, url)

    csv_filename = generate_csv_filename(url)
    df = pd.DataFrame(page_data)
    df.to_csv(csv_filename, index=False)

    return jsonify({"message": f"Scraping completed for {url}", "csv_file": csv_filename})


@app.route('/download_csv', methods=['GET'])
def download_csv():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL is required"}), 400

    csv_filename = generate_csv_filename(url)
    if os.path.exists(csv_filename):
        return send_file(csv_filename, as_attachment=True)
    else:
        return jsonify({"error": "CSV file not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
