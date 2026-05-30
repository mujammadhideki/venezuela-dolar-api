import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

def get_bcv_rate():
    """Obtiene la tasa oficial del BCV haciendo web scraping (Comprobado que funciona)."""
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
    Obtiene la tasa del dólar paralelo usando DolarApi.
    Es un servicio gratuito para desarrolladores que no bloquea a GitHub Actions.
    """
    url = "https://ve.dolarapi.com/v1/dolares/paralelo"
    try:
        # Se realiza una petición limpia sin headers complejos
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # DolarApi devuelve un JSON claro con la llave 'promedio'
        if "promedio" in data:
            return float(data["promedio"])
            
    except Exception as e:
        print(f"Error en DolarApi (Paralelo): {e}")
        
    return None

def main():
    # 1. Obtener los datos
    bcv = get_bcv_rate()
    paralelo = get_paralelo_rate()
    
    # 2. Resguardo de valores (Si algo falla guarda 0.0)
    bcv_val = bcv if bcv is not None else 0.0
    binance_val = paralelo if paralelo is not None else 0.0

    # Fecha y hora actual
    now = datetime.now().isoformat()
    
    # 3. Preparar la estructura de carpetas
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

    print(f"Proceso finalizado. BCV: {bcv_val} | Paralelo: {binance_val}")

if __name__ == "__main__":
    main()
