import os
import csv
import requests
from tqdm import tqdm

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1:8b" # Model bạn đang cài sẵn trong máy

PROMPTS = {
    "NUTRITION_LOOKUP": """
You are a dataset generator for an intent classification model.
Generate exactly 50 diverse questions where a user is asking for the NUTRITIONAL CONTENT of a food item.
Examples: "How many calories in an apple?", "What is the protein content of chicken breast?"
Provide ONLY the questions, one per line, without any numbering, bullet points, or conversational text.
""",
    
    "HEALTH_ADVICE": """
You are a dataset generator for an intent classification model.
Generate exactly 50 diverse questions where a user is asking for HEALTH ADVICE related to a specific medical condition or diet, WITHOUT asking for exact nutritional numbers.
Examples: "Is keto good for diabetes?", "What should I eat to lower my blood pressure?"
Provide ONLY the questions, one per line, without any numbering, bullet points, or conversational text.
""",
    
    "BOTH": """
You are a dataset generator for an intent classification model.
Generate exactly 50 diverse questions where a user is asking for BOTH nutritional numbers AND health advice in the same question.
Examples: "How much sugar is in a banana, and is it safe for a diabetic?", "Give me the protein in salmon and tell me if it helps build muscle."
Provide ONLY the questions, one per line, without any numbering, bullet points, or conversational text.
""",
    
    "NONE": """
You are a dataset generator for an intent classification model.
Generate exactly 50 diverse questions that have absolutely NOTHING to do with food, nutrition, or healthcare.
Topics: technology, programming, weather, geography, history, movies, sports, daily chit-chat, math.
Examples: "How do I reverse a string in Python?", "What is the capital of France?", "Is it going to rain tomorrow?"
Provide ONLY the questions, one per line, without any numbering, bullet points, or conversational text.
"""
}

def generate_intent_data_ollama(intent_label, target_count=600):
    unique_questions = set()
    print(f"\n--- Sinh dữ liệu cho nhãn: {intent_label} ({target_count} câu) ---")
    prompt = PROMPTS[intent_label]
    
    with tqdm(total=target_count) as pbar:
        while len(unique_questions) < target_count:
            try:
                payload = {
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False
                }
                
                response = requests.post(OLLAMA_API_URL, json=payload)
                if response.status_code == 200:
                    text_output = response.json().get('response', '')
                    questions = text_output.strip().split('\n')
                    
                    new_added = 0
                    for q in questions:
                        q = q.strip("- *.1234567890\"' ")
                        if len(q) > 10 and q not in unique_questions:
                            unique_questions.add(q)
                            new_added += 1
                            if len(unique_questions) >= target_count:
                                break
                                
                    pbar.update(new_added)
                else:
                    print(f"Ollama trả về mã lỗi: {response.status_code}")
                    
            except Exception as e:
                print(f"Lỗi kết nối Ollama: {e}. Vui lòng bật phần mềm Ollama lên!")
                break
                
    return list(unique_questions)

if __name__ == "__main__":
    os.makedirs("data/en", exist_ok=True)
    output_file = "data/en/synthetic_intent.csv"
    
    all_data = []
    target_per_class = 600 
    
    # Kiểm tra xem Ollama có đang chạy không
    try:
        requests.get("http://localhost:11434")
    except:
        print("CẢNH BÁO: Không thể kết nối tới Ollama. Vui lòng chạy phần mềm Ollama trước!")
        exit(1)
        
    for label in PROMPTS.keys():
        questions = generate_intent_data_ollama(label, target_count=target_per_class)
        for q in questions:
            all_data.append([q, label])
            
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        writer.writerows(all_data)
        
    print(f"\n[DONE] Đã lưu thành công {len(all_data)} câu vào {output_file}")
