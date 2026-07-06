# HEALTHCARE-RAG từ A đến Z

> Tài liệu nhập môn theo flow, dành cho người biết Python cơ bản.  
> Đối chiếu với code, model và notebook trong workspace ngày 22/06/2026.  
> Phiên bản này dùng **4 intent**: `NUTRITION_LOOKUP`, `HEALTH_ADVICE`, `BOTH`, `NONE`.

---

## 0. Cách học tài liệu này

Đừng bắt đầu bằng CRF hay RRF. Hãy học theo thứ tự:

1. Hiểu hệ thống nhận câu hỏi gì và trả lời bằng nguồn nào.
2. Hiểu bốn intent quyết định bốn đường đi.
3. Lần theo một request trong `ENPipeline.answer()`.
4. Sau đó mới học BERT, NER, embedding, BM25, RRF và reranker.
5. Cuối cùng học metric và cách phòng thủ các giới hạn.

Trong tài liệu, ba loại thông tin được tách rõ:

- **Runtime:** code thật đang chạy khi demo.
- **Training/evaluation:** notebook dùng để tạo model hoặc đo chất lượng.
- **Slide/report:** cách trình bày; nếu lệch runtime thì phải sửa slide/report, không sửa sự thật.

Thứ tự ưu tiên khi có mâu thuẫn:

```text
code runtime + config + model config
        > output notebook đã chạy
        > slide và báo cáo viết tay
```

---

# Tầng 1 - Bức tranh toàn cảnh

## 1. Đồ án giải quyết bài toán gì?

Đây là chatbot tiếng Anh về dinh dưỡng và sức khỏe. Một câu hỏi có thể cần:

- số liệu dinh dưỡng chính xác từ USDA;
- tài liệu y khoa từ NFCorpus;
- cả hai nguồn;
- hoặc bị từ chối vì nằm ngoài miền.

Do đó hệ thống không gửi mọi câu hỏi thẳng vào Llama. Nó phân loại intent trước để chọn đúng đường xử lý.

| Intent | Người dùng muốn gì? | Nguồn | Có gọi LLM? |
|---|---|---|---|
| `NUTRITION_LOOKUP` | Số calorie, protein, fat... của thực phẩm | USDA SQLite | Không nếu fast-path thành công |
| `HEALTH_ADVICE` | Tác dụng, rủi ro, bệnh lý, lời khuyên | NFCorpus | Có |
| `BOTH` | Vừa số USDA vừa phân tích sức khỏe | USDA + NFCorpus | Có |
| `NONE` | Câu ngoài dinh dưỡng/sức khỏe | Không nguồn | Không |

Ví dụ:

```text
How many calories are in an apple?
-> NUTRITION_LOOKUP

Is salmon good for heart health?
-> HEALTH_ADVICE

How much protein is in salmon, and is it good for heart health?
-> BOTH

How do I reverse a linked list in Python?
-> NONE
```

Điểm rất quan trọng: câu có tên thực phẩm chưa chắc là `BOTH`.

```text
Can ginger help nausea during pregnancy?
```

Câu này hỏi tác dụng sức khỏe, không hỏi số dinh dưỡng, nên là `HEALTH_ADVICE`.

## 2. RAG là gì?

RAG là Retrieval-Augmented Generation:

1. **Retrieval:** tìm tài liệu liên quan.
2. **Augmentation:** đưa tài liệu vào prompt.
3. **Generation:** LLM trả lời dựa trên tài liệu đó.

Flow RAG của project:

```text
Query
  -> BM25 tìm theo từ khóa
  -> MiniLM tìm theo ngữ nghĩa
  -> RRF hợp nhất hai bảng xếp hạng
  -> Cross-encoder rerank
  -> lấy top 3 tài liệu
  -> Llama 3.1:8b sinh câu trả lời
```

RAG không fine-tune Llama. Nó cung cấp context tại thời điểm inference.

## 3. Vì sao có USDA fast-path?

LLM có thể nhớ sai số, nhầm khẩu phần hoặc nhầm thực phẩm sống/chín. USDA là dữ liệu có cấu trúc, nên câu hỏi số được xử lý bằng code xác định:

```text
food name -> SQLite lookup -> nutrient values -> Markdown answer
```

Khi fast-path thành công, `used_llm=False`. Cách nói chính xác:

> Fast-path loại bỏ rủi ro LLM tự bịa số USDA; rủi ro còn lại là nhận diện hoặc ghép nhầm tên thực phẩm.

