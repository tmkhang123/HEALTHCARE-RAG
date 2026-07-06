# Hướng dẫn chuyên sâu TV1 - Slide 15 đến 19

> Phần phụ trách: Intent Dataset, Intent Classifier, Embedding/Vector Store, Hybrid Retrieval và Cross-Encoder Reranker.  
> Đối chiếu với slide PDF mới, code runtime, model config và output notebook ngày 22/06/2026.

---

## 0. Câu chuyện chung của 5 slide

Năm slide không phải năm chủ đề rời nhau. Chúng tạo thành một chuỗi:

```text
Slide 15: tạo dữ liệu để model hiểu 4 loại câu hỏi
Slide 16: train BERT để route đúng đường xử lý
Slide 17: biểu diễn tài liệu bằng vector để tìm theo ngữ nghĩa
Slide 18: kết hợp lexical + semantic retrieval bằng RRF
Slide 19: đọc kỹ ứng viên bằng cross-encoder để chọn top 3
```

Một câu chuyển ý tốt:

> Sau khi intent classifier quyết định câu hỏi cần đi nhánh health RAG, vấn đề tiếp theo là tìm đúng bằng chứng y khoa. Vì vậy em chuyển từ phần routing sang embedding, hybrid retrieval và reranking.

## 1. Năm chỉnh sửa bắt buộc trước khi trình bày

| Slide | Đang ghi | Sự thật từ code/notebook | Nên sửa |
|---|---|---|---|
| 15 | `-57 (3.4%)` | `57/2400 = 2.375%` | Bỏ phần trăm hoặc ghi `2.4%` |
| 15 | `2,400 + 240 -> 2,240` dễ gây hiểu nhầm | 2.400 raw -> dedup -> sample 500/class = 2.000 -> thêm 240 hard = 2.240 | Vẽ đủ bốn bước |
| 15 | separation `0.258/0.126/2.05x` | QA summary của file 2.240: `0.325/0.152/2.137x` | Chọn một lần chạy có provenance; ưu tiên summary mới |
| 16 | `Training Accuracy 99.36%` | 445/448 = 99.3304% trên held-out test | Ghi `Held-out Test Accuracy 99.33%` |
| 19 | `sorted(zip(...), reverse=True)` | code thật có `key=lambda x: x[0]` | Chụp code thật hoặc sửa snippet |

Ngoài ra slide 17 ghi “chunking” nhưng corpus benchmark hiện được load theo document title + abstract. Không nên mô tả một chunking pipeline nếu không chỉ được code thực thi tương ứng.

---

# Slide 15 - Intent Dataset Construction

## 2. Slide này phải chứng minh điều gì?

Slide cần trả lời bốn câu hỏi:

1. Vì sao nhóm tự tạo dataset?
2. Bốn nhãn nghĩa là gì?
3. Dataset được làm sạch/cân bằng thế nào?
4. Nhóm có kiểm tra chất lượng trước training không?

## 3. Bốn intent và ranh giới

### `NUTRITION_LOOKUP`

Người dùng yêu cầu số dinh dưỡng cụ thể.

```text
How much protein is in salmon?
How many calories are in an apple?
```

Route: USDA SQLite, có thể fast-path không LLM.

### `HEALTH_ADVICE`

Người dùng hỏi tác dụng, an toàn, bệnh lý hoặc lời khuyên; không hỏi số USDA.

```text
Is ginger safe during pregnancy?
Can salmon support heart health?
```

Route: NFCorpus -> Hybrid Retrieval -> Reranker -> Llama.

### `BOTH`

Câu hỏi thật sự cần cả số liệu và phân tích sức khỏe.

```text
How much protein is in salmon, and is it good for heart health?
```

Route: USDA + health RAG, rồi Llama tổng hợp.

### `NONE`

Câu hỏi ngoài miền.

```text
How do I reverse a linked list in Python?
```

Route: trả reject tĩnh, không DB/retrieval/LLM.

## 4. Vì sao không có public dataset phù hợp?

Các public datasets có thể có topic classification hoặc medical intent, nhưng không khớp chính xác routing schema do nhóm thiết kế:

```text
nutrition exact lookup / health advice / both / out-of-domain
```

