from typing import Callable

import evaluate  # Huggingface package, proxy might be needed for proper internet access
import jieba

from utils.llm import GPT


def bleu_score(continuation: str, reference: str, with_penalty=False):
    f = lambda text: list(jieba.cut(text))
    bleu = evaluate.load('bleu')
    results = bleu.compute(predictions=[continuation], references=[[reference]], tokenizer=f)
    score = results['bleu']
    brevity_penalty = results['brevity_penalty']
    return score if with_penalty else score / brevity_penalty

def rouge_score(continuation: str, reference: str):
    f = lambda text: list(jieba.cut(text))
    rouge = evaluate.load('rouge')
    results = rouge.compute(predictions=[continuation], references=[[reference]], tokenizer=f, rouge_types=['rougeL'])
    score = results['rougeL']
    return score

def kw_precision(continuation: str, reference: str, 
                 kw_extractor: Callable = GPT(report=True).extract_kws,
                 with_kw_list: bool = True
                 ) -> float | tuple[float, list[str], list[str]]:
    """Measures the rationality of the generated continuation sentence for the original news object using a model, the higher the score, the more rational"""
    kws = kw_extractor(continuation)
    if len(kws) == 0:
        return 0, [], [] if with_kw_list else 0
    appeared_kws = [kw for kw in kws if kw in reference]
    precision = len(appeared_kws) / len(kws)
    return precision, appeared_kws, kws if with_kw_list else precision
