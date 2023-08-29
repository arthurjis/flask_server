from pymongo import errors
from bson.objectid import ObjectId
from datetime import datetime
import openai
import time


def update_status_in_db(mongo_collection, token_id, status, error_msg=None):
    try:
        update_data = {
            'status': status,
            'completion_time': datetime.utcnow()
        }
        if error_msg:
            update_data['error_msg'] = error_msg
        mongo_collection.update_one(
            {"_id": ObjectId(token_id)},
            {'$set': update_data}
        )
    except errors.PyMongoError as e:
        print(
            f"Database error while updating status: {str(e)}, token: {token_id}")


def process_prompt_list(collection, token, prompt_list, retries=1, logger=None):
    token_id = ObjectId(token)  # Convert to ObjectId if necessary

    if not prompt_list:
        logger.error(f'prompt_worker failed for token {token} with error: Empty prompt list')
        update_status_in_db(collection, token_id,
                            'failed', 'Empty prompt list')
        return

    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    response_list = []
    current_step = 0

    try:
        for prompt in prompt_list:
            current_step += 1

            messages.append(
                {"role": "user", "content": prompt['prompt_string']})
            
            collection.update_one({"_id": ObjectId(token_id)},
                                  {'$set': {'current_step': current_step,
                                            '_messages': messages,
                                            '_response_list': response_list}})

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
                        logger.warning(f'openai.ChatCompletion failed on attemp {attempt} with error {e} for token {token}, retrying...')
                        time.sleep(1)
                    else:
                        logger.error(f'openai.ChatCompletion failed on attemp {attempt} with error {e} for token {token}, exiting...')
                        update_status_in_db(
                            collection, token_id, 'failed', str(e))
                        return

        usage = 0
        for i in response_list:
            try:
                if 'gpt-4' in i['model']:
                    usage += i['usage']['completion_tokens'] * 3e-5 + i['usage']['prompt_tokens'] * 6e-5
                elif 'gpt-3.5-turbo-16k' in i['model']:
                    usage += i['usage']['completion_tokens'] * 4e-6 + i['usage']['prompt_tokens'] * 3e-6
                elif 'gpt-3.5' in i['model']:
                    usage += i['usage']['completion_tokens'] * 2e-6 + i['usage']['prompt_tokens'] * 1.5e-6
                
            except KeyError:
                continue

        update_data = {
            'status': 'complete',
            'completion': response['choices'][0]['message']['content'],
            'usage': usage,
            'completion_time': datetime.utcnow(),
            '_messages': messages,
            '_response_list': response_list
        }
        collection.update_one({"_id": ObjectId(token_id)}, {
                              '$set': update_data})

        if logger:
            logger.info(f"Completed generate for token {token}")

    except KeyError as e:
        logger.error(f'prompt_worker failed for token {token} with KeyError: {e}')
        update_status_in_db(collection, token_id, 'failed',
                            f"Missing fields in response: {e}, {response}")
        return
    except errors.PyMongoError as e:
        logger.error(f'prompt_worker failed for token {token} with PyMongoError: {e}')
        update_status_in_db(collection, token_id, 'failed',
                            f"Database error: {str(e)}")
        return
    except Exception as e:
        logger.error(f'prompt_worker failed for token {token} with error: {e}')
        update_status_in_db(collection, token_id, 'failed',
                            f"An error occurred: {str(e)}")
        return