Vì vậy nhóm dùng một custom LLM-assisted dataset. Cách nói trung thực:

> Nhóm không tìm thấy public dataset khớp đúng bốn nhãn routing, nên xây custom dataset có LLM hỗ trợ, sau đó kiểm tra duplicate, balance và semantic separation. Đây là controlled dataset, không phải public benchmark.

Repo hiện giữ raw CSV và notebook pipeline, nhưng không giữ đầy đủ prompt/call log gốc đã sinh 2.400 raw queries. Nếu bị hỏi provenance sâu, không nên bịa prompt.

## 5. Flow tạo đúng dataset 2.240

```text
Raw LLM-assisted
2.400 = 600/class
       |
       v
MinHash LSH near-duplicate filtering
slide ghi loại 57
       |
       v
Downsample cân bằng
500/class = 2.000
       |
       v
Rule/template hard augmentation
60/class = 240
       |
       v
Final train file
560/class = 2.240
```

Điều phải nhớ:

- `2.400 -> 2.000` không có nghĩa xóa 400 duplicate.
- Sau dedup, notebook lấy 500 câu mỗi class để cân bằng.
- Sau đó mới cộng 240 hard examples.

## 6. MinHash LSH dễ hiểu

### Vấn đề

LLM thường sinh nhiều câu thay đổi vài từ:

```text
How many calories are in an apple?
What is the calorie amount in apple?
```

Nếu câu gần trùng rơi vào cả train và test, metric có thể đẹp giả tạo.

### Code thật

Notebook: `notebooks/en/build_intent_pipeline.ipynb`.

```python
def get_minhash(text, num_perm=128):
    m = MinHash(num_perm=num_perm)
    words = re.findall(r"\w+", str(text).lower())
    for word in words:
        m.update(word.encode("utf8"))
    return m

lsh = MinHashLSH(threshold=0.85, num_perm=128)
drop_indices = set()

for idx, row in raw_df.iterrows():
    signature = get_minhash(row["text"])
    if lsh.query(signature):
        drop_indices.add(idx)
    else:
        lsh.insert(idx, signature)
```

### Giải thích từng phần

- `re.findall(r"\w+")`: lấy token đơn giản.
- `MinHash`: tạo chữ ký xấp xỉ Jaccard similarity.
- `num_perm=128`: số phép hoán vị dùng cho chữ ký; lớn hơn thường ổn định hơn nhưng tốn hơn.
- `threshold=0.85`: chỉ đánh dấu khi hai tập token rất giống.
- `LSH`: giảm việc phải so sánh mọi cặp `O(n^2)`.

MinHash không kiểm tra label đúng. Nó chỉ kiểm tra lặp nội dung.

## 7. Balance và hard augmentation

### Balance

```python
balanced_llm_df = (
    clean_llm_df.groupby("label")
    .apply(lambda x: x.sample(n=500, random_state=42))
    .reset_index(drop=True)
)
```

Nếu một class có nhiều câu hơn, model dễ học thiên lệch. Lấy 500/class làm phần LLM đồng đều.

### Hard examples

Notebook tạo 60 mẫu/class bằng template. Ví dụ `BOTH`:

```python
for food in FOODS:
    for nutrient in NUTRIENTS:
        for condition in CONDITIONS:
            text = (
                f"How much {nutrient} is in {food}, "
                f"and is it safe for {condition}?"
            )
```

Hard examples tập trung vào ranh giới dễ nhầm:

- có food nhưng chỉ hỏi health -> `HEALTH_ADVICE`;
- vừa hỏi nutrient number vừa health -> `BOTH`;
- câu hoàn toàn ngoài miền -> `NONE`.

## 8. Dataset QA đo gì?

### Exact duplicate

```python
exact_dupes = final_df.duplicated("text").sum()
```

Summary hiện tại: `0` exact duplicates.

### Semantic separation

Mỗi câu được embed. Sau đó tính cosine similarity cho cặp cùng class và khác class.

```python
same_label = labels[:, None] == labels[None, :]
diff_label = labels[:, None] != labels[None, :]

within_avg = sim_matrix[same_label].mean()
between_avg = sim_matrix[diff_label].mean()
ratio = within_avg / between_avg
```

Summary của file cuối 2.240:

