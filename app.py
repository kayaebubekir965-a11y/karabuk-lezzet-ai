import os
from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import requests

app = Flask(__name__)

# HUGGING FACE API (Bedava AI Modeli)
# Sunucuyu yormamak için modeli indirmiyoruz, internetten soruyoruz.
API_URL = "https://api-inference.huggingface.co/models/savasy/bert-base-turkish-sentiment-cased"
# Not: Çok fazla istek atarsan HF token isteyebilir ama başlangıçta tokensız çalışır.

def query_ai(payload):
    try:
        response = requests.post(API_URL, json=payload)
        return response.json()
    except:
        return [{"label": "Nötr", "score": 0.5}]

def get_google_reviews(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Arayüzsüz mod (Sunucu için şart)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Render üzerinde Chrome'un yerini belirtiyoruz (render-build.sh kuracak)
    chrome_options.binary_location = "/opt/render/project/src/chrome/linux-114.0.5735.90/chrome-linux64/chrome"

    # Driver kurulumu
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    reviews = []
    try:
        driver.get(url)
        time.sleep(3) # Sayfanın yüklenmesini bekle
        
        # Google Maps yorumları genellikle bu class ile gelir ama değişebilir
        # Güncel class isimleri: wiI7pd, rsqaWe
        elements = driver.find_elements(By.CLASS_NAME, "wiI7pd")
        
        if not elements:
             elements = driver.find_elements(By.CLASS_NAME, "rsqaWe")

        for el in elements[:10]: # Max 10 yorum çekelim (Hız için)
            text = el.text.strip()
            if text:
                reviews.append(text)
                
    except Exception as e:
        print("Hata:", e)
    finally:
        driver.quit()
        
    return reviews

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "Link girmediniz!"}), 400

    # 1. Yorumları Çek
    reviews = get_google_reviews(url)
    
    if not reviews:
        return jsonify({"error": "Yorum bulunamadı veya link hatalı."}), 404

    # 2. Yapay Zeka ile Analiz Et
    results = []
    total_score = 0
    
    for review in reviews:
        ai_response = query_ai({"inputs": review})
        
        # API'den gelen yanıtı işle
        try:
            # HuggingFace bazen liste içinde liste döner
            if isinstance(ai_response, list) and len(ai_response) > 0:
                if isinstance(ai_response[0], list):
                    top_result = ai_response[0][0]
                else:
                    top_result = ai_response[0]
            
                label = top_result.get('label', 'positive')
                score = top_result.get('score', 0)
                
                status = "Pozitif" if label == "positive" else "Negatif"
                point = 10 if label == "positive" else 1
                
                total_score += point
                results.append({"text": review, "status": status, "confidence": score})
        except:
            results.append({"text": review, "status": "Nötr", "confidence": 0})

    # Ortalama Puan
    final_rating = total_score / len(reviews) if reviews else 0

    return jsonify({
        "reviews": results,
        "rating": f"{final_rating:.1f}/10"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)