Không nên nói “hệ thống tuyệt đối không hallucinate”.

## 4. Kiến trúc tổng thể

```text
Browser
  -> Spring Boot :8081
     - giao diện, auth, session, history
  -> POST /ask đến FastAPI :8000
  -> ENPipeline.answer(query, history)
     1. NER trên query hiện tại
     2. gom entity từ lịch sử
     3. intent classifier
     4. NONE -> trả reject ngay
     5. NUTRITION/BOTH -> USDA SQLite
     6. HEALTH/BOTH -> Hybrid retrieval -> reranker
     7. fast-path hoặc Llama generation
  -> JSON answer, intent, entities, sources
  -> Spring Boot hiển thị kết quả
```

File điều phối quan trọng nhất: [`src/en/pipeline.py`](../src/en/pipeline.py).

## 5. Offline và online khác nhau thế nào?

### Offline

- tạo và QA dataset intent;
- train intent BERT;
- train NER BioBERT/BERT + CRF;
- dựng USDA SQLite;
- encode NFCorpus vào ChromaDB;
- chạy notebook đánh giá.

### Online

- load checkpoint;
- chạy inference;
- tra database/truy hồi;
- sinh answer.

Runtime không train lại BERT sau mỗi câu hỏi.

## 6. Tự kiểm tra tầng 1

1. Vì sao câu hỏi calorie nên tránh LLM nếu có USDA?
2. `BOTH` khác `HEALTH_ADVICE` ở yêu cầu nào?
3. `NONE` tiết kiệm tài nguyên ra sao?
4. RAG có thay đổi trọng số Llama không?

---

# Tầng 2 - Từ điển thuật ngữ

## 7. Thuật ngữ machine learning

### Model và checkpoint

- **Model architecture:** cấu trúc tính toán, ví dụ BERT 12 lớp.
- **Checkpoint:** trọng số đã học, ví dụ `models/intent_model_v2/model.safetensors`.

### Training và inference

- **Training:** tính loss, backpropagation, cập nhật trọng số.
- **Inference:** dùng trọng số đã học để dự đoán.

### Epoch, batch, learning rate

- **Epoch:** một lượt đi qua toàn bộ train set.
- **Batch:** số mẫu xử lý trước một lần cập nhật.
- **Learning rate:** độ lớn của bước cập nhật trọng số.

### Train set và held-out test set

Dataset 2.240 câu được chia 80/20:

- 1.792 câu train để cập nhật model;
- 448 câu test được giữ khỏi training và chỉ dùng đánh giá cuối.

“Held-out” chỉ có nghĩa là phần test được tách ra và không cho model học.

### Accuracy và Macro-F1

```text
Accuracy = số dự đoán đúng / tổng số mẫu
```

Macro-F1 tính F1 riêng cho từng class rồi lấy trung bình, nên mỗi intent có trọng lượng ngang nhau.

## 8. Thuật ngữ NLP

### Intent classification

Phân loại mục đích của cả câu. Output chỉ có một trong bốn nhãn.

### NER

Named Entity Recognition xác định span trong câu:

```text
How much protein is in salmon?
         ^^^^^^^       ^^^^^^
         NUTRIENT      FOOD
```

Checkpoint NER có ba entity type được train:

- `FOOD`
- `DISEASE`
- `NUTRIENT`

Runtime JSON còn có key `SYMPTOM`, nhưng model config không có `B/I-SYMPTOM`; vì vậy đây là key tương thích/dự phòng, không phải entity type thứ tư đã train.

### BIO tagging

Với ba entity type, model có 7 nhãn token:

```text
O
B-FOOD, I-FOOD
B-DISEASE, I-DISEASE
B-NUTRIENT, I-NUTRIENT
```

`B` là token đầu entity, `I` là token tiếp theo, `O` là ngoài entity.

### CRF và Viterbi

- Linear layer tạo emission score cho từng token/label.
- CRF học cả transition giữa các label.
- Viterbi tìm chuỗi label có tổng điểm cao nhất.

Ví dụ CRF giúp tránh chuỗi vô lý như `O -> I-FOOD` nếu không có `B-FOOD` trước đó.

## 9. Thuật ngữ retrieval

### Corpus

Tập tài liệu để tìm kiếm. Project dùng 3.633 tài liệu NFCorpus gốc cho benchmark.

### Sparse và dense