```text
within_avg  = 0.3252
between_avg = 0.1522
ratio       = 2.1368x
```

Giải thích:

> Trung bình các câu cùng intent gần nhau hơn khoảng 2,14 lần so với các câu khác intent. Đây là tín hiệu bốn class có cấu trúc phân biệt, không phải bằng chứng label accuracy 100%.

## 9. Kịch bản nói slide 15

> Vì hệ thống có bốn routing path riêng nên nhóm cần một intent dataset đúng với thiết kế này, nhưng không có public dataset khớp bốn nhãn. Nhóm tạo 2.400 raw queries có LLM hỗ trợ, 600 câu mỗi nhãn. Sau đó dùng MinHash LSH ngưỡng 0,85 để phát hiện near-duplicate, rồi lấy cân bằng 500 câu mỗi nhãn. Nhóm bổ sung 60 hard examples mỗi nhãn để làm rõ các ranh giới khó, đặc biệt HEALTH_ADVICE với BOTH và câu ngoài miền NONE. File cuối có 2.240 câu, 560 câu mỗi class và không có exact duplicate. Kiểm tra embedding trên file cuối cho within-class 0,325, between-class 0,152, ratio khoảng 2,14 lần. Con số này cho thấy class có tín hiệu phân biệt, nhưng nhóm vẫn xem đây là controlled synthetic dataset chứ không phải benchmark ngoài thực tế.

Thời lượng hợp lý: 75-90 giây.

## 10. Câu hỏi khó slide 15

### “57 câu là exact duplicate hay near-duplicate?”

Near-duplicate do MinHash LSH ước lượng độ giống tập token. Exact duplicate của file cuối được kiểm riêng và bằng 0.

### “Vì sao 2.400 trừ 57 không bằng 2.000?”

Vì sau dedup nhóm còn downsample mỗi class về 500 để cân bằng. 2.000 là balanced LLM subset, không phải chỉ là kết quả phép trừ duplicate.

### “Hard examples có phải người đánh nhãn thủ công?”

Không hoàn toàn. Notebook sinh chúng bằng rule/template với label xác định theo cấu trúc câu. Đây là augmentation có kiểm soát, không phải expert annotation độc lập.

### “Semantic separation có chứng minh dataset đúng không?”

Không. Nó chỉ đo cấu trúc hình học của embedding. Label correctness vẫn cần review mẫu hoặc dữ liệu thật độc lập.

---

# Slide 16 - Intent Classifier Training & Evaluation

## 11. Tên slide nên sửa

Tiêu đề tốt nhất:

```text
Intent Classifier - Training & Held-out Evaluation
```

Headline metric:

```text
Held-out Test Accuracy: 99.33%
Macro-F1: 99.33%
```

Không gọi 99.33% là training accuracy vì nó được tính trên 448 held-out samples.

## 12. Standard stratified 80/20 split

```python
train_df, test_df = train_test_split(
    df,
    test_size=0.2,
    random_state=42,
    stratify=df["label"],
)
```

Kết quả:

```text
Total : 2.240 = 560/class
Train : 1.792 = 448/class
Test  :   448 = 112/class
```

`stratify` giữ tỷ lệ class giống nhau. Test được tách trước training nên gọi là held-out test.

## 13. Tại sao dùng BERT sequence classification?

Đây là bài toán:

```text
whole sentence -> exactly one label
```

BERT phù hợp hơn keyword rules vì nó hiểu quan hệ trong câu:

```text
Can ginger help nausea during pregnancy?
```

Có food/herb và condition nhưng mục đích chỉ là health advice.

So với dùng Llama để route:

- BERT nhỏ hơn;
- deterministic hơn;
- nhanh hơn;
- không cần prompt/API mỗi request;
- output cố định bốn class.

## 14. Cấu hình training

```python
LABELS = [
    "NUTRITION_LOOKUP",
    "HEALTH_ADVICE",
    "BOTH",
    "NONE",
]
MODEL_NAME = "bert-base-uncased"
MAX_LENGTH = 128
BATCH_SIZE = 16
EPOCHS = 3
LR = 2e-5
```

Đây là đoạn code nên chụp vì nó đồng thời chứng minh tên model, số class và hyperparameters.

