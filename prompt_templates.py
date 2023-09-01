import re
from errors import *


prompt_templates = {
    "读写整合课": {
        "template_list": [
            {
                "template_string": """假设你是一名在中国的{{class_level}}英语老师，现有一堂{{reading_theme}}的读写整合课，请依据该文本，设计相应的作业：{{reading_article}}\n要求如下：\n1. 作业分为{{question_usage}}，各类作业分别有{{a_number}};{{b_number}};{{c_number}}道\n2. 基于英语学习活动观，从学习理解、应用实践、迁移创新三个维度进行分层设计。\n3. 下列词语为本课关键词语，在设计词语类题目时可从中进行选择：{{highlighted_words}}\n4. 均用英语回复""",
                "model": "gpt-4",
                "temperature": 1,
                "max_tokens": 2048
            },
            {
                "template_string": """请为上述每项作业附上设计意图或参考答案。用英语回复""",
                "model": "gpt-4",
                "temperature": 1,
                "max_tokens": 2048
            },
            {
                "template_string": """请将上述题目整理成一份完整的英语题目清单，按照作业类型进行分类。并将每道题的设计意图和参考答案展示在题目后。用英语回复""",
                "model": "gpt-3.5-turbo",
                "temperature": 1,
                "max_tokens": 2048
            }
        ]
    },
    "拓展阅读": {
        "template_list": [
            {
                "template_string": """假设你是一名在中国的{{class_level}}英语老师，现有一堂{{reading_theme}}的阅读课，请依据下面这篇文章，生成一篇新的延展阅读文章，并设计新文章的续写作业：\n{{reading_article}}\n要求如下：\n1. 新文章字数上限为：{{words_max}}，字数下限为：{{words_min}}\n2. 续写作业题目数为{{d_number}}道 用英语回复""",
                "model": "gpt-4",
                "temperature": 1,
                "max_tokens": 2048
            },
            {
                "template_string": """请为上述续写作业附上设计意图及参考答案。用英语回复""",
                "model": "gpt-4",
                "temperature": 1,
                "max_tokens": 2048
            },
            {
                "template_string": """请将上述新阅读文章及题目、设计意图、参考答案整合和一篇完整的英语阅读材料。用英语回复""",
                "model": "gpt-3.5-turbo",
                "temperature": 1,
                "max_tokens": 2048
            }
        ]
    },
    "语法课": {
        "template_list": [
            {
                "template_string": """假设你是一名在中国的{{class_level}}英语老师，现有一堂主题为{{reading_theme}}，关于{{reading_article}}知识点的语法课。请围绕这一主题和知识点，进行相应的作业设计。

作业要求如下：
1. 作业分为{{question_usage}}，各类作业分别有{{a_number}}；{{b_number}}；{{c_number}}道
2. 基于英语学习活动观，从学习理解、应用实践、迁移创新三个维度进行分层设计。
3. 采用多模态的作业形式，影视，图片，音乐都可以，激发学生学习的兴趣，让语法学习生动灵活有趣。
4. 均用英语回复""",
                "model": "gpt-4",
                "temperature": 1,
                "max_tokens": 2048
            },
            {
                "template_string": """请为上述续写作业附上设计意图及参考答案。用英语回复""",
                "model": "gpt-4",
                "temperature": 1,
                "max_tokens": 2048
            },
            {
                "template_string": """请将上述题目整理成一份完整的英语题目清单，按照作业类型进行分类。并将每道题的设计意图和参考答案展示在题目后。
均用英语回复。""",
                "model": "gpt-3.5-turbo",
                "temperature": 1,
                "max_tokens": 2048
            }
        ]
    },
        "听力课": {
        "template_list": [
            {
                "template_string": """假设你是一名在中国的{{class_level}}英语老师，现有一堂主题为{{reading_theme}}的听说课，请依据以下听力文本设计相应的作业：

{{reading_article}}

作业要求如下：
1. 作业分为{{question_usage}}，各类作业分别有{{a_number}}；{{b_number}}；{{c_number}}道
2. 基于英语学习活动观，从学习理解、应用实践、迁移创新三个维度进行分层设计。
3. 均用英语回复""",
                "model": "gpt-4",
                "temperature": 1,
                "max_tokens": 2048
            },
            {
                "template_string": """请为上述续写作业附上设计意图及参考答案。用英语回复""",
                "model": "gpt-4",
                "temperature": 1,
                "max_tokens": 2048
            },
            {
                "template_string": """请将上述题目整理成一份完整的英语题目清单，按照作业类型进行分类。并将每道题的设计意图和参考答案展示在题目后。
均用英语回复。""",
                "model": "gpt-3.5-turbo",
                "temperature": 1,
                "max_tokens": 2048
            }
        ]
    },
}


def fetch_prompt_list_and_fill_placeholders_with(input_dict):

    class_type = input_dict.get("class_type")
    if not class_type:
        raise ClassTypeMissingException("class_type is missing in input_dict")

    template_list = prompt_templates.get(class_type, {}).get("template_list", [])
    if not template_list:
        raise TemplateListMissingException(f"No template list found for class_type {class_type}")
    
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
            "max_tokens": template_dict.get("max_tokens", 2048)
        }

        filled_prompts.append(filled_template_dict)

    return filled_prompts, list(missing_placeholders), class_type