- **Sparse:** dựa trên token/từ khóa, ví dụ TF-IDF và BM25.
- **Dense:** biến câu thành vector ngữ nghĩa, ví dụ MiniLM 384 chiều.

### Embedding

Embedding là vector số đại diện ý nghĩa câu. Hai câu gần nghĩa có cosine similarity cao hơn.

### Qrels

Qrels là ground truth nối query ID với document ID liên quan. Đây là cơ sở tính MRR retrieval.

### RRF

Reciprocal Rank Fusion hợp nhất nhiều bảng xếp hạng bằng vị trí, không cộng raw score khác thang đo.

### Reranker

Retriever tìm ứng viên nhanh; reranker đọc trực tiếp cặp `(query, document)` để sắp lại chính xác hơn.

## 10. Thuật ngữ generation

- **Prompt:** instructions + context + question gửi cho LLM.
- **Hallucination:** output nghe hợp lý nhưng không được dữ liệu hỗ trợ.
- **Grounded answer:** answer bám context/nguồn.
- **Fast-path:** đường xử lý không gọi LLM.

---

# Tầng 3 - Dữ liệu

## 11. Bản đồ dữ liệu

| Dữ liệu | Vai trò |
|---|---|
| `data/en/synthetic_intent.csv` | 2.400 query LLM-assisted, 600/class |
| `data/en/intent_v2/intent_train_v2.csv` | dataset intent cuối, 2.240, 560/class |
| `data/en/bc5cdr_bio.jsonl` hoặc nguồn tương ứng | NER chemical/disease |
| `data/en/food_bio.jsonl` | bổ sung nhãn FOOD |
| `data/nfcorpus/corpus.jsonl` | 3.633 tài liệu benchmark |
| `data/nfcorpus/queries.jsonl` | query NFCorpus |
| `data/nfcorpus/qrels/test.tsv` | qrels của 323 test query |
| `data/en/corpus.jsonl` | corpus runtime cho BM25 |
| `data/usda_food.db` | SQLite USDA runtime |

## 12. Dataset intent 4 lớp được tạo thế nào?

Notebook chính: [`notebooks/en/build_intent_pipeline.ipynb`](../notebooks/en/build_intent_pipeline.ipynb).

### Bước 1 - Raw LLM-assisted data

```text
2.400 câu = 600 câu x 4 labels
```

Đây là dataset custom vì không có public dataset khớp đúng bốn routing label của hệ thống.

### Bước 2 - Near-duplicate filtering

```python
lsh = MinHashLSH(threshold=0.85, num_perm=128)

for idx, row in raw_df.iterrows():
    m = get_minhash(row["text"])
    if lsh.query(m):
        drop_indices.add(idx)
    else:
        lsh.insert(idx, m)
```

Ý nghĩa:

1. `get_minhash()` biến tập token thành chữ ký ngắn.
2. `lsh.query(m)` tìm chữ ký có khả năng rất giống.
3. Nếu đã có câu gần giống thì đánh dấu bỏ.
4. Ngưỡng `0.85` khá chặt, chủ yếu bắt câu gần trùng.

Slide hiện ghi loại 57 near-duplicates. Nếu dùng số này, phần trăm đúng trên 2.400 raw là:

```text
57 / 2400 = 2.375%, không phải 3.4%
```

### Bước 3 - Cân bằng LLM data

Sau dedup, notebook không dùng toàn bộ số còn lại. Nó lấy đúng 500 câu mỗi class:

```python
balanced_llm_df = (
    clean_llm_df.groupby("label")
    .apply(lambda x: x.sample(n=500, random_state=42))
    .reset_index(drop=True)
)
```

Kết quả:

```text
2.000 LLM rows = 500/class
```

Do đó không được giải thích `2.400 -> 2.000` là “xóa 400 duplicates”. Nó gồm dedup rồi downsample để cân bằng.

### Bước 4 - Hard examples bằng rule/template

Notebook sinh thêm 60 câu khó cho mỗi class:

```text
NUTRITION_LOOKUP : 60
HEALTH_ADVICE    : 60
BOTH             : 60
NONE             : 60
Total            : 240
```

Ví dụ hard boundary:

```text
Is ginger safe during pregnancy?
-> HEALTH_ADVICE, không phải BOTH

How much protein is in salmon, and is it safe for hypertension?
-> BOTH
```

Đây là rule/template augmentation, không nên gọi là 240 mẫu được chuyên gia độc lập đánh nhãn thủ công.