## 15. Pipeline training

```text
text
 -> WordPiece tokenizer
 -> input_ids + attention_mask
 -> BERT encoder 12 layers
 -> [CLS] 768 dimensions
 -> Linear classifier 4 outputs
 -> logits
 -> CrossEntropyLoss
 -> backprop + AdamW
```

### Model head

```python
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(LABELS),
    id2label=ID2LABEL,
    label2id=LABEL2ID,
)
```

`num_labels=4` làm classification head có bốn output.

### Training loop

```python
out = model(
    input_ids=input_ids,
    attention_mask=attention_mask,
    labels=labels,
)
out.loss.backward()
optimizer.step()
optimizer.zero_grad()
```

Hugging Face tự tính CrossEntropyLoss khi có `labels`.

## 16. CrossEntropyLoss bằng ví dụ

Giả sử gold label là `BOTH`, model dự đoán:

```text
NUTRITION 0.50
HEALTH    0.20
BOTH      0.25
NONE      0.05
```

Loss gần đúng:

```text
-log(0.25)
```

Model bị phạt vì xác suất của class đúng còn thấp. Backpropagation tính gradient để tăng logit `BOTH` và điều chỉnh các trọng số liên quan.

## 17. Kết quả chính xác

Notebook output:

```text
test accuracy = 0.9933
test macro_f1 = 0.9933
```

```text
445 correct / 448 total = 99.3304%
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

Ba lỗi:

- 2 câu `BOTH` bị dự đoán thành `NUTRITION_LOOKUP`;
- 1 câu `NONE` bị dự đoán thành `HEALTH_ADVICE`.

Không phải “hai boundary errors”; tổng là ba.

## 18. Vì sao điểm cao?

1. Class cân bằng hoàn toàn.
2. Label schema được thiết kế rõ.
3. Synthetic phrasing có tính nhất quán.
4. Semantic separation khoảng 2.14x.
5. BERT đã pretrain và chỉ cần fine-tune cho routing hẹp.

Điểm cao chưa chứng minh:

- mọi câu người dùng thật đều đúng;
- tiếng Việt hoạt động;
- model không bị distribution shift;
- label data được chuyên gia xác nhận 100%.

## 19. Runtime checkpoint

Config thật:

```yaml
classifier_model_path: "models/intent_model_v2/"
```

Model config thật:

```json
{
  "0": "NUTRITION_LOOKUP",
  "1": "HEALTH_ADVICE",
  "2": "BOTH",
  "3": "NONE"
}
```

`src/en/classifier.py` vẫn có docstring cũ nói “3-class”, nhưng constant và model runtime là bốn class. Đây là comment stale, không phải logic runtime.

## 20. Kịch bản nói slide 16

> Dataset 2.240 câu được chia stratified 80/20, nên train có 1.792 câu và held-out test có 448 câu, mỗi class giữ tỷ lệ bằng nhau. Nhóm fine-tune bert-base-uncased với max length 128, batch 16, 3 epoch, learning rate 2e-5 và AdamW. Query được WordPiece tokenize, đi qua 12 lớp BERT; vector CLS 768 chiều được đưa vào linear head bốn output. Khi training, Hugging Face tính CrossEntropyLoss và backpropagation cập nhật trọng số. Trên held-out test, model đúng 445 trên 448 câu, tương ứng Accuracy và Macro-F1 đều khoảng 99,33%. Điểm cao phản ánh controlled balanced dataset có ranh giới rõ, không phải tuyên bố model hoàn hảo ngoài thực tế.

Thời lượng hợp lý: 75-90 giây.

## 21. Câu hỏi khó slide 16

### “Vì sao không có validation set riêng?”

Notebook bản chốt dùng standard train/test 80/20 để có protocol đơn giản. Nếu tune nhiều hyperparameters dựa trên test thì sẽ gây leakage; trong bản hiện tại nhóm dùng cấu hình cố định và báo held-out test. Với nghiên cứu lớn hơn nên có train/validation/test.

### “99.33% có overfit không?”

Training loss giảm nhanh và controlled test rất cao. Chưa thể kết luận overfit chỉ từ accuracy; cần dữ liệu người dùng thật/out-of-distribution để kiểm. Nhóm thừa nhận synthetic distribution là hạn chế.

### “Accuracy hay Macro-F1 quan trọng hơn?”

Dataset cân bằng nên hai số gần nhau. Macro-F1 vẫn tốt vì buộc nhìn chất lượng từng class ngang nhau.

### “Nếu model không load?”

`QueryClassifier` có fallback keyword rules. Tuy nhiên demo chuẩn phải load `models/intent_model_v2`, vì rules chỉ là phương án dự phòng.

---

# Slide 17 - Embedding & Vector Store

## 22. Embedding giải quyết gì?

BM25 cần từ khóa trùng. Dense embedding hỗ trợ synonym/paraphrase:

```text
heart disease
cardiovascular condition
```

Hai câu có thể không trùng token nhưng gần nhau trong vector space.

## 23. MiniLM biến text thành vector

Runtime config:

```yaml
embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
```

Output là vector 384 chiều. Không nên cố gán ý nghĩa cụ thể cho từng chiều; ý nghĩa nằm ở toàn vector.

Code:

```python
def embed(self, texts):
    return self._get_embedder().encode(
        texts,
        normalize_embeddings=True,
    ).tolist()
