from flask import Flask, jsonify, request
import threading
import os
import logging
from utils import *
from prompt_templates import fetch_prompt_list_and_fill_placeholders_with
from dotenv import load_dotenv
from datetime import datetime
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from prompt_worker import process_prompt_list



load_dotenv()


app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

try:
    mongo_uri = os.getenv('MONGO_URL')
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client['data_v1']
    results_collection = mongo_db['results']
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")




@app.route('/generate', methods=['POST'])
def generate():
    payload = request.json
    form = payload.get('form', None)

    if form is None:
        return jsonify({"msg": "Missing form in payload..."}), 400

    try:
        filled_prompts, missing_placeholders, class_type = fetch_prompt_list_and_fill_placeholders_with(
            form)
    except Exception as e:
        return jsonify({"msg": f"Bad class type... {e}"}), 400

    doc = {
        "type": class_type,
        "num_steps": len(filled_prompts),
        "current_step": 0,
        "status": "pending",
        "completion": None,
        "start_time": datetime.utcnow()
    }

    try:
        insert_result = results_collection.insert_one(doc)
        token = insert_result.inserted_id
        threading.Thread(target=process_prompt_list,
                         args=(results_collection, token, filled_prompts, 1, app.logger)).start()
        return jsonify({"class_type": class_type, "token": str(token), "num_steps": len(filled_prompts), "missing_placeholders": missing_placeholders}), 202

    except Exception as e:
        return jsonify({"msg": f"Database error: {str(e)}"}), 500


@app.route('/check-completion', methods=['GET'])
def check_completion():
    token = request.args.get('token')
    
    try:
        token_id = ObjectId(token)
        
        doc = results_collection.find_one({"_id": token_id})
        
        # If the document doesn't exist, return an error
        if doc is None:
            return jsonify({"msg": "Invalid token"}), 400
        
        # Remove fields that start with an underscore
        cleaned_doc = {k: v for k, v in doc.items() if not k.startswith('_')}        
        return JSONEncoder().encode(cleaned_doc)
        
    except errors.PyMongoError as e:
        # Handle MongoDB errors
        return jsonify({"msg": f"Database error: {str(e)}"}), 500
    except Exception as e:
        # Handle general errors
        return jsonify({"msg": f"An error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