### Bước 5 - Merge và shuffle

```python
final_df = pd.concat([balanced_llm_df, hard_df], ignore_index=True)
final_df = final_df.sample(frac=1, random_state=42).reset_index(drop=True)
```

Kết quả cuối:

```text
2.000 + 240 = 2.240
560 câu mỗi class
```

### Bước 6 - Dataset QA

File xác minh hiện tại: `reports/en/intent_v2_standard_split/dataset_qa_export_summary.json`.

```text
Rows                 : 2.240
Counts               : 560/class
Exact duplicates     : 0
Within-class cosine  : 0.3252
Between-class cosine : 0.1522
Separation ratio     : 2.1368x
```

Ý nghĩa semantic separation:

```python
ratio = within_avg / between_avg
```

`ratio > 1` cho thấy câu cùng label gần nhau hơn câu khác label trong không gian embedding. Nó không chứng minh label đúng 100%.

Slide đang dùng `0.258 / 0.126 / 2.05x`, trong khi summary mới của file 2.240 là `0.325 / 0.152 / 2.137x`. Khi thuyết trình chỉ chọn một lần chạy có provenance rõ; tốt nhất dùng summary mới.

## 13. Dữ liệu NER

NER kết hợp:

- BC5CDR cho disease và chemical;
- dữ liệu FOOD bổ sung.

Mapping chemical sang `NUTRIENT` là xấp xỉ miền. Không phải mọi chemical đều là nutrient, nên đây là một giới hạn hợp lệ để thừa nhận.

## 14. NFCorpus và qrels

NFCorpus gồm tài liệu y sinh và query có qrels. Benchmark retrieval dùng 323 query trong test qrels.

`MRR@10` chỉ cần biết document liên quan đứng ở rank nào; nó không cần LLM sinh answer.

## 15. USDA SQLite

USDA gốc là dữ liệu có cấu trúc lớn. SQLite giúp:

- tìm food nhanh;
- join nutrients theo ID;
- không phải đọc CSV lớn mỗi request;
- trả số xác định.

---

# Tầng 4 - Huấn luyện model

## 16. Intent BERT 4-class

Notebook: [`notebooks/en/train_intent_bert_v2_standard_split_colab.ipynb`](../notebooks/en/train_intent_bert_v2_standard_split_colab.ipynb).

### Cấu hình

```python
LABELS = ["NUTRITION_LOOKUP", "HEALTH_ADVICE", "BOTH", "NONE"]
MODEL_NAME = "bert-base-uncased"
MAX_LENGTH = 128
BATCH_SIZE = 16
EPOCHS = 3
LR = 2e-5
```

### Chia dữ liệu

```python
train_df, test_df = train_test_split(
    df,
    test_size=0.2,
    random_state=42,
    stratify=df["label"],
)
```

```text
Train: 1.792 = 448/class
Test :   448 = 112/class
```

### Tokenization

```python
tokenizer(
    text,
    truncation=True,
    padding="max_length",
    max_length=128,
)
```

- `input_ids`: ID token.
- `attention_mask`: 1 cho token thật, 0 cho padding.

### Kiến trúc

```text
query
 -> WordPiece tokens
 -> BERT 12 layers
 -> [CLS] vector 768 chiều
 -> Linear(768, 4)
 -> 4 logits
 -> argmax label
```

### Loss và optimizer

```python
model = AutoModelForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels=4,
    id2label=ID2LABEL,
    label2id=LABEL2ID,
)
optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
```

Khi truyền `labels`, Hugging Face tính CrossEntropyLoss nội bộ:

```python
out = model(**batch)
out.loss.backward()
optimizer.step()
optimizer.zero_grad()
```

### Kết quả held-out test

```text
Accuracy = 0.9933
Macro-F1 = 0.9933
445/448 câu đúng
```

Confusion matrix:

```text
                   predicted
gold            NUT  HEALTH  BOTH  NONE
NUTRITION       112      0      0     0
HEALTH            0    112      0     0
BOTH              2      0    110     0
NONE              0      1      0   111
```

Accuracy chính xác:

```text
445 / 448 = 0.993303... = 99.33%
```

Slide ghi `99.36%` là sai phép chia và tiêu đề “Training Accuracy” cũng sai scope. Cách gọi đúng: **held-out test accuracy 99.33%**.

