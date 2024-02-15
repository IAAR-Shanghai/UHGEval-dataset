import json
import os

from tqdm import tqdm

from utils.dataset import MachineAnnotations


def machine2pre(machine_annotations_dir, pre_annotations_dir):
    annots = MachineAnnotations(machine_annotations_dir)[:]
    for annot in tqdm(annots):
        path = os.path.join(pre_annotations_dir, annot["filename"])
        if os.path.exists(path):
            continue
        with open(path, 'w', encoding='utf-8') as f:
            obj = {
                "filename": annot["filename"],
                "newsBeginning": f"《{annot['headLine']}》 {annot['broadcastDate']}\n{annot['newsBeginning']}".replace('\n', '\n\n').strip(),
                "candidateHallucinatedContinuation": f"{annot['candidateHallucinatedContinuation']}".strip(),
                "toAnnotate": '\n'.join([f'{k} - {annot["hallucinatedKeywords"].get(k, "合理")}' for k in annot['keywords']]),
                "newsRemainder": f"{annot['newsRemainder']}".replace('\n', '\n\n').strip(),
            }
            json.dump(obj, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    machine2pre(
        'machine_annotations/keyword_hallucinated',
        'label_studio_annotations/pre_annotations'
    )
