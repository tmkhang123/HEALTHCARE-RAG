# Hướng dẫn chuyên sâu TV3 - Slide 20 đến 23

> Phần phụ trách: Generation, USDA fast-path, NONE guardrail, kết luận và live demo.  
> Đối chiếu với code runtime và slide PDF ngày 22/06/2026.

---

## 0. Bản đồ phần trình bày

```text
Slide 20: Sau retrieval/reranking, hệ thống tạo answer như thế nào?
Slide 21: Kết quả, giới hạn và hướng phát triển
Slide 22: Demo bốn intent và bốn đường đi
Slide 23: Kết thúc
```

Phần này không cần giải thích lại BM25/RRF. Chỉ cần nối từ slide 19:

> Sau khi reranker chọn top 3 evidence tốt nhất, pipeline quyết định trả lời trực tiếp từ USDA, gọi Llama với context, hoặc chặn câu hỏi ngoài miền.

---

# Slide 20 - Generation & USDA Fast-path

## 1. Bốn intent nhưng ba nhóm xử lý

Slide gọi “3 output branches” là hợp lý nếu hiểu như sau:

| Nhóm xử lý | Intent | Cách trả lời |
|---|---|---|
| USDA fast-path | `NUTRITION_LOOKUP` | format số từ SQLite, không LLM |
| LLM + RAG | `HEALTH_ADVICE`, `BOTH` | Llama đọc top 3 context; BOTH có thêm USDA |
| Guardrail | `NONE` | static rejection, không DB/retrieval/LLM |

`BOTH` vẫn là intent riêng, nhưng dùng cùng generation component với health path.

## 2. NONE guardrail chạy trước mọi tác vụ nặng

File: `src/en/pipeline.py`.

```python
intent = self.clf.classify(search_query)

if intent == "NONE":
    return {
        "answer": (
            "I'm sorry, I am a healthcare and nutrition assistant. "
            "I can only answer questions related to food, nutrition, and health."
        ),
        "intent": "NONE",
        "entities": curr_entities,
        "sources": [],
        "used_llm": False,
    }
```

Đây là early return:

```text
classify NONE
 -> không USDA
 -> không Chroma/BM25
 -> không reranker
 -> không Ollama
```

Không nên cam kết `<100 ms` nếu chưa có latency benchmark riêng. Chỉ cần nói nhanh hơn rõ rệt vì không gọi các component nặng.

## 3. USDA lookup được kích hoạt thế nào?

```python
if intent in ("NUTRITION_LOOKUP", "BOTH"):
    foods = entities_for_lookup.get("FOOD", [])
    cleaned_foods = []

    for food in foods:
        cleaned = _clean_food_entity(food)
        if cleaned and cleaned not in cleaned_foods:
            cleaned_foods.append(cleaned)

    for food in cleaned_foods[:3]:
        nutrition.append(self.db.lookup_en(food))
```

Ý nghĩa:

1. Chỉ nutrition hoặc BOTH mới tra USDA.
2. NER cung cấp FOOD.
3. `_clean_food_entity()` bỏ đơn vị/ký tự làm bẩn tên food.
4. Hệ thống tra tối đa ba food để hỗ trợ comparison.
5. Nếu NER không tìm được food, pipeline có spaCy noun-chunk fallback.

## 4. Điều kiện fast-path

File: `src/generation/generator.py`.

Ý tưởng code:

```python
if query_type == "NUTRITION_LOOKUP" and single_nutrition:
    answer = self._format_nutrition_answer(single_nutrition)
    return {
        "answer": answer,
        "sources": sources,
        "used_llm": False,
    }
```

Fast-path chỉ phù hợp khi:

- intent là nutrition-only;
- có đúng một record dinh dưỡng hợp lệ;
- không cần LLM tổng hợp health evidence.

`BOTH` không dùng fast-path hoàn toàn vì vẫn cần Llama tổng hợp phần health, dù số USDA được lấy xác định trước.

## 5. Fast-path trả format gì?

