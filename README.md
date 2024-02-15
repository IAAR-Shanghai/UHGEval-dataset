Note: If you are a reviewr of our paper, some files may miss due to Anonymous GitHub does not support files that are larger than 8MB. The full size of this repository is over 3GB.

# The full pipeline of creating hallucination dataset

## 1. Collect the raw news

- Status: Full data; Avaliable.
- Data location: [./sources/xinhua/raw/](./sources/xinhua/raw/)
- Number: 75 txt files, 737,766 news in total
- Note: Those data are belong to Xinhua News Agency, and are only used for research purposes.

## 2. Preprocess the raw news

- Status: No data; Need to generate using the script.
- Script: [./sources/xinhua/preprocessor.py](./sources/xinhua/preprocessor.py)
- Data location: [./sources/xinhua/processed](./sources/xinhua/processed); Use the script to generate the data
- Number: Retained 25,005 news articles (constituting 3.39% of the raw news).
- Filtering settings:
  - Only includes news categories such as: '政治', '法律', '军事', '教育', '体育', '经济', '市场', '科学', '技术', '医疗', '卫生', '社会', '文化', '艺术', '娱乐', '天气', '环保', '灾害', '事故' ('Politics', 'Law', 'Military', 'Education', 'Sports', 'Economics', 'Market', 'Science', 'Technology', 'Medical', 'Health', 'Society', 'Culture', 'Art', 'Entertainment', 'Weather', 'Environmental Protection', 'Disaster', 'Accident').
  - The length of newsBeginning + newsRemainder is between [630, 870].
  - newsBeginning has [2, 5] sentences. Note: sentence-ending symbols include "。；：？！"
  - The length of newsBeginning is between [80, 120].

## 3. Generate candidates

- Status: No data; Need to generate using the script.
- Script: [./gen_candidates.py](./gen_candidates.py)
- Data location: [./candidates/](./candidates/)
- Number: Retained 17,503 news articles (constituting 70.00% of the preprocessed news).
- Filtering settings:
  - keywordPrecision is between (0, 1), generally should be between (0.2, 0.6).
  - candidateHallucinatedContinuation consists of only 1 sentence.
  - The length of candidateHallucinatedContinuation is between [20, 70].
  - appearedKeywords has at least 2 keywords.

## 4. Automatic labelling

- Status: Partial data as examples; Need to generate using the script.
- Script: [./gen_machine_annotations.py](./gen_machine_annotations.py)
- Data location: [./machine_annotations/keyword_hallucinated](./machine_annotations/keyword_hallucinated)
- Note: Only articles labeled as having hallucinations were left for subsequent processing; those without hallucinations are located in [./machine_annotations/unhallucinated](./machine_annotations/unhallucinated)

## 5. Use Label Studio to enable human rechecking

[Label Studio](https://labelstud.io/) is a multi-type data labeling and annotation tool with standardized output format.

Relevant files can be found in [./label_studio_annotations/](./label_studio_annotations/).

## 5.1 Prepare Label Studio Pre-annotations

- Status: No data; Need to generate using the script.
- Script: [./gen_pre_annotations.py](./gen_pre_annotations.py)
- Data location: [./label_studio_annotations/pre_annotations](./label_studio_annotations/pre_annotations)
- Reference: [Import pre-annotated data into Label Studio](https://labelstud.io/guide/predictions)

## 5.2 Setup labeling configuration and begin human rechecking

- Script: [./label_studio_annotations/Label Studio Config.xml](./label_studio_annotations/Label%20Studio%20Config.xml)
- An instruction for human annotators: [./label_studio_annotations/README.md](./label_studio_annotations/README.md)
- An additional tutorial for human annotators: [./label_studio_annotations/新闻领域机器续写幻觉数据集标注培训.pptx](./label_studio_annotations/新闻领域机器续写幻觉数据集标注培训.pptx)
- Reference: [Labeling configuration](https://labelstud.io/guide/setup)

## 5.3 Export Label Studio JSON annotations

- Status: Partial data as examples; Need to export using Label Studio.
- Data location: [./label_studio_annotations/after_annotations](./label_studio_annotations/after_annotations)
- Reference: [Export annotations and data from Label Studio](https://labelstud.io/guide/export)

## 6. Get final hallucination dataset

- Status: Full data; Avaliable.
- Script: [./gen_hallucinations.py](./gen_hallucinations.py)
- Data location: [./hallucinations/XinhuaHallucinations.json](./hallucinations/XinhuaHallucinations.json)
- Number: Retained 5,141 news articles (constituting 29.37% of the candidates).
