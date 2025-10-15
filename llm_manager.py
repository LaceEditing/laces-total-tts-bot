import os
from openai import OpenAI
from groq import Groq
import tiktoken


class LLMManager:
    def __init__(self, model='gpt-4o', system_prompt='You are a helpful assistant.', max_tokens=8000):
        """Initialize LLM manager with specified model (OpenAI or Groq)"""
        self.model = model
        self.chat_history = []
        self.max_tokens = max_tokens

        # Determine if using Groq or OpenAI
        self.is_groq = (model.startswith('llama') or
                        model.startswith('mixtral') or
                        model.startswith('gemma') or
                        model.startswith('qwen') or
                        model.startswith('moonshotai') or
                        model.startswith('openai/'))

        if self.is_groq:
            self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        else:
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        if system_prompt:
            self.chat_history.append({
                "role": "system",
                "content": system_prompt
            })

    def count_tokens(self, messages):
        """Count tokens in message list"""
        if self.is_groq:
            # Rough estimate for Groq models
            total = 0
            for msg in messages:
                content = msg.get('content', '')
                if isinstance(content, str):
                    total += len(content.split()) * 1.3  # Rough token estimate
                elif isinstance(content, list):
                    for item in content:
                        if item.get("type") == "text":
                            total += len(item.get("text", "").split()) * 1.3
            return int(total)

        try:
            encoding = tiktoken.encoding_for_model(self.model)
            num_tokens = 0
            for message in messages:
                num_tokens += 4
                for key, value in message.items():
                    if key == "content":
                        if isinstance(value, list):
                            for item in value:
                                if item.get("type") == "text":
                                    num_tokens += len(encoding.encode(item.get("text", "")))
                                elif item.get("type") == "image_url":
                                    num_tokens += 255
                        else:
                            num_tokens += len(encoding.encode(str(value)))
                    else:
                        num_tokens += len(encoding.encode(str(value)))
                        if key == "name":
                            num_tokens += -1
            num_tokens += 2
            return num_tokens
        except Exception:
            return 0

    def manage_context(self):
        """Trim old messages if context is too long"""
        while self.count_tokens(self.chat_history) > self.max_tokens:
            if len(self.chat_history) > 1:
                self.chat_history.pop(1)
            else:
                break

    def chat(self, user_message, temperature=0.7, max_response_tokens=150, image_path=None):
        """Send a message and get response"""

        # Handle vision for OpenAI only
        if image_path and not self.is_groq:
            return self.chat_with_vision(user_message, image_path, temperature, max_response_tokens)

        # Regular text chat
        self.chat_history.append({
            "role": "user",
            "content": user_message
        })

        self.manage_context()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.chat_history,
                temperature=temperature,
                max_tokens=max_response_tokens
            )

            assistant_message = response.choices[0].message.content

            self.chat_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            error_msg = f"Error getting response: {e}"
            return error_msg

    def chat_with_vision(self, user_message, image_path, temperature=0.7, max_response_tokens=150):
        """Send message with image (OpenAI only)"""
        if self.is_groq:
            return "Vision not supported with Groq models. Use OpenAI GPT-4o for vision."

        import base64

        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        content = [
            {
                "type": "text",
                "text": user_message
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            }
        ]

        self.chat_history.append({
            "role": "user",
            "content": content
        })

        self.manage_context()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.chat_history,
                temperature=temperature,
                max_tokens=max_response_tokens
            )

            assistant_message = response.choices[0].message.content

            self.chat_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            error_msg = f"Error getting vision response: {e}"
            return error_msg

    def reset_conversation(self, system_prompt=None):
        """Reset conversation history"""
        self.chat_history = []
        if system_prompt:
            self.chat_history.append({
                "role": "system",
                "content": system_prompt
            })

    def set_model(self, model):
        """Change the LLM model"""
        self.model = model
        self.is_groq = model.startswith('llama') or model.startswith('mixtral') or model.startswith('gemma')

        if self.is_groq:
            self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        else:
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def set_system_prompt(self, prompt):
        """Update system prompt"""
        if self.chat_history and self.chat_history[0]["role"] == "system":
            self.chat_history[0]["content"] = prompt
        else:
            self.chat_history.insert(0, {
                "role": "system",
                "content": prompt
            })

    def get_history(self):
        """Get current conversation history"""
        return self.chat_history.copy()

    def load_history(self, history):
        """Load conversation history"""
        self.chat_history = history.copy()


if __name__ == '__main__':
    # Test the LLM manager
    llm = LLMManager(
        model='llama-3.1-8b-instant',
        system_prompt='You are a friendly AI named Bob.'
    )

    print(llm.chat("Hello! How are you?"))