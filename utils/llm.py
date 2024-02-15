import datetime
import requests
import json
import re

import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # Avoid RPM limit of OpenAI API


class LanguageModel:
    def request(self, query:str) -> str:
        """Implemented by each language model subclass"""
        return ''

    def continue_writing(self, obj:dict) -> str:
        template = '''你是一名新华社新闻工作者。我希望你能辅助我完成一篇新闻的撰写。

请你根据我已经写好的文本为我续写一段话。下面是一个例子：

已经写好的文本：

《不支持任何禁令！美全国步枪协会与特朗普唱反调》
2018-02-27
美国全国步枪协会发言人达娜·勒舍 25 日与总统唐纳德·特朗普唱起反调，说不同意把半自动步枪限购年龄提高至 21 岁，反对禁售“撞火枪托”。

续写的文本：

<response>
特朗普早些时候说已经与全国步枪协会“通气”。但勒舍作客美国广播公司“本周”栏目时说，全国步枪协会已经“极其清晰地”就这些议题表明立场。
</response>

现在我已经写好的文本是：

{}

请你完成要续写的文本（续写的文本写在<response></response>之间）：
'''
        query = template.format(f'《{obj["headLine"]}》\n{obj["broadcastDate"][:10]}\n{obj["newsBeginning"]}')
        try:  # TODO: temporary
            res = self.request(query)
        except:
            return ''
        real_res = res.split('<response>')[-1].split('</response>')[0]
        sentences = re.split(r'(?<=[。；：？！])', real_res)
        return sentences[0]

    @staticmethod  # Some subclasses' continue_writing will directly call this static method
    def _continue_writing_without_instruction(self, obj:dict) -> str:
        """Continue writing, version without instructions
        Some models may not follow instructions well due to insufficient fine-tuning of instructions, so no instructions are added, just input text directly.
        """
        template = "{}"
        query = template.format(f'《{obj["headLine"]}》\n{obj["broadcastDate"][:10]}\n{obj["newsBeginning"]}')
        try:  # TODO: temporary
            res = self.request(query)
        except:
            return ''
        if query in res:
            real_res = res.split(query)[-1].replace('<s>', '').replace('</s>', '').strip()
            sentences = re.split(r'(?<=[。；：？！])', real_res)
            return sentences[0]
        else:
            return ''

    def extract_kws(self, sentence:str) -> list[str]:
        template = '''你是一名新华社新闻工作者。
        
我需要你帮我从一句话中筛选出重要的词组或句子。不需要使用项目列表，每行一个关键词即可。下面是一个例子：

句子：

在她公开表示不支持将半自动步枪的购买年龄限制提高至21岁以及反对禁售“撞火枪托”的同时，这一立场与时事的发展和一些政治观点产生了冲突。

关键词：

<keywords>
公开表示
不支持
半自动步枪
购买年龄限制
提高
21岁
反对
禁售
撞火枪托
立场
政治观点
冲突
</keywords>

现在我的句子是：

{}

请给出提取出来的关键词（写在<keywords></keywords>之间）：
'''
        query = template.format(sentence)
        res = self.request(query)
        kws = res.split('<keywords>')[-1].split('</keywords>')[0].split('\n')
        filtered = [
            s.strip() 
            for s in kws 
            if s.strip() and s.strip() in sentence
            ]  # Remove empty strings and those not in the original sentence
        return filtered

    def are_kws_hallucinated(self, kws:list[str], candidate_obj:dict) -> dict:
        """Determine whether the keyword has an illusion, return a list of keywords with illusions"""

        template = '''你是一名新华社新闻工作者。

我需要你帮我判断一个机器续写的新闻是否存在幻觉。我会给你一段新闻的开头、机器续写的文本（其中关键词用<kw></kw>标注）、可以参考的事实。你需要对机器续写文本中的每一个关键词进行合理性判断。若不合理，则需要给出理由。例如：

这是一段新闻的开头：

"""
《（中国—东盟博览会）第12届中国—东盟博览会闭幕 促成“一带一路”国际产能合作项目34项》
2015-09-21 17:23:12
  新华社南宁9月21日电（记者熊红明、翁晔）第12届中国—东盟博览会、中国—东盟商务与投资峰会21日在广西南宁闭幕。本届博览会首次成功举办国际产能合作系列活动，会期通过各类项目洽谈会成功签约的国际产能合作项目达到34项。
"""

这是机器续写的文本：

"""
在<kw>第2届</kw><kw>中国—东盟博览会</kw>和<kw>中国—东盟商务与投资峰会</kw>期间，<kw>各国代表团</kw>积极寻求<kw>贸易和投资机会</kw>，共同推动<kw>全球经济一体化进程</kw>。本届<kw>展会</kw><kw>总展位数</kw><kw>460个</kw>，<kw>中国-东盟博览会秘书处</kw><kw>秘书长</kw><kw>王雷</kw>表示：“本届展会是<kw>全球最大规模的展会</kw>”。
"""

你可以参考的事实：

"""
\n  中国-东盟博览会秘书处秘书长王雷介绍，2015中国—东盟国际产能合作系列活动搭建了中国与东盟及海丝沿线地区产能合作的新平台。在国际产能与装备制造项目对接洽谈会上，现场达成合作意向11项，成功签约的国际产能合作项目达34项，涉及机械制造、汽车配件、能源建设、建材生产、有色金属、矿产开发等领域。\n  王雷介绍，本届博览会总展位数4600个，其中东盟10国和区域外安排展位1296个，比上届增长2.9%；参展参会客商6.5万人；采购商团组85家，比上届增加5%，其中有组织的专业采购商数量比上届多2500人。\n  在投资合作方面，举办了中马“两国双园”联合展区开展仪式、东盟各国投资推介会等投资促进活动。本届博览会国际合作项目签约项目更多，其中跨境商贸物流、园区建设等涉及“21世纪海上丝绸之路”的产业项目比上届增长50%。\n  王雷说，本届博览会合作区域由服务“10+1”向服务RCEP及“一带一路”沿线国家拓展，创造了更多商机。除韩国出任特邀贵宾国外，本届博览会还吸引印度、日本、澳大利亚、新西兰、土耳其、加纳、孟加拉国、巴基斯坦、哈萨克斯坦、吉尔吉斯斯坦、格鲁吉亚、俄罗斯、美国、加拿大等国家的团组和企业参展参会。\n  此外，博览会在环保、矿业、电力、教育、文化、药品合作、残疾人等其他论坛也取得丰硕成果。会期还开展了一系列民间友好和人文交流活动。广西与越南胡志明市、广西崇左市与老挝甘蒙省他曲市、广西贵港市与菲律宾三宝颜市缔结了友城关系。南宁民歌艺术节、中国—东盟（南宁）戏剧周大联欢等活动精彩纷呈，增进了相互了解和友谊。（完）
"""

<result>
{{
"第2届": "不合理，与标题冲突，应为第12届",
"中国—东盟博览会": "合理",
"中国—东盟商务与投资峰会": "合理",
"各国代表团": "合理",
"贸易和投资机会": "合理",
"全球经济一体化进程": "不合理，与事件冲突，应为区域经济一体化进程",
"展会": "合理",
"总展位数": "合理",
"460个": "不合理，与事实冲突，应为4600个",
"中国-东盟博览会秘书处": "合理",
"秘书长": "合理",
"王雷": "合理，与事实一致",
"全球最大规模的展会": "不合理，与事实不一致"
}}
</result>

如果你已经学会了，请完成下面的任务。

这是一段新闻的开头：

"""
《{headLine}》
{broadcastDate}
{newsBeginning}
"""

这是机器续写的文本：

"""
{candidateHallucinatedContinuation}
"""

你可以参考的事实：

"""
{newsRemainder}
"""

请给出判断结果（写在<result></result>之间）：

'''
        
        query = template.format(
            headLine=candidate_obj['headLine'],
            broadcastDate=candidate_obj['broadcastDate'],
            newsBeginning=candidate_obj['newsBeginning'],
            candidateHallucinatedContinuation=self._mark_kws(kws, candidate_obj['candidateHallucinatedContinuation']),
            newsRemainder=candidate_obj['newsRemainder']
        ).replace('{{', '{').replace('}}', '}')  # In Python, curly braces are special characters
        res = self.request(query)
        real_res = self._str2dict(res.split('<result>')[-1].split('</result>')[0])
        filtered = {
            k:v 
            for k,v in real_res.items()
            if k in kws and v.startswith('不合理')
        }
        return filtered

    @staticmethod
    def _mark_kws(kws:list[str], candidateHall:str) -> str:
        """Mark keywords in the text with <kw></kw>"""
        for idx, kw in enumerate(kws):
            if any([kw in tmp for tmp in kws[:idx]]):
                continue  # Prohibit a keyword from being a substring of any keyword before it, otherwise there will be nested annotations
            candidateHall = candidateHall.replace(kw, f'<kw>{kw}</kw>')
        return candidateHall

    @staticmethod
    def _str2dict(s:str) -> dict:
        try:
            d = json.loads(s)
        except json.decoder.JSONDecodeError:
            d = {}
        return d


