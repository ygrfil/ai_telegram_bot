from typing import Optional, List, Dict, Any, AsyncGenerator
import base64
import json
import aiohttp
import logging
from .base import BaseAIProvider
from ...config import Config
import asyncio

logger = logging.getLogger(__name__)

class GeminiProvider(BaseAIProvider):
    """Google Gemini API provider implementation."""

    def __init__(self, api_key: str, config: Config | None = None) -> None:
        """Initialize Gemini provider with API key and config."""
        super().__init__(api_key, config)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "models/gemini-pro"  # Default model
        self.vision_model = "models/gemini-pro-vision"  # Vision-capable model
        self._user_config = config
        logger.info(f"GeminiProvider initialized")

    async def chat_completion_stream(
        self,
        message: str,
        model_config: Dict[str, Any],
        history: List[Dict[str, Any]] | None = None,
        image: bytes | None = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming chat completion response from Google Gemini API."""
        try:
            # Determine if we're using the vision model
            has_vision = bool(model_config.get("vision", False) and image)
            active_model = self.vision_model if has_vision else self.model
            
            # Set the specific model version if provided in model_config
            if "name" in model_config and "gemini" in model_config["name"].lower():
                # Extract model version (e.g., "google/gemini-2.5-pro-preview-03-25" -> "gemini-2.5-pro")
                model_parts = model_config["name"].split("/")[-1].split("-")
                if len(model_parts) >= 2:
                    base_model = f"gemini-{model_parts[1]}-pro"
                    active_model = f"models/{base_model}"
                    if has_vision:
                        active_model = f"models/{base_model}-vision"

            # Build the API URL
            endpoint = f"{self.base_url}/{active_model}:streamGenerateContent"
            
            # Process the history to format compatible with Gemini
            formatted_history = []
            if history:
                for msg in history:
                    if not isinstance(msg, dict) or not all(k in msg for k in ["role", "content"]):
                        continue
                        
                    # Map OpenAI/standard roles to Gemini roles
                    role_map = {
                        "user": "user",
                        "assistant": "model",
                        "system": "user"  # Gemini doesn't have a direct system role
                    }
                    
                    role = role_map.get(msg["role"])
                    if not role:
                        continue
                        
                    content = msg["content"]
                    if isinstance(content, str) and content.strip():
                        formatted_history.append({
                            "role": role,
                            "parts": [{"text": content}]
                        })
            
            # Add system prompt as a user message at the beginning if not already present
            system_prompt = self._get_system_prompt(model_config["name"])
            if system_prompt and not any(msg.get("role") == "user" and 
                                        "parts" in msg and 
                                        any(part.get("text", "").startswith("You are") for part in msg["parts"]) 
                                        for msg in formatted_history[:1]):
                formatted_history.insert(0, {
                    "role": "user",
                    "parts": [{"text": system_prompt}]
                })
                
                # Add a model response to acknowledge the system prompt
                formatted_history.insert(1, {
                    "role": "model",
                    "parts": [{"text": "I understand and will follow these guidelines."}]
                })
            
            # Prepare the current message
            current_message = {
                "role": "user",
                "parts": []
            }
            
            # Add text content
            if message:
                current_message["parts"].append({"text": message})
                
            # Add image if provided and using vision model
            if image and has_vision:
                # Encode image to base64
                image_b64 = base64.b64encode(image).decode("utf-8")
                current_message["parts"].append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_b64
                    }
                })
            
            # Construct the request payload
            payload = {
                "contents": formatted_history + [current_message],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.95,
                    "topK": 40,
                    "maxOutputTokens": model_config.get("max_output_tokens", 2048),
                    "stopSequences": []
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{endpoint}?key={self.api_key}",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Gemini API error: {response.status} - {error_text}")
                        
                        # Yield a user-friendly error message
                        if response.status == 400:
                            yield "Sorry, I couldn't process that request. It might contain content that can't be handled."
                        elif response.status == 403:
                            yield "API access error. Please check your Gemini API key."
                        elif response.status == 429:
                            yield "The Gemini API rate limit has been reached. Please try again later."
                        else:
                            yield f"Error communicating with Gemini API (HTTP {response.status})."
                        return
                    
                    # Process streaming response
                    buffer = ""
                    async for line in response.content:
                        buffer += line.decode("utf-8")
                        
                        # Process complete JSON objects
                        while "\n" in buffer:
                            line_text, buffer = buffer.split("\n", 1)
                            if not line_text.strip():
                                continue
                                
                            try:
                                data = json.loads(line_text)
                                if "candidates" in data and data["candidates"]:
                                    candidate = data["candidates"][0]
                                    if "content" in candidate and "parts" in candidate["content"]:
                                        for part in candidate["content"]["parts"]:
                                            if "text" in part:
                                                yield part["text"]
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse JSON: {line_text}")
                                continue
                            except Exception as e:
                                logger.error(f"Error processing response chunk: {e}")
                                continue
                    
                    # Process any remaining buffer
                    if buffer.strip():
                        try:
                            data = json.loads(buffer)
                            if "candidates" in data and data["candidates"]:
                                candidate = data["candidates"][0]
                                if "content" in candidate and "parts" in candidate["content"]:
                                    for part in candidate["content"]["parts"]:
                                        if "text" in part:
                                            yield part["text"]
                        except Exception as e:
                            logger.error(f"Error processing final response chunk: {e}")
            
        except aiohttp.ClientError as e:
            logger.error(f"Network error with Gemini API: {e}")
            yield "Network error occurred while connecting to Gemini API."
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for Gemini API response")
            yield "The request to Gemini API timed out. Please try again."
        except Exception as e:
            logger.error(f"Unexpected error in Gemini provider: {e}")
            yield "An unexpected error occurred while processing your request."