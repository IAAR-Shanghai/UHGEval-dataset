import json
import os

from tqdm import tqdm

def filter_out(dir):
    """Delete json files in the dir folder that do not meet the criteria based on filter items"""
    paths = []
    for name in sorted(os.listdir(dir)):
        path = os.path.join(dir, name)
        obj = json.load(f:=open(path))
        if (
            '改稿' in obj.get('headLine', '') or 
            '（更新）' in obj.get('headLine', '') or 
            '（请以此为准）' in obj.get('headLine', '')
            ###### Add new filter items here ######
        ):
            paths.append(path)
        f.close()
    [print(path) for path in paths]
    if 'Y' == input(f'Total {len(paths)} files to be deleted, confirm deletion (Y/n)：'):
        for path in tqdm(paths):
            os.remove(path)


def objs_info(dir):
    """Count the number of various properties of JSON news under dir"""
    paths = os.listdir(dir)
    type_cnt = {'doc': 0, 'num': 0, 'kno': 0, 'gen': 0}
    generatedBy_cnt = {'InternLM': 0, 'SelfModel': 0, 'Qwen': 0, 'ChatGLM2': 0, 'Baichuan2': 0}
    for path in tqdm(paths):
        type_cnt[path[:3]] += 1
        with open(os.path.join(dir, path)) as f:
            obj = json.load(f)
            generatedBy_cnt[obj.get('generatedBy', 'Baichuan2')] += 1
    return type_cnt, generatedBy_cnt


def hall_rate_by_type():
    """Calculate the rate of hallucination occurrences"""

    kh = objs_info('machine_annotations/keyword_hallucinated')[0]
    un = objs_info('machine_annotations/unhallucinated')[0]

    for k in ['num', 'gen', 'kno', 'doc']:
        print(f'{k}: {kh[k]: >4} / {(kh[k]+un[k]): >4} = {kh[k] / (kh[k]+un[k]) * 100: .2f}%')
    print(f'ALL: {sum(kh.values()): >4} / {sum(kh.values())+sum(un.values()): >4} = {sum(kh.values()) / (sum(kh.values())+sum(un.values())) * 100: .2f}%')


def merge_jsons(src_dir, tgt_path):
    """Merge JSON files in the src_dir folder into tgt_path"""
    objs = []
    listdirs = sorted(os.listdir(src_dir))
    for name in listdirs:
        with open(os.path.join(src_dir, name)) as f:
            obj = json.load(f)
            objs.append(obj)
    with open(tgt_path, 'w', encoding='utf-8') as f:
        json.dump(objs, f, ensure_ascii=False, indent=4)


def get_filenames_in_dirs(dirs: list[str]) -> list[str]:
    filenames = []
    for dir in dirs:
        filenames.extend(os.listdir(dir))
    return filenames