Điểm cao không có nghĩa open-world hoàn hảo. Dataset cân bằng, synthetic và label schema rõ nên test cùng distribution tương đối dễ.

### Runtime load model nào?

`configs/config.yaml`:

```yaml
classifier_model_path: "models/intent_model_v2/"
```

`models/intent_model_v2/config.json` xác nhận đủ bốn label. Thư mục `models/classifier_bert/` là artifact cũ, không phải path active.

## 17. NER BioBERT/BERT + CRF

### Kiến trúc

```text
tokens
 -> BERT/BioBERT
 -> vector từng token
 -> Linear emission scores
 -> CRF
 -> Viterbi decode
 -> BIO labels
 -> merge span thành entity
```

CRF loss có thể hiểu:

```text
loss = log tổng điểm của mọi chuỗi hợp lệ - điểm chuỗi gold
```

Viterbi dùng dynamic programming và backpointer để tìm chuỗi tốt nhất mà không thử mọi tổ hợp.

### Kết quả notebook hiện tại

`eval_ner.ipynb` ghi:

```text
DISEASE F1 : 0.9206
FOOD F1    : 0.9868
NUTRIENT F1: 0.9674
Overall F1 : 0.9565
```

Đây là số nên đồng bộ với slide/report nếu protocol notebook là bản chốt. Báo cáo vẫn ghi `0.893`, nên hai tài liệu hiện chưa nhất quán.

---

# Tầng 5 - Runtime theo code

## 18. FastAPI nhận request

[`main/rag_server.py`](../main/rag_server.py):

```python
class AskRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

result = await run_in_threadpool(
    _en_pipeline.answer,
    req.message,
    history_dicts,
)
```

`run_in_threadpool` tránh chặn event loop bởi model inference đồng bộ.

## 19. Thứ tự thật trong `ENPipeline.answer()`

### Bước 1 - NER trước intent

```python
curr_entities = self.ner.predict(query)
```

NER chạy trước để lấy entity hiện tại và hỗ trợ history.

### Bước 2 - Gom entity lịch sử

Pipeline chạy NER trên tối đa các user message gần nhất, giữ tối đa 5 entity mỗi type. Nếu query hiện tại thiếu FOOD/DISEASE, nó backfill từ history.

Đây là **contextual entity accumulation**, không phải LLM query rewriting.

```yaml
use_llm_rewriter: false
```

### Bước 3 - Intent

```python
intent = self.clf.classify(search_query)
```

### Bước 4 - NONE guardrail

```python
if intent == "NONE":
    return {
        "answer": "I'm sorry, ...",
        "intent": "NONE",
        "sources": [],
        "used_llm": False,
    }
```

Đây là early return. SQLite, retriever, reranker và Llama đều không chạy.

### Bước 5 - USDA cho NUTRITION/BOTH

```python
if intent in ("NUTRITION_LOOKUP", "BOTH"):
    nutrition = db.lookup_en(clean_food)
```

### Bước 6 - Retrieval cho HEALTH/BOTH

```python
if intent in ("HEALTH_ADVICE", "BOTH"):
    candidates = self.retriever.retrieve(ret_q, top_k=20)
    chunks = self.reranker.rerank(ret_q, candidates, top_k=self.top_k)
```

`top_k` runtime là 3. Hybrid nhận yêu cầu 20 ứng viên và tự fetch `max(20*4,20)=80` từ mỗi branch trước RRF.

### Bước 7 - Generation

```python
result = self.generator.generate(
    query=query,
    nutrition_data=nutrition,
    health_chunks=chunks,
    query_type=intent,
    history=history,
)
```

## 20. Bốn trace cụ thể

### NUTRITION_LOOKUP

```text
apple + calories
 -> NER FOOD=apple, NUTRIENT=calories
 -> intent NUTRITION_LOOKUP
 -> SQLite USDA
 -> generator fast-path
 -> used_llm=False
```

### HEALTH_ADVICE

```text
salmon + heart health
 -> intent HEALTH_ADVICE
 -> Hybrid retrieval
 -> reranker top 3
 -> Llama + sources
```

### BOTH

```text
protein in salmon + heart health
 -> USDA lookup
 -> medical retrieval + reranker
 -> Llama tổng hợp hai context
```

### NONE

```text
reverse a linked list
 -> intent NONE
 -> static rejection
 -> no DB, no retriever, no LLM
```

---

# Tầng 6 - Embedding, retrieval và reranking

