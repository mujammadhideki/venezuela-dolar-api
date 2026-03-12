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
        # verify=False porque el certificado del BCV a veces da problemas en GitHub Actions
        response = requests.get(url, headers=headers, verify=False, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Buscar el contenedor específico del dólar
        usd_container = soup.find("div", {"id": "dolar"})
        if usd_container:
            rate_element = usd_container.find("strong")
            if rate_element:
                return float(rate_element.text.strip().replace(",", "."))
    except Exception as e:
        print(f"Error detectado en BCV: {e}")
    return None

def get_binance_rate():
    """Obtiene la tasa del Paralelo vía Binance P2P (Simulando venta)."""
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    
    # Configuramos el payload para obtener el precio real de mercado
    payload = {
        "asset": "USDT",
        "fiat": "VES",
        "merchantCheck": False,
        "page": 1,
        "payTypes": [],
        "publisherType": None,
        "rows": 10,
        "tradeType": "SELL",    # "SELL" nos da el precio al que la gente vende (el real)
        "transAmount": "1000"   # Filtramos montos bajos para evitar tasas falsas
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if data.get("data") and len(data["data"]) > 0:
            # Tomamos el primer anuncio de la lista (suele ser el más representativo)
            price = data["data"][0]["adv"]["price"]
            return float(price)
    except Exception as e:
        print(f"Error detectado en Binance: {e}")
    return None

def main():
    # 1. Obtener los datos
    bcv = get_bcv_rate()
    binance = get_binance_rate()
    
    # 2. Si fallan, ponemos 0.0 para saber que hubo un error de conexión
    bcv_val = bcv if bcv else 0.0
    binance_val = binance if binance else 0.0

    # Fecha y hora actual
    now = datetime.now().isoformat()
    
    # 3. Preparar la estructura de archivos
    os.makedirs("v1/dolares", exist_ok=True)
    
    # Archivo de tasa Oficial
    oficial = {
        "moneda": "USD",
        "nombre": "Oficial",
        "promedio": bcv_val,
        "fechaActualizacion": now
    }
    with open("v1/dolares/oficial", "w") as f:
        json.dump(oficial, f, indent=4)
        
    # Archivo de tasa Paralelo
    paralelo = {
        "moneda": "USD",
        "nombre": "Paralelo",
        "promedio": binance_val,
        "fechaActualizacion": now
    }
    with open("v1/dolares/paralelo", "w") as f:
        json.dump(paralelo, f, indent=4)

    # Archivo index.json (Resumen de ambos)
    index_data = [oficial, paralelo]
    with open("index.json", "w") as f:
        json.dump(index_data, f, indent=4)

    print(f"Proceso finalizado. BCV: {bcv_val} | Binance: {binance_val}")

if __name__ == "__main__":
    main()