```

`normalize_embeddings=True` đưa vector về độ dài 1, phù hợp cosine similarity.

## 24. ChromaDB lưu gì?

```python
collection.add(
    ids=[c["id"] for c in chunks],
    embeddings=self.embed(texts),
    documents=texts,
    metadatas=[{"source": c["source"]} for c in chunks],
)
```

Chroma lưu:

- ID;
- embedding;
- document text;
- metadata `source`.

Report đang nói có `chunk_index`, nhưng code hiện chỉ lưu `source`.

## 25. ANN/HNSW

Chroma collection được tạo với:

```python
metadata={"hnsw:space": "cosine"}
```

HNSW là Approximate Nearest Neighbor index. Nó đổi một ít tính chính xác tuyệt đối để tìm top-k nhanh hơn quét toàn bộ vector.

## 26. Cosine distance trong code

Chroma trả cosine distance; code đổi về score hiển thị:

```python
score = max(0.0, min(1.0, 1 - dist / 2))
```

Đây là score runtime của vector branch, không phải RRF score và không phải reranker score.

## 27. Corpus và “chunking”

NFCorpus benchmark có 3.633 documents. Runtime corpus có thể chứa document bổ sung, nhưng benchmark 323 query phải dùng corpus/qrels NFCorpus nhất quán.

Nếu loader đang index mỗi `title + abstract` như một document, hãy nói “document/passages” thay vì khẳng định đã chunk 500/100. `chunk_size` trong config chưa chứng minh chunking được gọi trong flow hiện tại.

## 28. Kịch bản nói slide 17

> Dense retrieval dùng all-MiniLM-L6-v2 để biến query và tài liệu thành vector 384 chiều. Vì vector biểu diễn ngữ nghĩa, các cụm như heart disease và cardiovascular condition có thể nằm gần nhau dù không trùng từ. Vector được chuẩn hóa và lưu trong ChromaDB cùng document text và source metadata; Chroma dùng HNSW cosine index để tìm top-k gần nhất nhanh hơn quét toàn corpus. Dense branch bổ sung cho BM25 ở các câu paraphrase, nhưng không thay thế BM25 vì semantic model vẫn có thể bỏ lỡ thuật ngữ hiếm.

## 29. Câu hỏi khó slide 17

### “384 chiều có nghĩa gì?”

Đó là kích thước output của MiniLM. Từng chiều không có nhãn dễ diễn giải; quan hệ giữa toàn bộ vector mới mang ý nghĩa.

### “Dense có luôn tốt hơn BM25 không?”

Không. Trên NFCorpus, BM25 0.5241 cao hơn Dense 0.4991 vì thuật ngữ y sinh chính xác có lợi cho lexical matching.

### “Fine-tuned embedding có đang chạy không?”

Không. Model domain có trên ổ đĩa nhưng config runtime chọn base `all-MiniLM-L6-v2`, phù hợp ablation vì Dense FT thấp hơn.

---

# Slide 18 - Hybrid Retrieval

## 30. Bốn phương pháp được so sánh

### TF-IDF

Baseline sparse. Mỗi document là vector trọng số từ/ngram; cosine similarity xếp hạng.

```python
TfidfVectorizer(max_features=20_000, ngram_range=(1, 2))
```

### BM25

Sparse lexical retrieval có term saturation và document length normalization. Tốt với thuật ngữ hiếm như `HbA1c`, `omega-3`.

### Dense MiniLM

Semantic retrieval qua 384D embedding và ChromaDB. Tốt với synonym/paraphrase.

### Hybrid RRF

Kết hợp rank của BM25 và Dense, không cộng raw score.

## 31. Vì sao không cộng raw scores?

BM25 score và cosine score khác thang đo. Cộng trực tiếp cần calibration/weight tuning. RRF chỉ dùng vị trí:

```python
rrf[text] += 1.0 / (RRF_K + rank + 1)
```

`enumerate` bắt đầu rank 0, nên `+1` đổi về rank 1-based.

## 32. RRF tính tay

Giả sử document A:

- rank 1 BM25;
- rank 3 Dense;
- `k=10`.

```text
RRF(A) = 1/(10+1) + 1/(10+3)
       = 0.0909 + 0.0769
       = 0.1678