class Baichuan2(LanguageModel):
    def request(self, query) -> str:
        url = "a_secret_url_to_make_a_request"
        payload = json.dumps({
            "prompt": query,
            "params": {
                "temperature": 1.0,
                "do_sample": True,
                "max_new_tokens": 100,
                "num_return_sequences": 1
            }
        })
        headers = {
        'token': 'a_secret_token',
        'Content-Type': 'application/json'
        }
        res = requests.request("POST", url, headers=headers, data=payload)
        res = res.json()['choices'][0]

        return res


class GPT(LanguageModel):
    def __init__(self, model: str = 'gpt-3.5-turbo', report=False):
        self.model = model
        self.report = report
        self.token_consumed = 0
        self.system_message = f"""You are ChatGPT, a large language model trained by OpenAI.
Knowledge cutoff: 2021-09
Current date: {datetime.datetime.now().date()}"""  # Useful trick

    @retry(wait=wait_random_exponential(min=21, max=70), stop=stop_after_attempt(6))
    def request(self, query: str) -> str:
        openai.api_key = "a_secret_api_key"
        res = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user","content": query},
                ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        self.token_consumed += res['usage']['total_tokens']
        print(f'\nToken consumed: {self.token_consumed}') if self.report else ()
        return res["choices"][0]["message"]["content"]


