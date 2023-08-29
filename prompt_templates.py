import re

prompt_templates = {
    "读写整合课": {
        "template_list": [
            {
                "template_string": """假设你是一名在中国的{{class_level}}英语老师，现有一堂{{reading_theme}}的读写整合课，请依据该文本，设计相应的作业：{{reading_article}}\n要求如下：\n1. 作业分为{{question_usage}}，各类作业分别有{{a_number}};{{b_number}};{{c_number}}道\n2. 基于英语学习活动观，从学习理解、应用实践、迁移创新三个维度进行分层设计。\n3. 下列词语为本课关键词语，在设计词语类题目时可从中进行选择：{{highlighted_words}}\n4. 均用英语回复""",
                "model": "gpt-4",
                "temperature": 1,
                "max_tokens": 1024
            },
            {
                "template_string": """请为上述每项作业附上设计意图或参考答案。""",
                "model": "gpt-4",
                "temperature": 1,
                "max_tokens": 1024
            },
            {
                "template_string": """请将上述题目整理成一份完整的英语题目清单，按照作业类型进行分类。并将每道题的设计意图和参考答案展示在题目后。""",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 1024
            }
        ]
    },
}


def fetch_prompt_list_and_fill_placeholders_with(input_dict):
    class_type = input_dict.get("class_type")
    if not class_type:
        return [], [], ''

    template_list = prompt_templates.get(
        class_type, {}).get("template_list", [])

    if not template_list:
        return [], [], ''

    filled_prompts = []
    missing_placeholders = set()

    for template_dict in template_list:
        template = template_dict["template_string"]
        placeholders = re.findall(r"{{\s*(.*?)\s*}}", template)

        filled_template = template
        for placeholder in placeholders:
            if placeholder in input_dict:
                filled_template = re.sub(
                    f"{{{{\s*{re.escape(placeholder)}\s*}}}}", str(input_dict[placeholder]), filled_template)
            else:
                missing_placeholders.add(placeholder)

        filled_template_dict = {
            "prompt_string": filled_template,
            "model": template_dict.get("model", "gpt-3.5-turbo"),
            "temperature": template_dict.get("temperature", 0.7),
            "max_tokens": template_dict.get("max_tokens", 1024)
        }

        filled_prompts.append(filled_template_dict)

    return filled_prompts, list(missing_placeholders), class_type