```

Document xuất hiện ở cả hai list được cộng hai đóng góp.

## 33. Candidate expansion thật

```python
fetch_k = max(top_k * 4, 20)
bm25_hits = self.bm25.retrieve(query, top_k=fetch_k)
dense_hits = self.dense.retrieve(query, top_k=fetch_k)
```

Runtime pipeline gọi:

```python
HybridRetriever.retrieve(query, top_k=20)
```

Do đó bên trong hybrid:

```text
fetch_k = max(20*4, 20) = 80
```

Tức là BM25 và Dense lấy tối đa 80 ứng viên mỗi branch, RRF hợp nhất rồi trả 20 ứng viên cho reranker. Slide “top 20 each” là bản đơn giản hóa, không đúng hoàn toàn code hiện tại.

## 34. MRR@10 và qrels

Benchmark dùng:

- 323 query NFCorpus test;
- qrels nối query với relevant document IDs;
- top 10 kết quả của từng method.

Pseudo-code đánh giá:

```python
scores = []

for query in queries:
    ranked_docs = retriever.search(query, top_k=10)
    gold_docs = qrels[query]

    first_rank = None
    for rank, doc_id in enumerate(ranked_docs, start=1):
        if doc_id in gold_docs:
            first_rank = rank
            break

    scores.append(0.0 if first_rank is None else 1.0 / first_rank)

mrr_at_10 = mean(scores)
```

## 35. Đọc ablation table

```text
TF-IDF                 0.3796
BM25                   0.5241
Dense vector           0.4991
Dense FT               0.4685
Hybrid RRF             0.5435
Hybrid RRF + Reranker  0.5754
```

Kết luận hợp lý:

1. BM25 mạnh trên biomedical terminology.
2. Dense có ích nhưng không thắng BM25 riêng lẻ.
3. Dense FT giảm, nên không active ở runtime.
4. Hybrid thắng từng branch vì chúng bù lỗi cho nhau.
5. Reranker tiếp tục cải thiện vị trí relevant document.

## 36. Kịch bản nói slide 18

> Nhóm so sánh bốn hướng retrieval trên đúng 323 test queries của NFCorpus bằng MRR@10. TF-IDF là baseline, BM25 thêm term saturation và length normalization nên đạt 0,5241. Dense MiniLM tìm theo ngữ nghĩa đạt 0,4991; thấp hơn BM25 vì corpus có nhiều thuật ngữ y sinh chính xác. Hybrid dùng RRF k bằng 10 để cộng đóng góp theo rank, tránh cộng BM25 score và cosine score khác thang đo. Hybrid đạt 0,5435, cho thấy lexical và semantic branch bù trừ nhau. Sau reranker, MRR tăng tiếp lên 0,5754.

## 37. Câu hỏi khó slide 18

### “MRR 0.5754 có nghĩa 57.54% câu đúng?”

Không. Nó là trung bình reciprocal rank của relevant document đầu tiên trong top 10.

### “Tại sao k của RRF là 10?”

Đây là hyperparameter chọn cho corpus nhỏ và được giữ cố định trong ablation. K nhỏ làm chênh lệch top ranks rõ hơn. Không nên nói nó là chuẩn duy nhất.

### “Dense FT thấp có phải thất bại?”

Là thí nghiệm âm có giá trị. Nó chứng minh fine-tune trên tập nhỏ/hẹp không luôn tốt hơn base và giúp nhóm chọn runtime model dựa trên evidence.

---

# Slide 19 - Cross-Encoder Reranker

## 38. Tại sao retriever chưa đủ?

Retriever ưu tiên recall và tốc độ: tìm ứng viên rộng. Một document có thể cùng chủ đề nhưng không trực tiếp trả lời câu hỏi.

Reranker ưu tiên precision ở đầu danh sách: đọc cặp query-document để đưa evidence tốt hơn lên top.

## 39. Bi-encoder và cross-encoder

### Bi-encoder

```text
query -> vector q
doc   -> vector d
score = cosine(q, d)
```

Document vectors có thể cache/index, nên tìm kiếm nhanh.

### Cross-encoder

```text
[CLS] query [SEP] document [SEP]
          -> Transformer attention
          -> relevance score
