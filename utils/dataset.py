import json
import os
import random
from collections import defaultdict


class Dataset:
    def __init__(self, dir):
        pass

    def __len__(self):
        pass

    def __getitem__(self, key):
        if isinstance(key, int):
            pass
        elif isinstance(key, slice):
            pass


class ProcessedDataset(Dataset):
    def __init__(self, dir):
        """
        Args:
            dir (str): Directory holding the preprocessed dataset
        """
        self.dir = dir
        self.filenames = sorted(os.listdir(dir))  # Inefficient but sufficient
        # After sorting, the order of files: doc, gen, kno, num

    def __len__(self):
        return len(self.filenames)
    
    def __getitem__(self, key):
        if isinstance(key, int):
            path = os.path.join(self.dir, self.filenames[key])
            obj = json.load(f:=open(path))
            f.close()
            return obj
        elif isinstance(key, slice):  # Slicing 10k news requires about 80KB of memory
            indices = list(range(self.__len__()))[key.start : key.stop : key.step]
            objs = []
            for i in indices:
                path = os.path.join(self.dir, self.filenames[i])
                obj = json.load(f:=open(path))
                objs.append(obj)
                f.close()
            return objs

    def type_info(self, report=True):
        """Get the number of each type, index slice, and start index"""
        info = {
            'doc': {'count': None, 'slice': None, 'ptr': None},
            'gen': {'count': None, 'slice': None, 'ptr': None},
            'kno': {'count': None, 'slice': None, 'ptr': None},
            'num': {'count': None, 'slice': None, 'ptr': None},
        }
        curr = 0
        for type in ['doc', 'gen', 'kno', 'num']:
            info[type]['count'] = sum([name.startswith(type) for name in self.filenames])
            info[type]['slice'] = slice(curr, curr + info[type]['count'])
            info[type]['ptr'] = curr
            curr += info[type]['count']
        print('\n'.join([f'{k}: {v}' for k,v in info.items()])) if report else ()
        return info


class Candidates(Dataset):
    def __init__(self, dir: str = './candidates', order='default'):
        """order can be default, sorted, shuffled"""
        self.candidates = []

        if order == 'sorted':
            listdirs = sorted(os.listdir(dir))
        elif order == 'shuffled':
            listdirs = os.listdir(dir)
            random.shuffle(listdirs)  # Corrected for accurate random shuffling
        else:
            listdirs = os.listdir(dir)

        for name in listdirs:
            with open(os.path.join(dir, name)) as f:
                self.candidates.append(json.load(f))
    
    def __len__(self):
        return len(self.candidates)
    
    def __getitem__(self, key):
        return self.candidates[key]

    def candidates_info(self, draw=True, report=False):
        import matplotlib.pyplot as plt
        
        candidates = self.candidates
        precision_distr = [candidate['keywordPrecision'] for candidate in candidates]
        num_appeared_kws_distr = [len(candidate['appearedKeywords']) for candidate in candidates]
        num_kws_distr = [len(candidate['keywords']) for candidate in candidates]

        if draw:
            _, axes = plt.subplots(nrows=3, ncols=1)
            for i, data in enumerate(['precision_distr', 'num_appeared_kws_distr', 'num_kws_distr']):
                axes[i].hist(eval(data), bins=10, density=True, alpha=0.6, color='b')
                axes[i].set_title(data)
            plt.show()

        if report:
            print(f'{precision_distr=}')
            print(f'{num_appeared_kws_distr=}')
            print(f'{num_kws_distr=}')
        
        return precision_distr, num_appeared_kws_distr, num_kws_distr


class MachineAnnotations(Dataset):
    """Machine-generated hallucinations"""
    def __init__(self, dir: str = './machine_annotations/keyword_hallucinated'):
        self.annots = []
        for name in os.listdir(dir):
            with open(os.path.join(dir, name)) as f:
                self.annots.append(json.load(f))

    def __len__(self):
        return len(self.annots)

    def __getitem__(self, key):
        return self.annots[key]
    
    def type_info(self, report=True):
        info = defaultdict(int)
        for item in self.annots:
            info[item['type']] += 1
        print(info) if report else ()
        return info


if __name__ == '__main__':
    # annots = MachineAnnotations()
    # annots.type_info()
    c = Candidates('candidates (17714)')
    c.candidates_info(report=True)
