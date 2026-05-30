import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

def get_bcv_rate():
    """Obtiene la tasa oficial del BCV."""
    url = "https://www.bcv.org.ve/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        usd_container = soup.find("div", {"id": "dolar"})
        if usd_container:
            rate_element = usd_container.find("strong")
            if rate_element:
                return float(rate_element.text.strip().replace(",", "."))
    except Exception as e:
        print(f"Error detectado en BCV: {e}")
    return None

def get_binance_rate():
    """Obtiene la tasa del Paralelo vía Binance P2P con payload y cabeceras web reales."""
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    
    # Payload idéntico al que genera un navegador real al consultar el P2P
    payload = {
        "asset": "USDT",
        "fiat": "VES",
        "merchantCheck": False,
        "page": 1,
        "payTypes": [],
        "publisherType": None,
        "rows": 10,
        "tradeType": "SELL",
        "transAmount": "",
        "countries": []
    }
    
    # Cabeceras de simulación de navegador completo
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Language": "es-ES,es;q=0.9",
        "Cache-Control": "no-cache",
        "Origin": "https://p2p.binance.com",
        "Lang": "es",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=25)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and len(data["data"]) > 0:
                # Extraemos el precio del primer anuncio del listado
                price = data["data"][0]["adv"]["price"]
                return float(price)
            else:
                print("Binance devolvió estructura vacía (Posible bloqueo suave).")
        else:
            print(f"Binance respondió con código de estado: {response.status_code}")
            
    except Exception as e:
        print(f"Error crítico conectando a Binance P2P: {e}")
        
    return None

def main():
    # 1. Obtener los datos
    bcv = get_bcv_rate()
    binance = get_binance_rate()
    
    # 2. Resguardo de valores
    bcv_val = bcv if bcv is not None else 0.0
    binance_val = binance if binance is not None else 0.0

    # Fecha y hora actual
    now = datetime.now().isoformat()
    
    # 3. Preparar la estructura de archivos
    os.makedirs("v1/dolares", exist_ok=True)
    
    oficial = {
        "moneda": "USD",
        "nombre": "Oficial",
        "promedio": bcv_val,
        "fechaActualizacion": now
    }
    with open("v1/dolares/oficial", "w") as f:
        json.dump(oficial, f, indent=4)
        
    paralelo = {
        "moneda": "USD",
        "nombre": "Paralelo",
        "promedio": binance_val,
        "fechaActualizacion": now
    }
    with open("v1/dolares/paralelo", "w") as f:
        json.dump(paralelo, f, indent=4)

    index_data = [oficial, paralelo]
    with open("index.json", "w") as f:
        json.dump(index_data, f, indent=4)

    print(f"Proceso finalizado. BCV: {bcv_val} | Binance (Paralelo): {binance_val}")

if __name__ == "__main__":
    main()
