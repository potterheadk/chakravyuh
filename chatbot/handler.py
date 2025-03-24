from flask import Blueprint, render_template, request, jsonify
import logging
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import json
from .config import ChatConfig
from .model import ChatModel

# Initialize config
ChatConfig.setup()

# Create blueprint
chat_blueprint = Blueprint('chat', __name__)
chat_model = ChatModel()


def save_image(file):
    """Handle image upload"""
    if not file or not file.filename:
        return None

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_dir = os.path.join(ChatConfig.UPLOAD_FOLDER, timestamp)
        os.makedirs(image_dir, exist_ok=True)

        filename = secure_filename(file.filename)
        image_path = os.path.join(image_dir, filename)
        file.save(image_path)
        logging.info(f"Saved image to: {image_path}")
        return image_path
    except Exception as e:
        logging.error(f"Error saving image: {str(e)}")
        raise


@chat_blueprint.route('/chatbot')
def chatbot():
    """Render the main chat interface"""
    return render_template('chatbot.html')


@chat_blueprint.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages and image uploads"""
    try:
        message = request.form.get('message')
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        # Handle image upload
        image_path = None
        if 'image' in request.files:
            image_path = save_image(request.files['image'])

        # Parse conversation history
        try:
            conversation_history = json.loads(request.form.get('conversation_history', '[]'))
        except json.JSONDecodeError:
            conversation_history = []

        # Get model response
        response_text = chat_model.get_response(
            message,
            conversation_history + chat_model.conversation_history,
            image_path
        )

        # Update conversation history
        chat_model.conversation_history += [
            {'role': 'user', 'content': message, 'images': [image_path] if image_path else []},
            {'role': 'assistant', 'content': response_text}
        ]

        # Prepare response
        response_data = {
            'response': response_text,
            'status': 'success',
            'conversation_history': chat_model.conversation_history
        }

        if image_path:
            response_data['image_path'] = image_path

        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': str(e) if chat_blueprint.debug else 'An error occurred processing your request',
            'status': 'error'
        }), 500


@chat_blueprint.errorhandler(413)
def request_entity_too_large(error):
    """Handle oversized file uploads"""
    return jsonify({'error': 'File too large. Maximum size is 16MB'}),