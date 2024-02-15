import json
import os

from tqdm import tqdm

def after_annotations2final_hallucinations(
        after_hallu_path = './label_studio_annotations/after_annotations/2023101000.json', 
        machine_annot_dir = './machine_annotations/keyword_hallucinated',
        final_hallucinations_dir = './hallucinations'
        ):

    # Read after_annotations
    with open(after_hallu_path) as f:
        after_annotations = json.load(f)

    # Extract filenames of news that are confirmed to have hallucinations
    final_hallucinations_filenames = [
        obj['data']['filename'] 
        for obj in after_annotations 
        if (
            obj['total_annotations'] >= 1 and  # Ensure someone annotated
            obj['cancelled_annotations'] ==0 and  # Ensure no one skipped
            sum([len(annot['result']) for annot in obj['annotations']]) == 0  # Ensure no one made incorrect annotations
            )
        ]

    # Save these files under final_hallucinations_dir
    for filename in tqdm(final_hallucinations_filenames):
        with open(os.path.join(machine_annot_dir, filename)) as f:
            obj = json.load(f)
        new_obj = {
            'filename': obj['filename'],
            'headLine': obj['headLine'],
            'broadcastDate': obj['broadcastDate'],
            'type': obj['type'],
            'newsBeginning': obj['newsBeginning'],
            'hallucinatedContinuation': obj['candidateHallucinatedContinuation'],
            'appearedKeywords': obj['appearedKeywords'],
            'allKeywords': {
                k: obj['hallucinatedKeywords'].get(k, '合理')
                for k in obj['keywords']
            },
            'newsRemainder': obj['newsRemainder']
        }
        with open(os.path.join(final_hallucinations_dir, filename), 'w', encoding='utf-8') as f:
            json.dump(new_obj, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    after_annotations2final_hallucinations(
        'label_studio_annotations/after_annotations/example.json',
        'machine_annotations/keyword_hallucinated',
        'hallucinations'
    )
