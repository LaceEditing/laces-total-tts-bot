"""
LLM Manager - Handles OpenAI API interactions
Supports multiple GPT models with conversation history
FIXED: Vision model checking and token counting for vision messages
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
        self.max_tokens = max_tokens  # User-configurable context limit

        # Add system prompt
        if system_prompt:
            self.chat_history.append({
                "role": "system",
                "content": system_prompt
            })

    def count_tokens(self, messages):
        """Count tokens in message list - FIXED to handle vision messages correctly"""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
            num_tokens = 0
            for message in messages:
                num_tokens += 4  # Message formatting overhead
                for key, value in message.items():
                    if key == "content":
                        # Handle both string and list content (for vision messages)
                        if isinstance(value, list):
                            # Vision message - approximate token count
                            for item in value:
                                if item.get("type") == "text":
                                    num_tokens += len(encoding.encode(item.get("text", "")))
                                elif item.get("type") == "image_url":
                                    # Images use approximately 85-255 tokens depending on detail
                                    # Using high detail, approximate 255 tokens
                                    num_tokens += 255
                        else:
                            # Regular text message
                            num_tokens += len(encoding.encode(str(value)))
                    else:
                        num_tokens += len(encoding.encode(str(value)))
                        if key == "name":
                            num_tokens += -1
            num_tokens += 2  # Assistant reply priming
            return num_tokens
        except Exception as e:
            print(f"[LLM] Token counting error: {e}")
            # Return a safe default to avoid breaking context management
            return 0

    def manage_context(self):
        """Trim old messages if context is too long"""
        while self.count_tokens(self.chat_history) > self.max_tokens:
            if len(self.chat_history) > 1:
                # Keep system message, remove oldest user/assistant message
                self.chat_history.pop(1)
            else:
                break

    def chat(self, user_message, temperature=0.7, max_response_tokens=500):
        """Send message and get response"""
        if not user_message.strip():
            return ""

        # Add user message to history
        self.chat_history.append({
            "role": "user",
            "content": user_message
        })

        # Manage context length
        self.manage_context()

        try:
            # Get completion from OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.chat_history,
                temperature=temperature,
                max_tokens=max_response_tokens
            )

            # Extract response
            assistant_message = response.choices[0].message.content

            # Add to history
            self.chat_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            error_msg = f"Error getting LLM response: {e}"
            print(error_msg)
            return error_msg

    def chat_with_vision(self, user_message, image_url=None, temperature=0.7):
        """Send message with optional image for vision models - FIXED vision checking"""
        if not user_message.strip():
            return ""

        # FIXED: Use exact model matching for vision support
        vision_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']
        supports_vision = self.model in vision_models  # EXACT match

        print(f"[LLM] Model: {self.model}, Vision support: {supports_vision}, Has image: {bool(image_url)}")

        if not supports_vision and image_url:
            print(f"[LLM] WARNING: {self.model} doesn't support vision. Falling back to text-only.")
            return self.chat(user_message, temperature)

        # Create message content with image
        if image_url and supports_vision:
            print(f"[LLM] Formatting vision request with image (length: {len(image_url)})")
            # Ensure proper format for vision API
            content = [
                {
                    "type": "text",
                    "text": user_message
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                        "detail": "high"  # Request high detail analysis
                    }
                }
            ]
        else:
            content = user_message

        # Add user message to history
        self.chat_history.append({
            "role": "user",
            "content": content
        })

        # Manage context
        self.manage_context()

        try:
            print(f"[LLM] Sending request to OpenAI API...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.chat_history,
                temperature=temperature,
                max_tokens=500
            )

            assistant_message = response.choices[0].message.content
            print(f"[LLM] Received response: {assistant_message[:100]}...")

            self.chat_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"Error getting vision response: {e}"
            print(f"[LLM] {error_msg}")
            print(f"[LLM] Full traceback: {error_details}")
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