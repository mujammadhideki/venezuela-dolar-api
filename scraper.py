import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

def get_bcv_rate():
    url = "https://www.bcv.org.ve/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # BCV has multiple currency rates. We want the one for USD.
        # The container usually has id="dolar"
        usd_container = soup.find("div", {"id": "dolar"})
        if usd_container:
            # Inside it should be the rate
            rate_element = usd_container.find("strong")
            if rate_element:
                rate_text = rate_element.text.strip().replace(",", ".")
                return float(rate_text)
        
        # Fallback if structure changed slightly or initial selector fails
        for container in soup.find_all("div", class_="field-content"):
            if "USD" in container.text:
                strong_tag = container.find_next("strong")
                if strong_tag:
                    rate_text = strong_tag.text.strip().replace(",", ".")
                    return float(rate_text)

    except Exception as e:
        print(f"Error fetching BCV: {e}")
    return None

def get_binance_rate():
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    payload = {
        "asset": "USDT",
        "fiat": "VES",
        "merchantCheck": False,
        "page": 1,
        "payTypes": [],
        "publisherType": None,
        "rows": 10,
        "tradeType": "BUY"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Filter out ads (promoted ads usually have isPromoted: True or something similar)
        # In the public API, we usually look for the first organic one.
        valid_ads = [ad for ad in data.get("data", []) if not ad.get("advertiser", {}).get("isPromoted", False)]
        
        if len(valid_ads) >= 2:
            # User wants the 2nd organic result if possible, or 1st if only 1 exists
            return float(valid_ads[1]["adv"]["price"])
        elif len(valid_ads) == 1:
            return float(valid_ads[0]["adv"]["price"])
    except Exception as e:
        print(f"Error fetching Binance: {e}")
    return None

def main():
    bcv = get_bcv_rate()
    binance = get_binance_rate()
    
    now = datetime.now().isoformat()
    
    # Structure compatible with DolarAPI (approx)
    data = [
        {
            "moneda": "USD",
            "nombre": "Oficial",
            "promedio": bcv,
            "fechaActualizacion": now
        },
        {
            "moneda": "USD",
            "nombre": "Paralelo",
            "promedio": binance,
            "fechaActualizacion": now
        }
    ]
    
    # Save to index.json
    with open("index.json", "w") as f:
        json.dump(data, f, indent=4)
    
    # Save individual for user's specific formula requests if needed
    # =IMPORTJSONAPI("https://.../v1/dolares/oficial")
    os.makedirs("v1/dolares", exist_ok=True)
    
    oficial = {
        "moneda": "USD",
        "nombre": "Oficial",
        "promedio": bcv,
        "fechaActualizacion": now
    }
    with open("v1/dolares/oficial", "w") as f:
        json.dump(oficial, f, indent=4)
        
    paralelo = {
        "moneda": "USD",
        "nombre": "Paralelo",
        "promedio": binance,
        "fechaActualizacion": now
    }
    with open("v1/dolares/paralelo", "w") as f:
        json.dump(paralelo, f, indent=4)

    print(f"Rates updated: BCV={bcv}, Binance={binance}")

if __name__ == "__main__":
    main()
