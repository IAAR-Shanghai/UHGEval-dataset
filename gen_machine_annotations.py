import json
import os
from collections import defaultdict

from tqdm import tqdm

from utils.llm import LanguageModel, GPT
from utils.dataset import Candidates


def annotate(candidates: list[dict], llm: LanguageModel, dir: str = 'machine_annotations'):
    subdirs_type_count = {  # Count the number of news of each category in each subfolder at the same time
        'keyword_hallucinated': defaultdict(int),
        'unhallucinated': defaultdict(int)
    }
    for cand in tqdm(candidates):

        if (os.path.exists(f'{dir}/keyword_hallucinated/{cand["filename"]}') or
             os.path.exists(f'{dir}/unhallucinated/{cand["filename"]}')):
            continue
        if hall_kws := llm.are_kws_hallucinated(cand['keywords'], cand):
            subdir = 'keyword_hallucinated'
            obj = {**cand, 'hallucinatedKeywords': hall_kws}
        else:
            subdir = 'unhallucinated'
            obj = cand
        with open(f'{dir}/{subdir}/{obj["filename"]}', 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=4)
        subdirs_type_count[subdir][cand['type']] += 1
    return subdirs_type_count


if __name__ == '__main__':
    cands = Candidates(dir='./candidates', order='shuffled')
    cands = cands[:]
    llm = GPT(report=True)
    annotate(cands, llm)
