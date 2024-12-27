from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
from flask import Flask, render_template_string
import time
import json

# Configure Selenium
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Set ProxyMesh (replace with your ProxyMesh credentials)
    proxy = "http://adityanaikade:yBV.xek5qVBaf6H@us-west.proxy.proxymesh.com:31280"
    chrome_options.add_argument(f"--proxy-server={proxy}")

    # Automatically manage ChromeDriver
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# Connect to MongoDB
def connect_to_mongo():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["x_trending_topics"]
    return db["trends"]

# Scrape X Trending Topics
def scrape_trending_topics():
    driver = create_driver()
    collection = connect_to_mongo()

    try:
        # Navigate to X login page
        driver.get("https://x.com/i/flow/login")
        time.sleep(5)

        # Log in to X 
        username_field = driver.find_element(By.NAME, "text")
        username_field.send_keys("AdityaNaikade")
        username_field.submit()
        time.sleep(5)

        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys("adyanaik@03")  
        password_field.submit()
        time.sleep(5)

        # Navigate to the homepage and fetch trending topics
        driver.get("https://x.com/home")
        time.sleep(5)

        # Locate the trending topics
        trends = driver.find_elements(By.XPATH, "//div[@aria-label='Timeline: Trending now']//span")
        trending_topics = [trend.text for trend in trends[:5]]

        # Collect additional details
        unique_id = str(int(time.time()))
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        ip_address = proxy.split("@")[1].split(":")[0]  # Extract IP from proxy URL

        # Store in MongoDB
        record = {
            "_id": unique_id,
            "trend1": trending_topics[0] if len(trending_topics) > 0 else "",
            "trend2": trending_topics[1] if len(trending_topics) > 1 else "",
            "trend3": trending_topics[2] if len(trending_topics) > 2 else "",
            "trend4": trending_topics[3] if len(trending_topics) > 3 else "",
            "trend5": trending_topics[4] if len(trending_topics) > 4 else "",
            "timestamp": timestamp,
            "ip_address": ip_address,
        }
        collection.insert_one(record)

        return record
    finally:
        driver.quit()

# Flask Web App
app = Flask(__name__)

@app.route("/")
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>X Trends</title>
    </head>
    <body>
        <h1>X (formerly Twitter) Trends</h1>
        <button onclick="location.href='/run-script'">Click here to run the script</button>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route("/run-script")
def run_script():
    result = scrape_trending_topics()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>X Trends</title>
    </head>
    <body>
        <h1>These are the most happening topics as on {result['timestamp']}</h1>
        <ul>
            <li>{result['trend1']}</li>
            <li>{result['trend2']}</li>
            <li>{result['trend3']}</li>
            <li>{result['trend4']}</li>
            <li>{result['trend5']}</li>
        </ul>
        <p>The IP address used for this query was {result['ip_address']}.</p>
        <h3>Here’s a JSON extract of this record from MongoDB:</h3>
        <pre>{json.dumps(result, indent=4)}</pre>
        <button onclick="location.href='/'">Click here to run the query again</button>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(debug=True)