## 21. Vector store

[`src/database/vector_store.py`](../src/database/vector_store.py) dùng MiniLM:

```python
encode(texts, normalize_embeddings=True)
```

Vector chuẩn hóa có độ dài 1. ChromaDB dùng cosine distance. Code đổi distance về score hiển thị:

```python
score = max(0.0, min(1.0, 1 - dist / 2))
```

## 22. TF-IDF và BM25

TF-IDF là baseline: từ hiếm có trọng số cao, dùng cosine giữa vector sparse.

BM25 cải thiện bằng:

- term-frequency saturation: lặp một từ quá nhiều không tăng điểm vô hạn;
- document length normalization: tài liệu dài không được lợi không công bằng.

## 23. Dense MiniLM

Dense retrieval tìm theo ý nghĩa. Nó hỗ trợ trường hợp query dùng từ khác tài liệu, ví dụ `heart disease` gần `cardiovascular condition`.

Điểm yếu: có thể bỏ lỡ thuật ngữ hiếm hoặc mã y khoa mà BM25 bắt tốt.

## 24. Hybrid RRF

[`src/en/retriever.py`](../src/en/retriever.py):

```python
rrf[text] += 1.0 / (RRF_K + rank + 1)
```

Với `RRF_K=10`:

```text
rank 1 trong BM25 -> 1/(10+1)
rank 3 trong Dense -> 1/(10+3)
total              -> cộng hai đóng góp
```

RRF dùng rank vì BM25 score và cosine score không cùng thang đo.

## 25. Cross-encoder reranker

[`src/en/reranker.py`](../src/en/reranker.py):

```python
pairs = [(query, c.text) for c in chunks]
scores = model.predict(pairs)
ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
return ranked[:top_k]
```

Bi-encoder encode query và document riêng, nhanh nhưng tương tác hạn chế. Cross-encoder đưa cả cặp qua attention, chính xác hơn nhưng chậm, nên chỉ rerank tập ứng viên nhỏ.

Runtime có lazy rerank: nếu gap giữa hai candidate đầu đủ lớn (`0.05`), pipeline có thể bỏ qua cross-encoder và lấy top 3 trực tiếp.

---

# Tầng 7 - Đánh giá

## 26. Intent

Dataset: 448 held-out test samples.

```text
Accuracy  = 0.9933
Macro-F1  = 0.9933
```

## 27. NER

Metric đúng là entity-level precision/recall/F1. Một entity chỉ đúng khi boundary và type đúng.

```text
Overall entity F1 = 0.9565
```

## 28. Retrieval

Dataset: 323 NFCorpus test queries + qrels.

MRR@10:

```text
TF-IDF                  0.3796
BM25                    0.5241
Dense MiniLM            0.4991
Dense fine-tuned        0.4685
Hybrid RRF              0.5435
Hybrid RRF + Reranker   0.5754
```

MRR cho mỗi query:

```text
rank 1 -> 1.0
rank 2 -> 0.5
rank 5 -> 0.2
không có relevant doc trong top 10 -> 0
```

Sau đó lấy trung bình 323 query.

MRR 0.5754 không có nghĩa 57.54% answer đúng. Nó chỉ đo vị trí document liên quan đầu tiên.

## 29. Generation

Slide hiện nói generation/end-to-end chưa có benchmark chính thức. Đây là cách nói an toàn nếu không có artifact đánh giá hoàn chỉnh.

Không dùng các số end-to-end cũ như `Hit@5=0.455` hoặc `Token F1=0.042` nếu file kết quả và protocol không còn được xác minh.

## 30. Vì sao đánh giá theo component hợp lý?

- Intent: routing đúng không?
- NER: entity span đúng không?
- Retrieval: document đúng đứng cao không?
- Generation: answer có bám context và đúng trọng tâm không?
- Fast-path: số có khớp USDA và `used_llm=False` không?

Một số duy nhất trộn mọi branch dễ che giấu lỗi và áp metric sai cho query `NONE`/fast-path.

---

# Tầng 8 - Những điểm phải đồng bộ trước khi bảo vệ

## 31. Slide 15-16

1. `57/2400 = 2.375%`, không phải 3.4%.
2. Flow đúng: 2.400 raw -> dedup -> sample 500/class -> 2.000 -> thêm 240 hard -> 2.240.
3. Full-set QA summary mới: `0.325 / 0.152 / 2.137x`.
4. Accuracy đúng: `445/448 = 99.33%`.
5. Gọi là held-out test accuracy, không phải training accuracy.

