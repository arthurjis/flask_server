import re

prompt_templates = {
    "读写整合课": {
        "template_list": [
            """假设你是一名在中国的{{   class_level  }}英语老师，现有一堂{{reading_theme}}的读写整合课，请依据该文本，设计相应的作业：
            {{reading_article}}
            要求如下：
            1. 作业分为{{question_usage}}，各类作业分别有{{a_number}}；{{b_number}}；{{c_number}}道
            2. 基于英语学习活动观，从学习理解、应用实践、迁移创新三个维度进行分层设计。
            3. 下列词语为本课关键词语，在设计词语类题目时可从中进行选择：{{highlighted_words}}
            4. 均用英语回复""",
            """请为上述每项作业附上设计意图或参考答案。""",
            """请将问题、答案、设计意图进行整合，导出为表格形式"""
        ]
    }
}


def fetch_prompt_list_and_fill_placeholders_with(input_dict):
    class_type = input_dict.get("class_type")
    template_list = prompt_templates.get(class_type, {}).get("template_list", [])
    
    if not template_list:
        return [], [], ''
    
    filled_prompts = []
    missing_placeholders = set()
    
    for template in template_list:
        placeholders = re.findall(r"{{\s*(.*?)\s*}}", template)
        # print('placeholders', placeholders)
        
        filled_template = template
        for placeholder in placeholders:
            if placeholder in input_dict:
                # print(str(input_dict[placeholder]))
                filled_template = re.sub(f"{{{{\s*{re.escape(placeholder)}\s*}}}}", str(input_dict[placeholder]), filled_template)
            else:
                missing_placeholders.add(placeholder)
                
        filled_prompts.append(filled_template)
        
    return filled_prompts, list(missing_placeholders), class_type