Hàm `_format_nutrition_answer()` dựng Markdown bằng Python. Output hiện là structured Markdown/bullets, không nên gọi chắc chắn là “Markdown table” nếu code không tạo bảng.

Điểm quan trọng không phải hình thức bảng, mà là:

```text
SQLite values -> deterministic string formatting -> answer
```

Không có token generation nên LLM không thể thay đổi số USDA.

## 6. Cách nói đúng về hallucination

Không nói:

> Fast-path có zero hallucination tuyệt đối.

Nên nói:

> Fast-path không có LLM numeric hallucination vì số được format trực tiếp từ USDA. Rủi ro còn lại là NER hoặc fuzzy matching chọn sai food record.

Ví dụ hệ thống có thể trả đúng số của một record nhưng record đó không đúng loại người dùng muốn, như raw/cooked hoặc giống food name khác.

## 7. Health/BOTH retrieval path

File: `src/en/pipeline.py`.

```python
if intent in ("HEALTH_ADVICE", "BOTH"):
    candidates = self.retriever.retrieve(ret_q, top_k=20)

    if lazy_confident:
        chunks = candidates[:self.top_k]
    else:
        chunks = self.reranker.rerank(
            ret_q,
            candidates,
            top_k=self.top_k,
        )
```

`self.top_k=3`, nên generator nhận tối đa ba health chunks.

## 8. Prompt được xây thế nào?

File: `src/generation/generator.py`.

```text
System instructions
+ USDA nutrition section nếu có
+ top 3 Reference Documents nếu cần health
+ Question
+ Answer prefix
```

Các guardrail chính:

- dùng đúng số USDA được cung cấp;
- không tự ước lượng số không có;
- medical answer phải dựa trên reference documents;
- thiếu evidence thì nói không đủ thông tin.

Guardrail giảm rủi ro, không phải bằng chứng tuyệt đối LLM không sai.

## 9. Ollama call

Runtime config trong generator:

```python
"options": {
    "num_ctx": 4096,
    "num_predict": 700,
    "temperature": 0.0,
}
```

Giải thích:

- `num_ctx=4096`: cửa sổ context của request.
- `num_predict=700`: số token sinh tối đa, không phải 700 từ.
- `temperature=0.0`: giảm ngẫu nhiên, output ổn định hơn.

Báo cáo đang ghi `temperature=0.3`, `num_predict=2000`; cần đồng bộ về code thật.

## 10. `used_llm` và sources

Generator trả nội bộ:

```python
{
    "answer": answer,
    "sources": sources,
    "used_llm": used_llm,
}
```

`rag_server.py` in `used_llm` ra terminal để debug, nhưng response JSON gửi frontend hiện chỉ có:

- answer;
- intent;
- entities;
- sources.

Do đó trong demo muốn chứng minh fast-path không gọi LLM, hãy cho xem terminal log `Used LLM: False`, không nói UI đang hiển thị field này nếu UI không có.

## 11. Ollama lỗi thì sao?

Generator catch lỗi request/timeout và dùng `_fallback_answer()`. Khi đó:

- API vẫn có thể trả HTTP 200;
- answer là fallback được dựng từ data/context;
- `used_llm=False`;
- terminal có warning Ollama.

HTTP 200 không tự động chứng minh Llama đã chạy thành công.

## 12. Kịch bản nói slide 20

> Sau reranking, pipeline có ba nhóm xử lý. Với NUTRITION_LOOKUP, nếu tìm được một food record hợp lệ, generator format trực tiếp số USDA và trả `used_llm=False`, nên không có rủi ro LLM tự thay đổi số; rủi ro còn lại là chọn sai food record. Với HEALTH_ADVICE, top 3 evidence được chèn vào prompt cho Llama 3.1:8b. Với BOTH, prompt có đồng thời số USDA và tài liệu y khoa để Llama tổng hợp. Cuối cùng, intent NONE được early-return bằng thông báo tĩnh, không gọi database, retrieval hay LLM. Runtime dùng temperature 0, context 4096 và tối đa 700 output tokens để câu trả lời ổn định, gọn hơn.

