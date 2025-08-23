import asyncio
import logging
from typing import Optional
import requests
import json


class UniversalMessageProcessor:
    """Processes messages using various AI providers with smart summarization."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-pro", provider: str = "gemini", base_url: str = ""):
        self.api_key = api_key
        self.model_name = model_name
        self.provider = provider.lower()
        self.base_url = base_url
        
        # Default prompt for caption summarization (600-800 characters)
        self.summarization_template = """
        لطفاً متن زیر را به صورت خلاصه و حرفه‌ای در زبان فارسی بازنویسی کنید. متن باید بین 600 تا 800 کاراکتر باشد، واضح، دقیق و مناسب برای انتشار در کانال تلگرام باشد. نکات مهم و اصلی را حفظ کنید:

        متن اصلی: {original_text}

        لطفاً فقط متن بازنویسی شده را ارائه دهید.
        """
        
        # Original template for full processing
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
        """Process a message using the configured AI provider with smart template selection."""
        try:
            # Choose appropriate template based on text length and custom prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                text_length = len(message_text) if message_text else 0
                if text_length > 800:
                    # Use summarization template for long texts
                    prompt = self.summarization_template
                else:
                    # Use regular template for shorter texts
                    prompt = self.prompt_template
            
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
                
                # Ensure total length doesn't exceed Telegram limits
                final_text = response + footer
                
                # If it's a caption (with media), limit to 1020 characters (leaving space for "...")
                # For text messages, limit to 4090 characters
                if len(final_text) > 1020:
                    # This is likely a caption, so summarize more aggressively
                    if len(response) > 800:
                        # Try to re-process with more aggressive summarization
                        aggressive_prompt = """
                        لطفاً متن زیر را به صورت بسیار خلاصه و مختصر در زبان فارسی بازنویسی کنید. متن نهایی باید حداکثر 700 کاراکتر باشد و نکات کلیدی را حفظ کند:

                        متن اصلی: {original_text}

                        لطفاً فقط متن خلاصه شده را ارائه دهید.
                        """
                        formatted_aggressive_prompt = aggressive_prompt.format(original_text=message_text)
                        
                        if self.provider == "gemini":
                            shorter_response = await self._process_gemini(formatted_aggressive_prompt)
                        elif self.provider == "openai":
                            shorter_response = await self._process_openai(formatted_aggressive_prompt)
                        elif self.provider == "openrouter":
                            shorter_response = await self._process_openrouter(formatted_aggressive_prompt)
                        
                        if shorter_response:
                            final_text = shorter_response + footer
                            if len(final_text) <= 1020:
                                return final_text
                    
                    # If still too long, truncate
                    max_response_length = 1020 - len(footer) - 3  # Leave space for "..."
                    if len(response) > max_response_length:
                        response = response[:max_response_length] + "..."
                    final_text = response + footer
                
                return final_text
            
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