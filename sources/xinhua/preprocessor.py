import os
import json
import re
from collections import defaultdict

import numpy as np
from tqdm import tqdm


def statistics(objs, report=True):
    """Get statistical information for a collection of objs, where objs contains multiple obj, i.e., multiple news articles"""
    total_news = len(objs)
    is_valid = np.array([valid(obj) for obj in objs])
    category = np.array([obj.get('newsCategoryName', '') for obj in objs])
    category = category[is_valid]

    category_dict = defaultdict(int)
    for c in category:
            category_dict[c] += 1
    
    # The most frequent categories
    print('\n'.join([
        str(ele) 
        for ele in 
        sorted(list(category_dict.items()), key=lambda a: a[1], reverse=True)[:15]
        ])) if report else ()
    
    # Number of valid entries / Total number of news
    print(sum(is_valid), '/', total_news) if report else ()

    return category_dict, sum(is_valid), total_news


def complete_statistics(dir='raw'):
    """Get comprehensive statistical information for all objs in a directory"""
    acc_d = defaultdict(int)  # Accumulated category statistics
    acc_v = 0  # Accumulated number of valid news
    acc_t = 0  # Total number of news accumulated

    curr_dir = os.path.dirname(__file__)
    all_names = os.listdir(os.path.join(os.path.dirname(__file__), dir))
    for name in tqdm(all_names, 'Compiling statistics'):
        path = os.path.join(curr_dir, dir, name)
        with open(path) as f:
            objs = json.load(f)
            d, v, t = statistics(objs, report=False)

            for key, value in d.items():
                acc_d[key] += value
            acc_v += v
            acc_t += t
    
    print('Complete statistics:')
    print('\n'.join([
        str(ele) 
        for ele in 
        sorted(list(acc_d.items()), key=lambda a: a[1], reverse=True)
        ]))
    print(acc_v, '/', acc_t)


def assign_type(newsCategoryName):
    if any([kw in newsCategoryName for kw in ['政治', '法律', '军事', '教育']]):
        return 'doc'  # document-intensive
    if any([kw in newsCategoryName for kw in ['体育', '经济', '市场']]):
        return 'num'  # number-intensive
    if any([kw in newsCategoryName for kw in ['科学', '技术', '医疗', '卫生']]):
        return 'kno'  # knowledge-intensive
    if any([kw in newsCategoryName for kw in ['社会', '文化', '艺术', '娱乐', '天气', '环保', '灾害', '事故']]):
        return 'gen'  # general
    else:
        return ''


def valid(obj):
    """Determine if a news obj is appropriate"""
    
    # Key fields must not be empty
    none_exist = obj.get('headLine', '') == '' or obj.get('broadcastDate', '') == '' or obj.get('content', '') == ''
    if none_exist:
        return False
    
    # The length of the news content should be between [630, 870]
    content = obj.get('content', '')
    content_length_improper = not (630 <= len(content) <= 870)
    if content_length_improper:
        return False
    
    # The length of the first i sentences should be between [80, 120], where i can only be 2, 3, 4, 5
    sentences = re.split(r'(?<=[。；？！])', content)  # Split the article into sentences using common Chinese punctuation, retaining the punctuation
    beginning_proper = False
    for i in range(2, 5+1):
        if 80 <= len(''.join(sentences[:i])) <= 120:
            beginning_proper = True
            break
    return beginning_proper


def full2half(text:str):
    """Convert full-width characters to half-width characters in a string"""
    halfwidth_text = ''
    stay_still = '，。；：？！（）'  # Typical Chinese symbols that don't need conversion
    for char in text:
        code = ord(char)
        if char in stay_still:
            halfwidth_char = char
        elif 65281 <= code <= 65374:
            # The range of full-width characters in Unicode is 0xFF01 to 0xFF5E
            halfwidth_char = chr(code - 65248)
        elif char == '　':
            # Convert full-width space to half-width space
            halfwidth_char = ' '
        else:
            halfwidth_char = char
        halfwidth_text += halfwidth_char
    return halfwidth_text


def save_single_file(type_, no, obj):
    filename = f'{type_}_{str(no).zfill(6)}.json'
    path = os.path.join(os.path.dirname(__file__), 'processed', filename)
    sentences = re.split(r'(?<=[。；？！])', obj['content'])
    i = -1
    for i in range(2, 5+1):
        if 80 <= len(''.join(sentences[:i])) <= 120:
            break
    news_obj = {
        'filename': filename,
        'headLine': full2half(obj['headLine']),
        'broadcastDate': full2half(obj['broadcastDate']),
        'type': type_,
        'newsBeginning': full2half(''.join(sentences[:i])),
        'newsRemainder': full2half(''.join(sentences[i:]))
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(news_obj, f, ensure_ascii=False, indent=4)


def main():
    count_type = {'doc': 0, 'num': 0, 'kno': 0, 'gen': 0}
    curr = os.path.dirname(__file__)

    progress_bar = tqdm(sorted(os.listdir(os.path.join(curr, 'raw'))))
    for dir in progress_bar:  # for all files
        path = os.path.join(curr, 'raw', dir)
        f = open(path)
        objs = json.load(f)

        for obj in objs:  # for all news
            type_ = assign_type(obj.get('newsCategoryName', ''))
            if type_ == '' or not valid(obj):  # Filtering
                continue
            count_type[type_]+=1
            save_single_file(type_, count_type[type_], obj)

        f.close()
        progress_bar.set_description(f'Preprocessed {dir}')
    
    print(count_type)


if __name__ == '__main__':

    main()
    
    # complete_statistics()
