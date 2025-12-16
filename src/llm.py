import re
from typing import Any
import httpx
from src.config import OLLAMA_MODEL, OLLAMA_URL
from src.schemas import QuerySpec

async def query_spec_call_llm(system_prompt: str, user_message: str) -> QuerySpec:
        async with httpx.AsyncClient(timeout=45) as client:
            payload: dict[str, Any] = {
                "model": OLLAMA_MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "format": "json",
            }
            r = await client.post(OLLAMA_URL, json=payload)
            r.raise_for_status()
            response_json = r.json()
            
            # Handle both Ollama native API and OpenAI-compatible API formats
            if "choices" in response_json:
                # OpenAI-compatible format: /v1/chat/completions
                content = response_json["choices"][0]["message"]["content"]
            else:
                # Ollama native format: /api/chat
                content = response_json["message"]["content"]
            
            m = re.search(r"\{.*\}", content, flags=re.S)
            if not m:
                raise ValueError("No JSON found in Ollama output")
            
            import json
            response_data = json.loads(m.group(0))
            print(f"DEBUG - LLM raw JSON response:\n{json.dumps(response_data, indent=2)}")
            
            # Extract the nested query structure
            query_data = response_data.get("query", {})
            
            # Merge is_banking_domain from top level
            query_data["is_banking_domain"] = response_data.get("is_banking_domain")
            
            # Fix TimeRange - must update query_data dict directly
            time_range = query_data.get("time_range")
            if time_range is not None:  # Only process if time_range is provided
                if time_range.get("mode") == "relative" and (not time_range.get("last") or not time_range.get("unit")):
                    # Set defaults for relative mode
                    time_range["last"] = 180
                    time_range["unit"] = "days"
                    query_data["time_range"] = time_range  # Update the dict
            
            # Fix params if it's a string instead of dict
            if isinstance(query_data.get("params"), str):
                try:
                    query_data["params"] = json.loads(query_data["params"])
                except:
                    query_data["params"] = {}
            
            print(f"DEBUG - query_data before validation:\n{json.dumps(query_data, indent=2)}")
            try:
                return QuerySpec.model_validate(query_data)
            except Exception as validation_error:
                print(f"DEBUG - QuerySpec validation failed: {validation_error}")
                raise