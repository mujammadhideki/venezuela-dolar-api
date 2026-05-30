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

def get_paralelo_rate():
    """
    Obtiene la tasa de Binance P2P / Paralelo haciendo web scraping 
    a ExchangeMonitor, saltándose los bloqueos de APIs.
    """
    # Buscamos directamente en la página de estadísticas de Binance de ExchangeMonitor
    url = "https://exchangemonitor.net/estadisticas/ve/binance"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Encontramos la etiqueta H2 que contiene el precio grande en la web
        price_element = soup.find("h2", class_="tasa")
        if price_element:
            # Extraemos el texto, quitamos la palabra 'Bs.' y reemplazamos la coma por punto
            price_text = price_element.text.replace("Bs.", "").strip().replace(",", ".")
            return float(price_text)
            
    except Exception as e:
        print(f"Error extrayendo de ExchangeMonitor: {e}")
        
    return None

def main():
    # 1. Obtener los datos
    bcv = get_bcv_rate()
    paralelo = get_paralelo_rate()
    
    # 2. Resguardo de valores
    bcv_val = bcv if bcv is not None else 0.0
    binance_val = paralelo if paralelo is not None else 0.0

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
        
    paralelo_data = {
        "moneda": "USD",
        "nombre": "Paralelo",
        "promedio": binance_val,
        "fechaActualizacion": now
    }
    with open("v1/dolares/paralelo", "w") as f:
        json.dump(paralelo_data, f, indent=4)

    index_data = [oficial, paralelo_data]
    with open("index.json", "w") as f:
        json.dump(index_data, f, indent=4)

    print(f"Proceso finalizado. BCV: {bcv_val} | Binance (Paralelo): {binance_val}")

if __name__ == "__main__":
    main()
