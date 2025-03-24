from ollama import Client
import logging
from .config import ChatConfig

class ChatModel:
    def __init__(self):
        self.client = Client(
            host=ChatConfig.OLLAMA_HOST,
            headers=ChatConfig.OLLAMA_HEADERS
        )
        self.conversation_history = []

    def get_response(self, message, conversation_history, image_path=None):
        """Get response from the Ollama model"""
        try:
            messages = conversation_history + [{
                'role': 'user',
                'content': 'You are Medical expert, analyze image and give short concise responses with accurate data, provide links related to the issues. Do not hallucinate',
                'images': [image_path] if image_path else []
            }]

            response = self.client.chat(model='llama3.2-vision:11b', messages=messages)
            return response['message']['content']
        except Exception as e:
            logging.error(f"Model error: {str(e)}")
            raise