## 13. Câu hỏi khó slide 20

### “Temperature 0 có hết hallucination không?”

Không. Nó giảm randomness. Grounding, source constraints và USDA fast-path mới là các lớp giảm rủi ro chính.

### “BOTH có used_llm=False không?”

Thông thường không, vì phần health cần LLM tổng hợp. USDA trong BOTH vẫn là dữ liệu xác định nhưng toàn answer đi qua generation.

### “Nếu USDA không tìm thấy food?”

Pipeline có NER cleaning và noun-chunk fallback. Nếu vẫn không tìm thấy, generator phải thông báo exact data unavailable thay vì đoán số.

### “Citations có đảm bảo từng claim được support?”

Không tuyệt đối. Sources cho biết tài liệu được đưa vào context; muốn xác minh từng claim cần faithfulness/citation-grounding evaluation riêng.

---

# Slide 21 - Conclusion & Future Directions

## 14. Bốn kết quả nên đọc đúng

### NER

Output mới trong `eval_ner.ipynb`:

```text
Overall entity F1 = 0.9565
```

Slide làm tròn `0.95` được, nhưng báo cáo đang ghi `0.893`. Nhóm cần chọn protocol chốt và đồng bộ.

### Intent

```text
445/448 = 99.33%
Macro-F1 = 99.33%
```

Slide đang ghi 99.36%, cần sửa.

### Retrieval

```text
Hybrid RRF + Reranker MRR@10 = 0.5754
```

Đây là retrieval ranking quality trên 323 NFCorpus queries, không phải answer accuracy.

### Fast-path

Có thể nói nhanh hơn LLM path và số được lấy từ USDA. Chỉ ghi `<1s` nếu có latency test/repeatable output đi kèm.

## 15. Giới hạn nên nói trung thực

### Intent data synthetic

2.240 câu cân bằng và QA tốt, nhưng cách diễn đạt của người dùng thật đa dạng hơn.

### Corpus giới hạn

NFCorpus có 3.633 benchmark documents, nhỏ hơn PubMed/full clinical guidelines.

### Local LLM latency

Llama 3.1:8b phụ thuộc GPU, prompt length, output length và Ollama setup. Không nên cam kết dưới 30 giây trên mọi máy.

### Generation chưa có benchmark chính thức

Retrieval MRR không thay thế faithfulness/correctness evaluation. Nếu RAGAS đã bỏ, slide nên nói đây là future work, không claim score.

### English-only

Intent/NER/corpus hiện tập trung tiếng Anh.

## 16. Future work hợp lý

- thu thập query người dùng thật và đánh nhãn độc lập;
- mở rộng corpus bằng PubMed/guidelines;
- đánh giá generation bằng faithfulness, relevance và human review;
- benchmark domain reranker trước khi active;
- giảm latency bằng model nhỏ, quantization hoặc streaming;
- hỗ trợ tiếng Việt với data/model phù hợp.

Nếu folder reranker fine-tuned đã tồn tại nhưng chưa active, nên nói:

> Validate and activate a domain reranker if it outperforms the base model.

Không nói “chưa train reranker” nếu model artifact đã có.

## 17. Kịch bản nói slide 21

> Hệ thống đã hoàn thành các component chính: NER đạt entity F1 khoảng 0,9565 theo notebook mới; intent bốn lớp đạt Accuracy và Macro-F1 0,9933 trên 448 held-out samples; Hybrid RRF kết hợp reranker đạt MRR@10 0,5754 trên 323 NFCorpus queries. Fast-path tách số USDA khỏi LLM, còn NONE chặn out-of-domain sớm. Tuy nhiên intent data vẫn chủ yếu synthetic, corpus còn nhỏ, local LLM có latency phụ thuộc phần cứng và generation chưa có benchmark chính thức hoàn chỉnh. Hướng phát triển là thu thập query thật, mở rộng corpus, đánh giá faithfulness/correctness và chỉ kích hoạt model domain khi benchmark chứng minh tốt hơn.

