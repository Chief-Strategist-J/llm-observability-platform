import requests
import os
from pathlib import Path

class ChatController:
    def __init__(self, api_base_url=None):
        self.api_base_url = api_base_url or os.getenv("API_BASE_URL", "http://localhost:8000")

    def check_health(self):
        try:
            response = requests.get(f"{self.api_base_url}/health")
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"API Error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Connection Error: {str(e)}"}

    def get_download_progress(self):
        try:
            cache_path = Path.home() / ".cache" / "huggingface" / "hub" / "models--google--gemma-2-2b-it"
            if cache_path.exists():
                size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
                return {"success": True, "size_gb": size / (1024**3)}
            else:
                return {"success": False, "message": "Model cache not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_message(self, prompt, params):
        try:
            response = requests.post(
                f"{self.api_base_url}/v1/chat/completions",
                json={
                    "prompt": prompt,
                    **params
                },
                timeout=300
            )
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "content": content}
            else:
                return {"success": False, "error": f"Error: {response.status_code} - {response.text}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out. The model might still be downloading."}
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}

    def stream_message(self, prompt, params):
        try:
            params["stream"] = True
            response = requests.post(
                f"{self.api_base_url}/v1/chat/completions",
                json={
                    "prompt": prompt,
                    **params
                },
                stream=True,
                timeout=300
            )
            
            if response.status_code == 200:
                import json
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except:
                                continue
            else:
                yield f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            yield f"Error: {str(e)}"
