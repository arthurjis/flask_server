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
from datetime import datetime, timedelta


load_dotenv()



app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

# Dictionary to store status and completion by token
operations = {}
 

# Clear operations 
def clear_completed_operations():
    if not len(operations):
        return

    tokens_to_remove = [token for token, operation in operations.items() if operation['status'] == 'complete' and datetime.utcnow() - operation['completion_time'] > timedelta(hours=1)]
    for token in tokens_to_remove:
        del operations[token]['completion']
        operations[token]['status'] = 'expired'
    app.logger.info(f'Cleared {len(tokens_to_remove)} completed operations')

scheduler = BackgroundScheduler()
scheduler.add_job(clear_completed_operations, 'interval', seconds=3600)
scheduler.start()



@app.route('/operations')
def index():
    return jsonify(operations)




# Sending the prompt to OpenAI and getting the completion
def process_prompt_list(token, prompt_list, retries=1):

    if not prompt_list:
        operations[token]['status'] = 'failed'
        operations[token]['error_msg'] = 'Empty prompt list'

    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    response_list = []
    current_step = 0

    for prompt in prompt_list:
        current_step += 1
        operations[token]['current_step'] = current_step
        messages.append({"role": "user", "content": prompt['prompt_string']})

        # Retry logic starts here
        for attempt in range(retries + 1):
            try:
                response = openai.ChatCompletion.create(
                    model=prompt['model'],
                    messages=messages,
                    max_tokens=prompt['max_tokens'],
                    temperature=prompt['temperature'],
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
    try:
        operations[token]['status'] = 'complete'
        operations[token]['completion'] = response['choices'][0]['message']['content']
        operations[token]['usage'] = usage
        operations[token]['completion_time'] = datetime.utcnow()
        app.logger.info(f"Completed generate for token {token}")

    except KeyError as e:
        operations[token]['status'] = 'failed'
        operations[token]['error_msg'] = f"Missing fields in response: {e}, {response}"
        return



@app.route('/generate', methods=['POST'])
def generate():
    payload = request.json
    form = payload.get('form', None)

    if form is None:
        return jsonify({"msg": "Missing form in payload..."}), 400

    filled_prompts, missing_placeholders, class_type = fetch_prompt_list_and_fill_placeholders_with(form)

    if not filled_prompts or not class_type:
        return jsonify({"msg": "Bad class type..."}), 400
    
    token = str(uuid.uuid4())
    
    operations[token] = {"type": class_type, "num_steps": len(filled_prompts), "current_step": 0, "status": "pending", "completion": None, "start_time": datetime.utcnow()}

    # Start a new thread to process the prompt (you might want to use a task queue like Celery in production)
    threading.Thread(target=process_prompt_list, args=(token, filled_prompts)).start()

    return jsonify({"class_type": class_type, "token": token, "num_steps": len(filled_prompts), "missing_placeholders": missing_placeholders}), 202



@app.route('/check-completion', methods=['GET'])
def check_completion():
    token = request.args.get('token')
    if token not in operations:
        return jsonify({"msg": "Invalid token"}), 400

    return jsonify(operations[token])



if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
