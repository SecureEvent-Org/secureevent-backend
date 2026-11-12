import time
import statistics
import requests

URL = "http://127.0.0.1:8000/api/v1/auth/verify-gate"
IMAGE_PATH = "laura.jpeg"  
NUM_REQUESTS = 25          # Número de validaciones consecutivas a simular

def run_load_test():
    latencies_ms = []
    success_count = 0

    print(f"Iniciando prueba de carga unitaria ({NUM_REQUESTS} peticiones) hacia {URL}...\n")

    for i in range(1, NUM_REQUESTS + 1):
        start_time = time.perf_counter()
        try:
            with open(IMAGE_PATH, "rb") as img_file:
                files = {"file": (IMAGE_PATH, img_file, "image/jpeg")}
                response = requests.post(URL, files=files)
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            latencies_ms.append(elapsed_ms)

            if response.status_code == 200:
                data = response.json()
                success_count += 1
                print(f"Petición #{i:02d} | HTTP 200 | Acceso: {data['access']:7s} | "
                      f"Similitud: {data['similarity_percentage']}% | Latencia total: {elapsed_ms:.2f} ms")
            else:
                print(f"Petición #{i:02d} | ERROR HTTP {response.status_code}")

        except Exception as e:
            print(f"Petición #{i:02d} | Excepción: {e}")

    if latencies_ms:
        print("\n--- RESUMEN DE MÉTRICAS DE RENDIMIENTO (TAREA 1.14) ---")
        print(f"Peticiones exitosas : {success_count}/{NUM_REQUESTS}")
        print(f"Latencia promedio   : {statistics.mean(latencies_ms):.2f} ms")
        print(f"Latencia mínima     : {min(latencies_ms):.2f} ms")
        print(f"Latencia máxima     : {max(latencies_ms):.2f} ms")
        print(f"Cumple RNF (<2000ms): {'SÍ' if statistics.mean(latencies_ms) < 2000 else 'NO'}")

if __name__ == "__main__":
    run_load_test()