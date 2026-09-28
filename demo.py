import json

from fastapi.testclient import TestClient

from ai_platform.app import create_app

if __name__ == "__main__":
    with TestClient(create_app()) as client:
        response = client.post(
            "/v1/infer",
            json={
                "tenant": "demo",
                "region": "us",
                "prompt": "Summarize a synthetic system.",
                "max_output_tokens": 32,
            },
        )
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
