from flask import Flask, jsonify, request
import uuid
import threading
import os
import openai
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from utils import *
from prompt_templates import fetch_prompt_list_and_fill_placeholders_with
from dotenv import load_dotenv
import time

load_dotenv()



app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

# Dictionary to store status and completion by token
operations = {}
 

# Clear operations 
def clear_completed_operations():
    if not len(operations):
        return

    tokens_to_remove = [token for token, operation in operations.items() if operation['status'] == 'complete']
    for token in tokens_to_remove:
        del operations[token]
    app.logger.info(f'Cleared {len(tokens_to_remove)} completed operations')

scheduler = BackgroundScheduler()
scheduler.add_job(clear_completed_operations, 'interval', seconds=3600)
scheduler.start()



@app.route('/operations')
def index():
    return jsonify(operations)




# Sending the prompt to OpenAI and getting the completion
def process_prompt_list(token, prompt_list, model, temperature, max_token, retries=1):

    # app.logger.debug(f"Begin generate for token {token}")

    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    response_list = []
    current_step = 0

    for prompt in prompt_list:
        current_step += 1
        operations[token]['current_step'] = current_step
        messages.append({"role": "user", "content": prompt})

        # Retry logic starts here
        for attempt in range(retries + 1):
            try:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_token,
                    temperature=temperature,
                )
                messages.append(dict(response['choices'][0]['message']))
                response_list.append(response)
                break

            except Exception as e:
                if attempt < retries:
                    time.sleep(1)
                else:
                    operations[token]['status'] = 'failed'
                    operations[token]['error_msg'] = str(e)
                    return

    # Calculate usage in USD
    usage = 0
    for i in response_list:
        try:
            usage += i['usage']['completion_tokens'] * 2e-5 + i['usage']['prompt_tokens'] * 1.5e-5
        except KeyError:
            continue

    completion = {
        "message": response['choices'][0]['message']['content'],
        "usage": usage
    }

    operations[token]['status'] = 'complete'
    operations[token]['completion'] = completion
    
    app.logger.info(f"Completed generate for token {token}")



@app.route('/generate', methods=['POST'])
def generate():
    payload = request.json
    form = payload.get('form', None)
    model = payload.get('model', 'gpt-3.5-turbo')
    temperature = get_float_value(payload, 'temperature', 0.7)
    max_token = get_int_value(payload, 'max_token', 1024)

    if form is None:
        return jsonify({"msg": "Missing form in payload..."}), 400

    filled_prompts, missing_placeholders, class_type = fetch_prompt_list_and_fill_placeholders_with(form)

    token = str(uuid.uuid4())
    operations[token] = {"type": class_type, "num_steps": len(filled_prompts), "current_step": 0, "status": "pending", "completion": None}

    # Start a new thread to process the prompt (you might want to use a task queue like Celery in production)
    threading.Thread(target=process_prompt_list, args=(token, filled_prompts, model, temperature, max_token)).start()

    return jsonify({"class_type": class_type, "token": token, "num_steps": len(filled_prompts), "missing_placeholders": missing_placeholders}), 202



@app.route('/check-completion', methods=['GET'])
def check_completion():
    token = request.args.get('token')
    if token not in operations:
        return jsonify({"msg": "Invalid token"}), 400

    return jsonify(operations[token])



if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