## 32. Slide/report architecture

Code thật chạy NER/history trước classifier. `Preprocessor` được khởi tạo nhưng không được gọi trong `answer()`.

## 33. Report cần sửa

- intent data cũ 1.500/1.680/3-class;
- intent batch 32/max length 64;
- NER F1 0.893 nếu đã chốt notebook 0.9565;
- reranker top 5 thay vì runtime top 3;
- generator temperature 0.3/num_predict 2000 thay vì code 0.0/700;
- endpoint dùng `req.question` thay vì field thật `req.message`;
- rewriter trong demo dù config đang tắt;
- end-to-end số cũ không còn artifact chắc chắn.

---

# Tầng 9 - Câu hỏi phản biện

## 34. Intent

### Vì sao cần `NONE`?

Để chặn out-of-domain sớm, tránh lãng phí retrieval/LLM và giảm khả năng trả lời linh tinh.

### Vì sao accuracy cao?

Dataset cân bằng, label schema rõ và phần lớn câu synthetic có phrasing nhất quán. Vì vậy phải gọi đây là controlled held-out performance, không phải open-world perfection.

### Dataset do LLM sinh có đáng tin không?

Nhóm thực hiện dedup, balance, semantic separation và hard-template augmentation. Tuy nhiên chưa có đánh giá độc lập quy mô lớn bởi chuyên gia, nên distribution gap với câu hỏi thật vẫn là hạn chế.

## 35. Retrieval

### Vì sao BM25 cao hơn Dense?

NFCorpus có nhiều thuật ngữ y sinh chính xác; lexical matching có lợi. Dense vẫn bổ sung paraphrase, nên Hybrid cao hơn từng branch.

### Vì sao fine-tuned Dense thấp hơn base?

Fine-tuning trên tập nhỏ/hẹp có thể làm mất khả năng tổng quát. Ablation âm vẫn có giá trị vì giúp chọn base model dựa trên số liệu.

### Vì sao không rerank toàn corpus?

Cross-encoder phải đọc từng cặp query-document nên quá chậm. Retriever giảm 3.633 docs xuống một tập nhỏ trước.

## 36. Generation

### Temperature 0 có loại hallucination không?

Không. Nó giảm ngẫu nhiên, không bảo đảm factuality. Grounding, guardrail và fast-path mới là các lớp giảm rủi ro.

### Nếu retrieval sai nhưng LLM bám context thì sao?

Answer có thể faithful với context nhưng vẫn incorrect với câu hỏi. Faithfulness và correctness là hai khái niệm khác nhau.

---

# 37. Tóm tắt 60 giây

> Hệ thống là chatbot dinh dưỡng và sức khỏe với bốn intent. BERT phân luồng sang USDA lookup, health RAG, nhánh kết hợp hoặc NONE guardrail. NER BioBERT/BERT + CRF nhận diện FOOD, DISEASE và NUTRIENT; history entity accumulation hỗ trợ hội thoại mà không bật LLM rewriter. Câu số liệu đi SQLite USDA và có fast-path không qua LLM. Câu sức khỏe đi BM25 và MiniLM, hợp nhất bằng RRF k=10, rồi cross-encoder chọn top 3 cho Llama 3.1:8b. Intent đạt Accuracy/Macro-F1 0.9933 trên 448 held-out samples; NER notebook hiện đạt F1 0.9565; Hybrid+Reranker đạt MRR@10 0.5754 trên 323 NFCorpus queries. Điểm mạnh là routing theo nguồn và đánh giá từng component; giới hạn chính là intent data synthetic và generation chưa có benchmark chính thức hoàn chỉnh.

## 38. Checklist trước demo

- [ ] `models/intent_model_v2/config.json` có đủ 4 labels.
- [ ] `models/ner_bert/` load được CRF model.
- [ ] `data/usda_food.db` tồn tại.
- [ ] Chroma collection có dữ liệu.
- [ ] Ollama có `llama3.1:8b`.
- [ ] `/health` trả `pipeline_ready=true`.
- [ ] Test đủ 4 intent.
- [ ] Slide dùng `99.33%`, không phải `99.36%`.
- [ ] Không gọi 57/2400 là 3.4%.
- [ ] Không claim rewriter đang chạy.
- [ ] Không claim generation đã có benchmark nếu chưa có artifact.
