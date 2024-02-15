"""Note: this script cannot be run directly, as it relys on deployed LLMs and reward models. 
This is just a demo of how to generate hallucinated continuation candidates. The actual 
usage is to deploy the LLMs and reward models, and then use the gen_candidates function to 
generate candidates."""

import json
import os
from typing import Callable, Union

from tqdm import tqdm

from utils.dataset import ProcessedDataset
from utils.llm import (Baichuan2, ChatGLM2, InternLM, LanguageModel, Qwen,
                       SelfModel)
from utils.metric import kw_precision
from utils.reward_model import get_reward_score_from_rm_ziya


def fluency_ranking(
        sentences: dict,
        obj: dict,
        score: Callable = get_reward_score_from_rm_ziya
        ) -> list[str]:
    """为多个大模型生成的句子按照与上文衔接的流畅度进行排序"""
    newsBeginning = f'《{obj["headLine"]}》\n{obj["broadcastDate"][:10]}\n{obj["newsBeginning"]}'
    results = []
    for llm_name, continuation in sentences.items():
        score = get_reward_score_from_rm_ziya(newsBeginning, continuation)
        results.append((llm_name, score))
    results = sorted(results, key=lambda x: x[1], reverse=True)
    return [llm_name for llm_name, _ in results]


def gen_candidates(
        datasets: Union[ProcessedDataset, list[dict]],
        llms: list[LanguageModel],  # 多个模型生成，选出最合适的一个
        dir: str ='candidates'
        ):
    """生成待标注的候选幻觉文本数据集，并保存至dir下"""
    for idx in tqdm(range(len(datasets))):
        news_obj = datasets[idx]

        if os.path.exists(os.path.join(os.path.dirname(__file__), dir, news_obj['filename'])):
            continue

        sentences = {type(llm).__name__: llm.continue_writing(news_obj) for llm in llms}  # 续写
        sentences = {
            llm_name: sentence
            for llm_name, sentence in sentences.items()
            if 20 <= len(sentence) <= 70
            }  # 过滤长度不合适的
        ranks = fluency_ranking(sentences, news_obj)  # 获得流畅度排名

        results = [
            # 候选文本，准确率，出现的关键词，全部关键词，生成文本对应大模型名称
            (sentences[rank], *kw_precision(sentences[rank], str(news_obj)), rank)
            for rank in ranks[:3]  # 只考虑前三个
            ]
        results = [
            (sentence, precision, appeared_kws, kws, llm_name)
            for sentence, precision, appeared_kws, kws, llm_name in results
            if 0 < precision < 1 and len(appeared_kws) >= 2
            ]  # 过滤准确率极值以及出现的关键词过少的
        if not results:
            continue

        final_result = min(results, key=lambda x: x[1])  # 获得最终的候选幻觉文本，准确率最低的那个
        path = os.path.join(os.path.dirname(__file__), dir, news_obj['filename'])
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                **news_obj,
                'candidateHallucinatedContinuation': final_result[0],
                'keywordPrecision': final_result[1],
                'appearedKeywords': final_result[2],
                'keywords': final_result[3],
                'generatedBy': final_result[4]
            }, f, ensure_ascii=False, indent=4)


def gen_candidates_by_fold(datasets, start_ptr=0, fold_size = 1000):
    datasets = datasets[start_ptr:]
    num_fold = len(datasets) // fold_size + 1
    for ith in range(num_fold):
        print(f'The {ith+1}/{num_fold} fold.')
        sliced_dataset = datasets[ith*fold_size : (ith+1)*fold_size]
        gen_candidates(sliced_dataset, [Baichuan2()] * 2, kw_precision, 'candidates')


if __name__ == '__main__':
    import random
    xinhua = ProcessedDataset('./sources/xinhua/processed')[:]
    random.shuffle(xinhua)
    llms = [Baichuan2(), InternLM(), Qwen(), ChatGLM2(), SelfModel()]
    gen_candidates(xinhua, llms, './candidates')