## 18. Câu hỏi khó slide 21

### “Metric nào chứng minh hệ thống trả lời đúng?”

Hiện các metric mạnh nhất chứng minh từng component: intent, NER và retrieval. Chưa có một generation correctness benchmark chính thức, nên nhóm không đánh đồng MRR với answer correctness.

### “Vậy bài đã hoàn chỉnh chưa?”

Pipeline ứng dụng đã hoạt động end-to-end và có component evaluation. Phần còn thiếu là đánh giá generation ở quy mô đủ lớn, đây là giới hạn nghiên cứu chứ không có nghĩa demo không chạy.

### “Prompt có đủ đảm bảo an toàn y khoa không?”

Không. Prompt guardrail chỉ giảm rủi ro. Hệ thống là trợ lý thông tin, không thay thế chẩn đoán/chuyên gia y tế.

---

# Slide 22 - Live Demo

## 19. Mục tiêu demo

Demo không chỉ để cho thấy chatbot trả lời. Nó phải chứng minh intent thật sự đổi flow.

## 20. Chuẩn bị trước demo

### Kiểm tra model và data

```powershell
Test-Path models/intent_model_v2/config.json
Test-Path models/ner_bert/config.json
Test-Path data/usda_food.db
Test-Path data/chroma_db
ollama list
```

### Khởi động Ollama

```powershell
ollama run llama3.1:8b "Say hello in one sentence."
```

### Khởi động FastAPI

```powershell
conda activate nutrition-rag
python main/rag_server.py
```

### Kiểm tra health endpoint

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Kỳ vọng:

```json
{"status":"ok","pipeline_ready":true}
```

Khởi động Spring Boot từ đúng thư mục có `pom.xml`, không chạy `mvn spring-boot:run` ở project root nếu root không có plugin/pom tương ứng.

## 21. Case 1 - NUTRITION_LOOKUP

```text
How many calories are in an apple?
```

Kỳ vọng terminal:

```text
Classified Intent: NUTRITION_LOOKUP
FOOD: apple
NUTRIENT: calories
Used LLM: False
Sources: USDA FoodData Central (...)
```

Lời nói:

> Intent nutrition đi thẳng SQLite và không gọi Llama. Terminal `Used LLM: False` là bằng chứng flow fast-path.

Không nên dùng `100g apple` nếu NER vẫn có khả năng gộp cả `100g apple` thành FOOD và làm SQLite matching kém.

## 22. Case 2 - HEALTH_ADVICE

```text
Is salmon good for heart health?
```

Kỳ vọng:

- intent `HEALTH_ADVICE`;
- sources là medical articles;
- `Used LLM: True`;
- không cần USDA để answer phần health.

Lời nói:

> Câu này đi full RAG: BM25 và Dense tìm candidate, RRF fusion, reranker chọn top 3 và Llama tổng hợp dựa trên medical context.

## 23. Case 3 - BOTH

```text
How much protein is in salmon, and is salmon good for heart health?
```

Kỳ vọng:

- intent `BOTH`;
- source có USDA và articles;
- `Used LLM: True`;
- answer có số protein và phần health.

Lời nói:

> BOTH kích hoạt cả hai nguồn. Số đến từ USDA, evidence đến từ NFCorpus, sau đó Llama tổng hợp thành một answer.

## 24. Case 4 - NONE

```text
How do I reverse a linked list in Python?
```

Kỳ vọng:

```text
Classified Intent: NONE
Used LLM: False
Sources: []
```

Lời nói:

> NONE guardrail chặn query ngoài miền bằng early return, không tốn tài nguyên cho database, retrieval hoặc Llama.

## 25. Đo latency nhanh

```powershell
Measure-Command {
  Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/ask" `
    -ContentType "application/json" `
    -Body '{"message":"Is salmon good for heart health?","history":[]}'
}
```

So sánh latency giữa fast-path và health path, nhưng không lấy một lần chạy làm benchmark chính thức.

## 26. Nếu demo lỗi

### HTTP 200 nhưng answer fallback

