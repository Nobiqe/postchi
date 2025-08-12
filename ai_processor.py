import asyncio
import logging
from typing import Optional
import requests
import json


class UniversalMessageProcessor:
    """Processes messages using various AI providers."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-pro", provider: str = "gemini", base_url: str = ""):
        self.api_key = api_key
        self.model_name = model_name
        self.provider = provider.lower()
        self.base_url = base_url
        
        self.prompt_template = """
        لطفاً متن زیر را به صورت رسمی و حرفه‌ای در زبان فارسی بازنویسی کنید. متن باید واضح، دقیق و مناسب برای انتشار در کانال تلگرام باشد:

        متن اصلی: {original_text}

        لطفاً فقط متن بازنویسی شده را ارائه دهید.
        """
        
        # Initialize based on provider
        if self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
    
    async def process_message(self, message_text: str, custom_prompt: Optional[str] = None, custom_footer: Optional[str] = None) -> Optional[str]:
        """Process a message using the configured AI provider."""
        try:
            prompt = custom_prompt or self.prompt_template
            formatted_prompt = prompt.format(original_text=message_text)
            
            if self.provider == "gemini":
                response = await self._process_gemini(formatted_prompt)
            elif self.provider == "openai":
                response = await self._process_openai(formatted_prompt)
            elif self.provider == "openrouter":
                response = await self._process_openrouter(formatted_prompt)
            else:
                logging.error(f"Unsupported provider: {self.provider}")
                return None
            
            if response:
                # Use custom footer or default
                footer = custom_footer or ""
                
                return response + footer
            
            return None
            
        except Exception as e:
            logging.error(f"Error processing message with {self.provider}: {e}")
            return None


    async def _process_gemini(self, prompt: str) -> Optional[str]:
        """Process with Gemini."""
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text.strip()
        except Exception as e:
            logging.error(f"Gemini processing error: {e}")
            return None
    
    async def _process_openai(self, prompt: str) -> Optional[str]:
        """Process with OpenAI."""
        try:
            url = self.base_url or "https://api.openai.com/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            }
            
            response = await asyncio.to_thread(requests.post, url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                logging.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"OpenAI processing error: {e}")
            return None
    
    async def _process_openrouter(self, prompt: str) -> Optional[str]:
        """Process with OpenRouter."""
        try:
            if self.base_url.endswith('/chat/completions'):
                url = self.base_url
            elif self.base_url.endswith('/v1'):
                url = f"{self.base_url}/chat/completions"
            else:
                url = f"{self.base_url}/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-repo",  # Optional
                "X-Title": "Telegram Channel Processor"  # Optional
            }
            
            data = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = await asyncio.to_thread(requests.post, url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                logging.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                print(f"API Response: {response.text}")  # Add this line for debugging
                return None
                
        except Exception as e:
            logging.error(f"OpenRouter processing error: {e}")
            return None