```

Query và doc nhìn thấy nhau trong cùng forward pass. Chính xác hơn nhưng phải chạy một lần cho từng pair.

## 40. Model và code runtime

```yaml
reranker_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
top_k: 3
```

```python
def rerank(self, query, chunks, top_k=3):
    if not chunks:
        return []

    model = self._get_model()
    pairs = [(query, c.text) for c in chunks]
    scores = model.predict(pairs)

    ranked = sorted(
        zip(scores, chunks),
        key=lambda x: x[0],
        reverse=True,
    )
    return [
        RetrievedChunk(text=c.text, source=c.source, score=float(score))
        for score, c in ranked[:top_k]
    ]
```

Giải thích:

1. Lazy load model ở request đầu tiên.
2. Tạo 20 `(query, document)` pairs từ Hybrid output.
3. `predict()` trả relevance score.
4. Sort giảm dần theo score bằng `key=lambda x: x[0]`.
5. Trả top 3 cho generator.

## 41. Candidate funnel chính xác

```text
3.633 NFCorpus documents
  -> BM25 top 80 + Dense top 80
  -> RRF merged top 20
  -> Cross-encoder scores 20 pairs
  -> runtime top 3 contexts
  -> Llama
```

Trong evaluation MRR@10, reranker phải trả top 10 để đo đúng cutoff 10. Runtime top 3 và evaluation top 10 phục vụ hai mục đích khác nhau, không mâu thuẫn.

## 42. Lazy rerank

Pipeline có tối ưu:

```python
if (
    lazy_rerank
    and len(candidates) > 1
    and candidates[0].score - candidates[1].score >= 0.05
):
    chunks = candidates[:3]
else:
    chunks = reranker.rerank(query, candidates, top_k=3)
