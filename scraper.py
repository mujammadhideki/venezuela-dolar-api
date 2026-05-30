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
    Obtiene la tasa de Binance P2P a través de un espejo público (CriptoDolar)
    que no bloquea los servidores de GitHub Actions.
    """
    url = "https://api.criptodolar.me/v1/providers/binance?fiat=ves"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # Esta API devuelve una lista o un diccionario directo con el precio
        # Buscamos el valor de compra/venta o promedio
        if isinstance(data, list) and len(data) > 0:
            return float(data[0].get("price", 0.0))
        elif isinstance(data, dict):
            # Dependiendo de su estructura exacta:
            return float(data.get("price", data.get("vhl", {}).get("price", 0.0)))
            
    except Exception as e:
        print(f"Error en método principal (CriptoDolar): {e}")
        
    # PLAN B: Si el anterior falla, usamos otra API de respaldo (Monedas de Venezuela)
    try:
        backup_url = "https://ve.thesubcurrency.com/api/v1/rates/usdt"
        res = requests.get(backup_url, timeout=20)
        if res.status_code == 200:
            b_data = res.json()
            return float(b_data.get("rate", 0.0))
    except Exception as e:
        print(f"Error en Plan B (Subcurrency): {e}")
        
    return None

def main():
    # 1. Obtener los datos
    bcv = get_bcv_rate()
    paralelo = get_paralelo_rate()
    
    # 2. Validar respuestas
    bcv_val = bcv if bcv is not None else 0.0
    binance_val = paralelo if paralelo is not None and paralelo > 0.0 else 0.0

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

    print(f"Proceso finalizado. BCV: {bcv_val} | Paralelo: {binance_val}")

if __name__ == "__main__":
    main()
