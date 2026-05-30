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

def get_paralelo_rate():
    """
    Obtiene la tasa del dólar paralelo usando una API pública alternativa
    para evitar los bloqueos de Cloudflare/Binance en GitHub Actions.
    """
    # Usamos la API pública de pydolarvenezuela que monitorea EnParaleloVzla y Binance
    url = "https://pydolarvenezuela-api.vercel.app/api/v1/dollar?page=enparalelovzla"
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # Extraemos el promedio general del paralelo
        if "promedio" in data:
            return float(data["promedio"])
            
    except Exception as e:
        print(f"Error detectado en Paralelo (API): {e}")
        
        # Plan B: Si la API anterior falla, intentamos con la de Binance P2P limpia
        return get_binance_backup()
    return None

def get_binance_backup():
    """Plan de respaldo directo a Binance P2P con headers optimizados."""
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    payload = {
        "asset": "USDT",
        "fiat": "VES",
        "merchantCheck": False,
        "page": 1,
        "payTypes": [],
        "publisherType": None,
        "rows": 5,
        "tradeType": "SELL",
        "transAmount": "" # Dejamos el monto vacío para evitar respuestas erróneas si cambia la API
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                return float(data["data"][0]["adv"]["price"])
    except Exception as e:
        print(f"Error en Plan B (Binance directo): {e}")
    return None

def main():
    # 1. Obtener los datos
    bcv = get_bcv_rate()
    paralelo = get_paralelo_rate()
    
    # 2. Si fallan por completo, dejamos el valor en 0.0 para alertar un error real
    bcv_val = bcv if bcv else 0.0
    binance_val = paralelo if paralelo else 0.0

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
    paralelo_data = {
        "moneda": "USD",
        "nombre": "Paralelo",
        "promedio": binance_val,
        "fechaActualizacion": now
    }
    with open("v1/dolares/paralelo", "w") as f:
        json.dump(paralelo_data, f, indent=4)

    # Archivo index.json (Resumen de ambos)
    index_data = [oficial, paralelo_data]
    with open("index.json", "w") as f:
        json.dump(index_data, f, indent=4)

    print(f"Proceso finalizado. BCV: {bcv_val} | Paralelo: {binance_val}")

if __name__ == "__main__":
    main()