```

Nếu Hybrid đã rất tự tin, có thể bỏ cross-encoder để giảm latency. Ngưỡng `0.05` là heuristic, chưa phải giá trị được chứng minh tối ưu bằng ablation.

## 43. Hiệu quả reranker

```text
Hybrid RRF              0.5435
Hybrid RRF + Reranker   0.5754
Absolute gain           0.0319
Relative gain           0.0319 / 0.5435 ≈ 5.87%
```

Không gọi `0.0319` là “3.19%” nếu không nói rõ đó là absolute MRR points. Cách nói tốt:

> MRR@10 tăng 0,0319 điểm, tương đương khoảng 5,9% tương đối so với Hybrid RRF.

## 44. Kịch bản nói slide 19

> Hybrid retriever tìm ứng viên nhanh nhưng vẫn có document chỉ cùng chủ đề, chưa chắc chứa bằng chứng tốt nhất. Vì vậy nhóm dùng cross-encoder ms-marco-MiniLM-L-6-v2. Khác bi-encoder encode query và document riêng, cross-encoder đưa cả cặp vào cùng Transformer để attention đọc tương tác trực tiếp và cho một relevance score. Runtime lấy top 20 từ Hybrid, reranker chấm 20 pairs rồi chọn top 3 cho Llama. Trên benchmark 323 query, MRR@10 tăng từ 0,5435 lên 0,5754, tức tăng 0,0319 điểm. Chi phí là latency cao hơn, nên hệ thống chỉ rerank tập ứng viên nhỏ và còn có lazy-rerank để bypass khi Hybrid đủ tự tin.

## 45. Câu hỏi khó slide 19

### “Tại sao không dùng cross-encoder trên 3.633 docs?”

Vì mỗi document cần một forward pass theo pair. 3.633 pairs mỗi query quá chậm; retrieve-then-rerank là kiến trúc funnel chuẩn.

### “Reranker có fine-tune không?”

Runtime đang dùng pretrained MS MARCO model. Folder domain model có tồn tại nhưng config không active vì chưa có bằng chứng nó vượt base trong benchmark chốt.

### “Reranker có tăng recall không?”

Nó không tạo ứng viên mới. Nếu relevant doc không nằm trong candidate set, reranker không thể cứu. Nó chủ yếu cải thiện ordering/precision ở top.

### “Top 20 hay top 3?”

Top 20 là input candidate count của cross-encoder. Top 3 là output runtime gửi cho generator. Evaluation dùng top 10 để tính MRR@10.

---

# 46. Lời thuyết trình liền mạch 5 slide

> Trước hết, hệ thống cần route bốn loại câu hỏi: tra số USDA, health advice, câu kết hợp và out-of-domain. Vì không có public dataset khớp schema này, nhóm tạo 2.400 raw queries có LLM hỗ trợ, deduplicate bằng MinHash LSH, lấy cân bằng 500 câu mỗi class và thêm 60 hard examples mỗi class. Dataset cuối có 2.240 câu, 560 mỗi nhãn. QA summary cho thấy không có exact duplicate và within-class similarity cao hơn between-class khoảng 2,14 lần.
>
> Nhóm chia stratified 80/20 và fine-tune bert-base-uncased bốn class. Query được WordPiece tokenize tối đa 128 token, đi qua BERT 12 lớp; vector CLS được đưa vào linear head và train bằng CrossEntropyLoss với AdamW. Trên 448 held-out samples, model đúng 445 câu, Accuracy và Macro-F1 đều khoảng 99,33%. Đây là controlled performance trên synthetic distribution, không phải open-world perfection.
>
> Khi intent yêu cầu health advice, hệ thống cần tìm bằng chứng. Dense branch dùng all-MiniLM-L6-v2 tạo vector 384 chiều và ChromaDB HNSW tìm theo cosine similarity. Dense bắt paraphrase tốt, còn BM25 bắt thuật ngữ hiếm tốt. Nhóm kết hợp hai rank list bằng RRF k bằng 10. Trên 323 NFCorpus queries, Hybrid đạt MRR@10 0,5435, cao hơn BM25 và Dense riêng lẻ.
>
> Cuối cùng, cross-encoder đọc trực tiếp từng cặp query-document trong top 20, sắp lại và chọn top 3 cho Llama. Reranking nâng MRR@10 lên 0,5754. Như vậy toàn phần của em đi từ dữ liệu routing, model routing, đến hai tầng tìm và lọc evidence trước generation.

---

# 47. Checklist học của TV1

- [ ] Phân biệt rõ 4 intent bằng yêu cầu của người dùng, không bằng từ khóa đơn lẻ.
- [ ] Giải thích được `2.400 -> 2.000 -> 2.240`.
- [ ] Không nói 57/2400 là 3.4%.
- [ ] Nhớ QA summary mới `0.325 / 0.152 / 2.137x`.
- [ ] Nhớ split `1.792/448`, mỗi class `448/112`.
- [ ] Nhớ `445/448 = 99.33%`.
- [ ] Giải thích được `[CLS] -> Linear(768,4)`.
- [ ] Giải thích được CrossEntropyLoss và AdamW ở mức ý tưởng.
- [ ] Phân biệt BM25, Dense, RRF, Cross-encoder.
- [ ] Tính tay được một RRF score.
- [ ] Giải thích MRR@10 không phải answer accuracy.
- [ ] Phân biệt candidate top 20, runtime top 3 và evaluation top 10.
- [ ] Nói được một hạn chế của synthetic intent data và một hạn chế của retrieval.