Xem terminal có `[WARN Ollama]` và `Used LLM: False` không.

### Ollama chậm

Kiểm:

```powershell
ollama ps
nvidia-smi
```

Đảm bảo model đang ở GPU và đã warm-up.

### Nutrition gọi LLM

Kiểm tra:

- intent có đúng nutrition không;
- NER/fallback có tìm food không;
- SQLite có record không;
- nutrition data có đủ để fast-path không.

### Source y khoa không phù hợp

Đây là retrieval error. Có thể giải thích pipeline hoạt động nhưng candidate relevance còn phụ thuộc corpus và retriever.

## 27. Kịch bản nói slide 22

> Demo gồm bốn câu tương ứng bốn intent. Câu apple đi USDA fast-path, terminal cho thấy `Used LLM: False`. Câu salmon-heart đi full RAG và trả medical sources. Câu protein-salmon-heart được phân loại BOTH nên kết hợp USDA với article evidence rồi Llama tổng hợp. Câu lập trình được phân loại NONE và early-return, không gọi các component nặng. Như vậy intent classifier không chỉ tạo nhãn hiển thị mà quyết định trực tiếp đường xử lý.

---

# Slide 23 - Kết thúc

Không thêm claim kỹ thuật mới. Câu kết ngắn:

> Nhóm em xin cảm ơn thầy cô và sẵn sàng trả lời câu hỏi về dữ liệu, mô hình, retrieval cũng như các giới hạn của hệ thống.

---

# 28. Bộ câu hỏi phản biện tổng hợp

### “NONE có phải là NER label mới không?”

Không. `NONE` là intent class của whole sentence. NER vẫn train ba entity type FOOD, DISEASE, NUTRIENT.

### “Tại sao BOTH không trả trực tiếp như nutrition?”

Vì phần health cần diễn giải context y khoa. USDA chỉ cung cấp nutrient values, không đủ trả lời tác dụng/rủi ro.

### “Source list có nghĩa LLM trích đúng từng câu không?”

Không chắc. Nó chứng minh tài liệu được đưa vào pipeline; claim-level support cần evaluation riêng.

### “MRR 0.5754 và intent 99.33% có cộng thành system score không?”

Không. Hai metric đo hai component khác nhau, trên dataset khác nhau.

### “Nếu intent sai thì sao?”

Routing sai từ đầu có thể bỏ qua đúng data source. Vì vậy intent được đánh giá riêng và demo đủ bốn branch.

### “Spring Boot có phải phần AI không?”

Không. Nó quản lý UI, auth, session/history và gọi FastAPI. AI/RAG nằm trong Python pipeline.

### “Hệ thống có multi-hop RAG không?”

Không nên gọi là multi-hop RAG. Hệ thống là Hybrid RAG với contextual entity accumulation cho multi-turn chat.

---

# 29. Những câu không nên nói

- “Fast-path không thể sai.”
- “Temperature 0 triệt tiêu hallucination.”
- “MRR 0.5754 nghĩa là 57.54% answer đúng.”
- “RAGAS đã đánh giá generation” nếu notebook/result đã bỏ.
- “LLM rewriter đang chạy” khi `use_llm_rewriter=false`.
- “used_llm hiển thị trên UI” nếu chỉ terminal có.
- “99.36% training accuracy.”
- “Hệ thống là multi-hop RAG.”

## 30. Checklist TV3

- [ ] Hiểu ba nhóm xử lý và bốn intent.
- [ ] Chỉ đúng early return của `NONE`.
- [ ] Giải thích điều kiện fast-path.
- [ ] Nói đúng `num_predict` là token tối đa.
- [ ] Nói đúng rủi ro food matching còn lại.
- [ ] Nhớ metric intent 99.33%, NER 0.9565, retrieval 0.5754.
- [ ] Test sẵn đủ bốn query demo.
- [ ] Warm-up Ollama trước demo.
- [ ] Quan sát terminal `Used LLM` và warnings.
- [ ] Không claim generation benchmark chưa có.
