"""
LLM Manager - PRODUCTION BUILD (No Console Output)
Handles OpenAI API interactions with conversation history
"""

import os
from openai import OpenAI
import tiktoken


class LLMManager:
    def __init__(self, model='gpt-4o', system_prompt='You are a helpful assistant.', max_tokens=8000):
        """Initialize LLM manager with specified model"""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = model
        self.chat_history = []
        self.max_tokens = max_tokens

        if system_prompt:
            self.chat_history.append({
                "role": "system",
                "content": system_prompt
            })

    def count_tokens(self, messages):
        """Count tokens in message list"""
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

    def chat(self, user_message, temperature=0.7, max_response_tokens=500):
        """Send message and get response"""
        if not user_message.strip():
            return ""

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
            error_msg = f"Error getting LLM response: {e}"
            return error_msg

    def chat_with_vision(self, user_message, image_url=None, temperature=0.7, max_response_tokens=500):
        """Send message with optional image for vision models"""
        if not user_message.strip():
            return ""

        vision_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']
        supports_vision = self.model in vision_models

        if not supports_vision and image_url:
            return self.chat(user_message, temperature, max_response_tokens)

        if image_url and supports_vision:
            content = [
                {
                    "type": "text",
                    "text": user_message
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                        "detail": "high"
                    }
                }
            ]
        else:
            content = user_message

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
        model='gpt-4o',
        system_prompt='You are a friendly AI named Bob.'
    )

    print("Testing LLM Manager...")
    response = llm.chat("Hello! What's your name?")
    print(f"Response: {response}")

    response = llm.chat("What can you help me with?")
    print(f"Response: {response}")

    print(f"\nConversation has {len(llm.chat_history)} messages")
    print(f"Total tokens: {llm.count_tokens(llm.chat_history)}")