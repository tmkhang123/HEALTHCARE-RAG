import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

print('Loading model and data...')
model = SentenceTransformer('all-MiniLM-L6-v2')
df = pd.read_csv('data/en/intent_v2/intent_train_v2.csv')

print('Encoding...')
embeddings = model.encode(df['text'].tolist(), show_progress_bar=False)
sim_matrix = cosine_similarity(embeddings)

labels = df['label'].values
n = len(labels)

print('Calculating metrics...')
same_label_mask = labels[:, None] == labels[None, :]
np.fill_diagonal(same_label_mask, False)
diff_label_mask = labels[:, None] != labels[None, :]

within_avg = sim_matrix[same_label_mask].mean()
between_avg = sim_matrix[diff_label_mask].mean()
ratio = within_avg / between_avg

print(f'within: {within_avg:.3f}')
print(f'between: {between_avg:.3f}')
print(f'ratio: {ratio:.2f}x')
