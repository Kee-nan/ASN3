import re
import spacy
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
import hdbscan
from sklearn.feature_extraction.text import TfidfVectorizer
from config import RELEASE_FILES, PATCH_COLUMNS, REVIEW_FILES, REVIEW_COLUMNS

review_file_path = './Reviews/Zoom_reviews.csv'
release_file_path = './Releases/Zoom_releases.csv'

# Check if the Spacy model is installed, if not, download it
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

model = SentenceTransformer('all-MiniLM-L6-v2')

def clean_text(text):
    if pd.isna(text):
        return ""
    doc = nlp(text)
    tokens = [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct and token.is_alpha]
    return " ".join(tokens)

def cluster_and_extract_keywords(df, text_column, version_column):
    # Clean and embed
    print("Cleaning text...")
    df['cleaned'] = df[text_column].apply(clean_text)
    print("Gathering embeddings")
    embeddings = model.encode(df['cleaned'].tolist(), show_progress_bar=True)

    # Group by version (or another identifier)
    version_clusters = {}
    for version in df[version_column].unique():
        print("Processing Version: " + str(version))
        version_df = df[df[version_column] == version]

        # Cluster within version
        clusterer = hdbscan.HDBSCAN(min_cluster_size=5, prediction_data=True)
        labels = clusterer.fit_predict(embeddings[version_df.index])
        version_df['cluster'] = labels

        # TF-IDF for version-specific clustering
        vectorizer = TfidfVectorizer(max_df=0.8, min_df=2)
        tfidf = vectorizer.fit_transform(version_df['cleaned'])
        feature_names = vectorizer.get_feature_names_out()

        # Get top keywords per cluster in the version
        keywords_per_cluster = {}
        for label in np.unique(labels):
            if label == -1:
                continue  # skip noise

            mask = version_df['cluster'] == label
            cluster_tfidf = tfidf[mask.values]
            mean_tfidf = np.asarray(cluster_tfidf.mean(axis=0)).ravel()

            top_indices = mean_tfidf.argsort()[::-1][:10]  # Top 10 keywords
            top_keywords = [feature_names[i] for i in top_indices]
            keywords_per_cluster[label] = top_keywords
        
        version_clusters[version] = keywords_per_cluster

    return df, version_clusters

# Storage for all results
cluster_summary = []

# Process Review Files
for file in ['Reviews/Zoom_reviews.csv']:
    print(f"Processing review file: {file}")
    df = pd.read_csv(file)
    df, version_keywords = cluster_and_extract_keywords(df, REVIEW_COLUMNS['Description'], REVIEW_COLUMNS['Version'])

    for version, keywords in version_keywords.items():
        for label, words in keywords.items():
            cluster_summary.append({
                'version': version,
                'file': file,
                'cluster_label': label,
                'top_keywords': ", ".join(words)
            })

# Save everything to a CSV
output_df = pd.DataFrame(cluster_summary)
output_df.to_csv("cluster_keywords_summary_by_version.csv", index=False)

print("✅ Cluster keywords saved to cluster_keywords_summary_by_version.csv")
