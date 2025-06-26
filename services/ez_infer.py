import requests
import json
import uuid
import websocket
from flask import Flask, request, jsonify
import base64
import urllib.parse
import random
import os # Importa il modulo os per accedere alle variabili d'ambiente
import time # For tracking uptime

app = Flask(__name__)

COMFYUI_API_ADDRESS = "http://127.0.0.1:8188"
REQUEST_TIMEOUT = 3600

# Track when the application started
APP_START_TIME = time.time()

@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint per verificare lo stato del servizio e la connessione a ComfyUI.
    Restituisce l'uptime corrente e lo stato della connessione a ComfyUI.
    """
    current_time = time.time()
    uptime_seconds = current_time - APP_START_TIME
    
    # Convert uptime to human readable format
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    uptime_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    # Test ComfyUI connection
    comfyui_status = "unknown"
    comfyui_error = None
    
    try:
        # Try to reach ComfyUI's system stats endpoint or queue endpoint
        test_endpoint = f"{COMFYUI_API_ADDRESS}/system_stats"
        response = requests.get(test_endpoint, timeout=10)
        if response.status_code == 200:
            comfyui_status = "connected"
        else:
            comfyui_status = "error"
            comfyui_error = f"HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        comfyui_status = "disconnected"
        comfyui_error = "Connection refused"
    except requests.exceptions.Timeout:
        comfyui_status = "timeout"
        comfyui_error = "Request timeout"
    except Exception as e:
        comfyui_status = "error"
        comfyui_error = str(e)
    
    health_data = {
        "status": "healthy",
        "uptime": {
            "seconds": round(uptime_seconds, 2),
            "formatted": uptime_formatted
        },
        "comfyui": {
            "status": comfyui_status,
            "error": comfyui_error
        },
        "service": "ez_infer",
        "timestamp": current_time
    }
    
    # Return appropriate HTTP status based on ComfyUI connection
    status_code = 200 if comfyui_status == "connected" else 503
    
    return jsonify(health_data), status_code

@app.route('/generate', methods=['POST'])
def generate_image():
    """
    Endpoint per generare un'immagine inviando un workflow JSON a ComfyUI.
    Il workflow viene passato nel corpo della richiesta POST.
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    workflow = request.get_json()

    if not workflow:
        return jsonify({"error": "Workflow JSON cannot be empty"}), 400

    # ----- INIZIO MODIFICA PER IL SEED CON CONDIZIONE ENV VAR -----
    # Controlla la variabile d'ambiente RANDOM_SEED_NODES
    random_seed_enabled = os.getenv("INFERENCE_RANDOM_SEED_NODES", "true").lower() == "true"
    print(f"DEBUG: RANDOM_SEED_NODES è impostato a: {random_seed_enabled}")

    if random_seed_enabled:
        seed_found_and_updated = False
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and "inputs" in node_data:
                inputs = node_data["inputs"]
                if "seed" in inputs:
                    # Genera un nuovo seed casuale
                    new_seed = random.randint(0, 0xFFFFFFFFFFFFFFFF) # Un grande numero per seed
                    inputs["seed"] = new_seed
                    seed_found_and_updated = True
                    print(f"DEBUG: Aggiornato seed nel nodo {node_id} a: {new_seed}")
                    
                    # Se c'è anche un campo 'control_after_generate' nel KSampler, impostalo su 'randomize' o 'increment'
                    if "control_after_generate" in inputs:
                        inputs["control_after_generate"] = "randomize"
                        print(f"DEBUG: Impostato control_after_generate nel nodo {node_id} a 'randomize'")
                    break # Assumiamo che ci sia solo un nodo KSampler con seed da modificare
        
        if not seed_found_and_updated:
            print("WARN: RANDOM_SEED_NODES è TRUE ma nessun campo 'seed' valido trovato nel workflow. ComfyUI potrebbe servire dalla cache.")
    else:
        print("DEBUG: RANDOM_SEED_NODES non è TRUE. Il seed nel workflow non verrà modificato automaticamente.")
    # ----- FINE MODIFICA PER IL SEED CON CONDIZIONE ENV VAR -----

    client_id = str(uuid.uuid4())
    prompt_endpoint = f"{COMFYUI_API_ADDRESS}/prompt"
    websocket_address = f"{COMFYUI_API_ADDRESS.replace('http', 'ws')}/ws?clientId={client_id}"

    try:
        payload = {
            "prompt": workflow,
            "client_id": client_id
        }
        print(f"DEBUG: Invio workflow a ComfyUI: {prompt_endpoint}")
        response = requests.post(prompt_endpoint, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        prompt_result = response.json()
        print(f"DEBUG: Prompt Result from ComfyUI: {json.dumps(prompt_result, indent=2)}")

        if "error" in prompt_result:
            print(f"ERROR: Errore da ComfyUI durante l'invio del prompt: {prompt_result}")
            return jsonify({"error": f"ComfyUI prompt error: {prompt_result['error']}"}), 500

        prompt_id = prompt_result.get("prompt_id")
        if not prompt_id:
            return jsonify({"error": "ComfyUI did not return a prompt_id"}), 500

        print(f"DEBUG: Prompt inviato con successo, ID: {prompt_id}. Connessione al websocket...")

        ws_connection = None
        try:
            ws_connection = websocket.create_connection(websocket_address, timeout=REQUEST_TIMEOUT)
            print("DEBUG: Connesso al websocket.")

            final_images = []
            
            while True:
                try:
                    message = ws_connection.recv()
                except websocket.WebSocketTimeoutException:
                    print("WARN: WebSocket recv timed out. Re-attempting recv.")
                    continue
                except websocket.WebSocketConnectionClosedException:
                    print("ERROR: WebSocket connection closed unexpectedly during recv.")
                    break

                if isinstance(message, str):
                    json_message = json.loads(message)
                    msg_type = json_message.get("type")
                    data = json_message.get("data", {})
                    prompt_id_in_msg = data.get("prompt_id")

                    print(f"DEBUG: Raw WS message: {json.dumps(json_message, indent=2)}")

                    if msg_type == "executing" and data.get("node") is None and prompt_id_in_msg == prompt_id:
                        print("DEBUG: Generazione completata (executing: null). Uscita dal loop WebSocket.")
                        break
                    
                    if prompt_id_in_msg == prompt_id:
                        if msg_type == "progress":
                            print(f"DEBUG: Progresso: {data.get('value')}/{data.get('max')} (node: {data.get('node')})")
                        elif msg_type == "executed":
                            node_id = data.get("node")
                            output_data = data.get("output", {})
                            print(f"DEBUG: Nodo '{node_id}' eseguito. Output keys: {output_data.keys()}")
                    elif prompt_id_in_msg is not None:
                        print(f"DEBUG: Ignorando messaggio WS di un altro prompt (type: {msg_type}, prompt_id: {prompt_id_in_msg}).")
                    else:
                        print(f"DEBUG: Messaggio WS globale/senza prompt_id (type: {msg_type}).")

                elif isinstance(message, bytes):
                    print(f"DEBUG: Received binary data of length {len(message)}. Ignoring as we rely on history API for final output.")

            history_endpoint = f"{COMFYUI_API_ADDRESS}/history/{prompt_id}"
            print(f"DEBUG: Recupero history da ComfyUI: {history_endpoint}")
            history_response = requests.get(history_endpoint, timeout=REQUEST_TIMEOUT)
            history_response.raise_for_status()
            history_data = history_response.json()
            print(f"DEBUG: History Data for {prompt_id}: {json.dumps(history_data, indent=2)}")

            if prompt_id not in history_data:
                print(f"ERROR: Prompt ID {prompt_id} not found in history.")
                return jsonify({"error": "Prompt ID not found in history"}), 500

            outputs = history_data[prompt_id].get("outputs", {})
            if not outputs:
                print(f"WARN: Nessun output trovato per il prompt ID {prompt_id} nella history.")
                return jsonify({"message": "Workflow processed, but no outputs found in history.", "history_raw": history_data}), 200

            for node_id, node_output in outputs.items():
                print(f"DEBUG: Processing output for node: {node_id}")
                if "images" in node_output:
                    for image_info in node_output["images"]:
                        filename = image_info["filename"]
                        file_type = image_info["type"]
                        subfolder = image_info.get("subfolder", "")

                        image_url = f"{COMFYUI_API_ADDRESS}/view?filename={urllib.parse.quote(filename)}&type={file_type}"
                        if subfolder:
                             image_url += f"&subfolder={urllib.parse.quote(subfolder)}"
                        
                        print(f"DEBUG: Recupero immagine: {image_url}")
                        try:
                            image_response = requests.get(image_url, timeout=REQUEST_TIMEOUT)
                            image_response.raise_for_status()

                            final_images.append({
                                "filename": filename,
                                "data_base64": base64.b64encode(image_response.content).decode('utf-8'),
                                "type": image_info.get("format", "image/jpeg")
                            })
                            print(f"DEBUG: Immagine '{filename}' aggiunta ai risultati.")
                        except requests.exceptions.RequestException as img_ex:
                            print(f"ERROR: Errore nel recupero dell'immagine '{filename}' da {image_url}: {img_ex}")
                            
            if not final_images:
                print("WARN: Nessuna immagine finale recuperata.")
                return jsonify({"message": "Workflow processed, but no images were retrieved from outputs.", "history_raw": history_data}), 200

            print(f"INFO: Generazione completata. Restituzione {len(final_images)} immagini.")
            return jsonify({"status": "success", "images": final_images, "prompt_id": prompt_id}), 200

        except websocket.WebSocketConnectionClosedException as ws_closed_ex:
            print(f"ERROR: WebSocket connection closed unexpectedly: {ws_closed_ex}")
            return jsonify({"error": f"WebSocket connection closed: {str(ws_closed_ex)}"}), 500
        except Exception as ws_ex:
            print(f"ERROR: Errore durante la comunicazione WebSocket: {ws_ex}")
            return jsonify({"error": f"WebSocket communication error: {str(ws_ex)}"}), 500
        finally:
            if ws_connection:
                print("DEBUG: Chiusura connessione WebSocket.")
                ws_connection.close()


    except requests.exceptions.RequestException as e:
        print(f"ERROR: Errore di rete o HTTP: {e}")
        return jsonify({"error": f"Network or HTTP error: {str(e)}"}), 500
    except json.JSONDecodeError as e:
        print(f"ERROR: Errore di decodifica JSON: {e}")
        return jsonify({"error": f"JSON decoding error: {str(e)}"}), 400
    except Exception as e:
        print(f"FATAL: Errore inatteso: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    print(f"Avvio del server Flask. Ascolto su http://127.0.0.1:5000")
    print(f"Assicurati che ComfyUI sia in esecuzione e accessibile all'indirizzo: {COMFYUI_API_ADDRESS}")
    inference_debug = os.getenv("INFERENCE_DEBUG", "false").lower() == "true"
    app.run(host='127.0.0.1', port=5000, debug=inference_debug)