class SelfModel(LanguageModel):
    def request(self, query) -> str:
        url = "a_secret_url_to_make_a_request"
        payload = json.dumps({
            "prompt": query,
            "params": {
                "temperature": 1.0,
                "do_sample": True,
                "max_new_tokens": 600,
                "num_return_sequences": 1
            }
        })
        headers = {
        'token': 'a_secret_token',
        'Content-Type': 'application/json'
        }
        res = requests.request("POST", url, headers=headers, data=payload)
        res = res.json()['choices'][0]

        return res

    def continue_writing(self, obj:dict) -> str:
        template = "Human: 【生成任务：文本续写】我要你担任新闻编辑。我将为您提供与新闻相关的故事或主题，您将续写一篇评论文章，对已有文本进行符合逻辑的续写。您应该利用自己的经验，深思熟虑地解释为什么某事很重要，用事实支持主张，并补充已有故事中可能缺少的逻辑段落。\n请对以下文本进行续写。\n {} Assistant:"
        query = template.format(f'《{obj["headLine"]}》\n{obj["broadcastDate"][:10]}\n{obj["newsBeginning"]}')
        res = self.request(query)
        real_res = res.split('Assistant:')[-1].split('</s>')[0].strip()
        sentences = re.split(r'(?<=[。；：？！])', real_res)
        return sentences[0]
    
    def extract_kws(self, sentence: str) -> list[str]:
        raise NotImplementedError("This method is disabled in SelfModel class")
    
    def are_kws_hallucinated(self, kws: list[str], candidate_obj: dict) -> dict:
        raise NotImplementedError("This method is disabled in SelfModel class")


class ChatGLM2(LanguageModel):
    def request(self, query) -> str:
        url = "a_secret_url_to_make_a_request"
        payload = json.dumps({
            "prompt": query,
            "params": {
                "temperature": 0.95,
                "do_sample": True,
                "max_new_tokens": 100,
                "num_return_sequences": 1
            }
        })
        headers = {
        'token': 'a_secret_token',
        'Content-Type': 'application/json'
        }
        res = requests.request("POST", url, headers=headers, data=payload)
        res = res.json()['choices'][0]

        return res
    
    def continue_writing(self, obj: dict) -> str:
        return super()._continue_writing_without_instruction(self, obj)

    def extract_kws(self, sentence: str) -> list[str]:
        raise NotImplementedError("This method is disabled in ChatGLM2 class")
    
    def are_kws_hallucinated(self, kws: list[str], candidate_obj: dict) -> dict:
        raise NotImplementedError("This method is disabled in ChatGLM2 class")


class InternLM(LanguageModel):
    def request(self, query) -> str:
        url = "a_secret_url_to_make_a_request"
        payload = json.dumps({
            "prompt": query,
            "params": {
                "temperature": 1.0,
                "do_sample": True,
                "max_new_tokens": 100,
                "num_return_sequences": 1
            }
        })
        headers = {
        'token': 'a_secret_token',
        'Content-Type': 'application/json'
        }
        res = requests.request("POST", url, headers=headers, data=payload)
        res = res.json()['choices'][0]

        return res

    def continue_writing(self, obj: dict) -> str:
        """续写"""
        return super()._continue_writing_without_instruction(self, obj)

    def extract_kws(self, sentence: str) -> list[str]:
        raise NotImplementedError("This method is disabled in InternLM class")
    
    def are_kws_hallucinated(self, kws: list[str], candidate_obj: dict) -> dict:
        raise NotImplementedError("This method is disabled in InternLM class")


class Qwen(LanguageModel):
    def request(self, query) -> str:
        url = "a_secret_url_to_make_a_request"
        payload = json.dumps({
            "prompt": query,
            "params": {
                "temperature": 1,
                "do_sample": True,
                "max_new_tokens": 100,
                "num_return_sequences": 1
            }
        })
        headers = {
        'token': 'a_secret_token',
        'Content-Type': 'application/json'
        }
        res = requests.request("POST", url, headers=headers, data=payload)
        res = res.json()['choices'][0]

        return res

    def continue_writing(self, obj: dict) -> str:
        return super()._continue_writing_without_instruction(self, obj)

    def extract_kws(self, sentence: str) -> list[str]:
        raise NotImplementedError("This method is disabled in Qwen class")
    
    def are_kws_hallucinated(self, kws: list[str], candidate_obj: dict) -> dict:
        raise NotImplementedError("This method is disabled in Qwen class")
