import os
import csv
import time
import google.generativeai as genai
from tqdm import tqdm
from dotenv import load_dotenv

# Đọc file .env từ thư mục gốc một cách thủ công (đảm bảo 100% lấy được)
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / '.env'

GEMINI_API_KEY = None
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            if "GEMINI_API_KEY=" in line:
                GEMINI_API_KEY = line.split("=", 1)[1].strip()

if not GEMINI_API_KEY:
    raise ValueError("LỖI: Chưa lấy được API Key! File .env đang bị thiếu hoặc tên biến không phải là GEMINI_API_KEY.")

genai.configure(api_key=GEMINI_API_KEY)

# Sử dụng model Gemini 2.5 Flash
model = genai.GenerativeModel('gemini-2.5-flash')

PROMPTS = {
    "NUTRITION_LOOKUP": """
You are a dataset generator for an intent classification model.
Generate exactly 50 diverse questions where a user is asking for the NUTRITIONAL CONTENT of a food item.
Examples: "How many calories in an apple?", "What is the protein content of chicken breast?"
Provide ONLY the questions, one per line, without any numbering or bullet points.
    """,
    
    "HEALTH_ADVICE": """
You are a dataset generator for an intent classification model.
Generate exactly 50 diverse questions where a user is asking for HEALTH ADVICE related to a specific medical condition or diet, WITHOUT asking for exact nutritional numbers.
Examples: "Is keto good for diabetes?", "What should I eat to lower my blood pressure?"
Provide ONLY the questions, one per line, without any numbering or bullet points.
    """,
    
    "BOTH": """
You are a dataset generator for an intent classification model.
Generate exactly 50 diverse questions where a user is asking for BOTH nutritional numbers AND health advice in the same question.
Examples: "How much sugar is in a banana, and is it safe for a diabetic?", "Give me the protein in salmon and tell me if it helps build muscle."
Provide ONLY the questions, one per line, without any numbering or bullet points.
    """,
    
    "NONE": """
You are a dataset generator for an intent classification model.
Generate exactly 50 diverse questions that have absolutely NOTHING to do with food, nutrition, or healthcare.
Topics: technology, programming, weather, geography, history, movies, sports, daily chit-chat, math.
Examples: "How do I reverse a string in Python?", "What is the capital of France?", "Is it going to rain tomorrow?"
Provide ONLY the questions, one per line, without any numbering or bullet points.
    """
}

def generate_intent_data(intent_label, target_count=600):
    unique_questions = set()
    print(f"\n--- Sinh dữ liệu cho nhãn: {intent_label} ({target_count} câu) ---")
    prompt = PROMPTS[intent_label]
    
    with tqdm(total=target_count) as pbar:
        while len(unique_questions) < target_count:
            try:
                response = model.generate_content(prompt)
                questions = response.text.strip().split('\n')
                
                new_added = 0
                for q in questions:
                    q = q.strip("- *.1234567890 ")
                    if len(q) > 10 and q not in unique_questions:
                        unique_questions.add(q)
                        new_added += 1
                        if len(unique_questions) >= target_count:
                            break
                            
                pbar.update(new_added)
                time.sleep(2) # Nghỉ để tránh Rate Limit của API Free
                
            except Exception as e:
                print(f"Lỗi khi gọi API: {e}. Đang thử lại...")
                time.sleep(5)
                
    return list(unique_questions)

if __name__ == "__main__":
    os.makedirs("data/en", exist_ok=True)
    output_file = "data/en/synthetic_intent.csv"
    
    all_data = []
    
    # Bạn có thể điều chỉnh số lượng mỗi nhãn ở đây (ví dụ: 600)
    target_per_class = 600 
    
    for label in PROMPTS.keys():
        questions = generate_intent_data(label, target_count=target_per_class)
        for q in questions:
            all_data.append([q, label])
            
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        writer.writerows(all_data)
        
    print(f"\n[DONE] Đã lưu thành công {len(all_data)} câu vào {output_file}")
