import requests
import time
import threading

URL = "https://miqueiassoarescardoso.github.io/obmepemgraficos/resultados.html"  # Substitua pela URL correta

def keep_alive():
    while True:
        try:
            response = requests.get(URL)
            print(f"Ping feito: {response.status_code}")
        except Exception as e:
            print(f"Erro ao fazer ping: {e}")
        time.sleep(20)  # Faz uma requisição a cada 5 minutos

# Rodar em uma thread separada
thread = threading.Thread(target=keep_alive, daemon=True)
thread.start()
