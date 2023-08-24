from flask import Flask, jsonify, request
import uuid
from time import sleep
import threading
import os
import openai
from apscheduler.schedulers.background import BackgroundScheduler



app = Flask(__name__)




# Dictionary to store status and completion by token
operations = {}

def clear_completed_operations():
    tokens_to_remove = [token for token, operation in operations.items() if operation['status'] == 'complete']
    for token in tokens_to_remove:
        del operations[token]

scheduler = BackgroundScheduler()
scheduler.add_job(clear_completed_operations, 'interval', seconds=60)
scheduler.start()



@app.route('/')
def index():
    return jsonify(operations)

# Simulated function that represents sending the prompt to OpenAI and getting the completion
def process_prompt(token, prompt):
    sleep(60)  # Simulate processing time
    completion = "Generated completion for: " + prompt
    operations[token]['status'] = 'complete'
    operations[token]['completion'] = completion



@app.route('/send-prompt', methods=['POST'])
def send_prompt():
    prompt_data = request.json
    prompt = prompt_data.get('prompt')
    if prompt is None:
        return jsonify({"msg": "Prompt is required"}), 400

    token = str(uuid.uuid4())
    operations[token] = {"status": "pending", "completion": None}

    # Start a new thread to process the prompt (you might want to use a task queue like Celery in production)
    threading.Thread(target=process_prompt, args=(token, prompt)).start()

    return jsonify({"token": token}), 202



@app.route('/check-completion', methods=['GET'])
def check_completion():
    token = request.args.get('token')
    if token not in operations:
        return jsonify({"msg": "Invalid token"}), 400

    return jsonify(operations[token])



if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
