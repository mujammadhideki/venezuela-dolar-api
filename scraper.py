import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

def get_bcv_rate():
    url = "https://www.bcv.org.ve/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        # verify=False porque el certificado del BCV a veces falla en servidores externos
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Intento 1: Por ID directo (el más común)
        usd_container = soup.find("div", {"id": "dolar"})
        if usd_container:
            rate_element = usd_container.find("strong")
            if rate_element:
                return float(rate_element.text.strip().replace(",", "."))
        
        # Intento 2: Por clase si el ID falla
        for container in soup.find_all("div", class_="field-content"):
            if "USD" in container.text:
                strong_tag = container.find_next("strong")
                if strong_tag:
                    return float(strong_tag.text.strip().replace(",", "."))
    except Exception as e:
        print(f"Error fetching BCV: {e}")
    return None

def get_binance_rate():
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    
    # Payload actualizado con parámetros obligatorios para evitar "illegal parameter"
    payload = {
        "asset": "USDT",
        "fiat": "VES",
        "merchantCheck": False,
        "page": 1,
        "payTypes": [],
        "publisherType": None,
        "rows": 10,
        "tradeType": "BUY",
        "transAmount": "0"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("data") and len(data["data"]) > 0:
            # Tomamos el primer anuncio orgánico disponible
            price = data["data"][0]["adv"]["price"]
            return float(price)
    except Exception as e:
        print(f"Error fetching Binance: {e}")
    return None

def main():
    bcv = get_bcv_rate()
    binance = get_binance_rate()
    
    # Si alguno falla, mantenemos un valor de referencia o el anterior para no dejar el JSON vacío
    # Puedes cambiar estos valores por los que tenías (ej. 550.0)
    bcv = bcv if bcv else 0.0 
    binance = binance if binance else 0.0

    now = datetime.now().isoformat()
    
    # Datos para index.json
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
    
    # Guardar index.json principal
    with open("index.json", "w") as f:
        json.dump(data, f, indent=4)
    
    # Guardar archivos individuales en v1/dolares/
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

    print(f"Actualización exitosa: BCV={bcv}, Binance={binance}")

if __name__ == "__main__":
    main()
