import re
import nltk
import hdbscan
import pandas as pd
import numpy as np
import argparse
from nltk.corpus import words
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from config import RELEASE_FILES, PATCH_COLUMNS, REVIEW_FILES, REVIEW_COLUMNS


def clean_version(v):
    """
    Drops all unneeded version info.
    Example: "version 51.01 (4306)" -> "51.01"
    """
    s = str(v).lower().strip()
    pattern = re.search(r'(\d+\.\d+(?:\.\d+)?)', s)
    if pattern:
        return pattern.group(1)
    return s

def extract_major_minor(version):
    """
    Extracts the major.minor part of a version string.
    """
    match = re.search(r'(\d+)\.(\d+)', str(version))
    if match:
        major, minor = match.groups()
        return f"{major}.{minor}"
    return None

# Some words and phrases I found that tend not to be useful in reviews
# We're more looking for details on specific things
BORING_REVIEWS = {
    "good", "bad", "nice", "great", "ok", "okay", "fine", "works", "cool",
    "love it", "hate it", "very good app", "wow", "happy", "gud", "excellent",
    "fantastic", "best", "super", "amazing", "terrible"
}

def is_informative(text):
    """
    Checks if text is informative (not too short or too repetitive).
    """
    text = text.strip().lower()
    words = text.split()
    unique_words = set(words)
    return len(words) >= 5 and len(unique_words) >= 3

# Try loading files with different encodings
try:
    releases = pd.read_csv(release_file_path, encoding='cp1252')
except UnicodeDecodeError:
    releases = pd.read_csv(release_file_path, encoding='latin1')

try:
    reviews = pd.read_csv(review_file_path, encoding='cp1252')
except UnicodeDecodeError:
    reviews = pd.read_csv(review_file_path, encoding='latin1')

reviews = reviews.dropna(subset=[REVIEW_COLUMNS["Version"]])

# 2. Preprocess text
def clean_text(text):
    """
    Cleans text by lowercasing, removing emojis and extra whitespace.
    """
    if isinstance(text, str):
        text = re.sub(r'Ã', '', text)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002700-\U000027BF"  # Dingbats
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        text = text.lower().strip()
        # Remove anything that isn't actual text
        text = emoji_pattern.sub(r'', text)
        return text
    return ""

# Function to check if a cluster label is valid (i.e., not nonsensical)
def is_valid_label(label, threshold=0.3):
    """
    Returns True if the fraction of valid English words in the label exceeds the threshold.
    Here, a valid word is one that consists solely of alphabetic characters and is found
    in the NLTK English words corpus.
    """
    # Need this as sometimes this spits out nonsensical labels due to the nature of reviews
    tokens = re.findall(r'\w+', label)
    if not tokens:
        return False
    valid_count = sum(1 for token in tokens if token.isalpha() and token in english_words)

    return (valid_count / len(tokens)) >= threshold


def create_cluster(app_name: str):
    # Clean junk out of our reviews
    reviews['cleaned_content'] = reviews['content'].apply(clean_text)
    # Filter out any reviews that don't seem like they'll actually be useful
    reviews = reviews[reviews['cleaned_content'].apply(is_informative)]

    # Embed the cleaned review texts
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(reviews['cleaned_content'].tolist(), show_progress_bar=True)
    reviews['embedding'] = embeddings.tolist()

    # Get our versions like we do in main
    if app_name == "Zoom":
        reviews["clean_version"] = reviews[REVIEW_COLUMNS.get("Version")].apply(clean_version)
    elif app_name == "Webex":
        reviews["clean_version"] = reviews[REVIEW_COLUMNS.get("Version")].apply(extract_major_minor)
    elif app_name == "Firefox":
        # Firefox has no versions for features, so we gotta do some more work here
        review_date_col = REVIEW_COLUMNS.get("Date")
        release_date_col = PATCH_COLUMNS.get("Date")
        releases[release_date_col] = pd.to_datetime(releases[release_date_col], errors='coerce')
        reviews[review_date_col] = pd.to_datetime(reviews[review_date_col], errors='coerce')
        reviews = reviews.sort_values(review_date_col)

        release_dates = sorted(releases[release_date_col].dropna().unique().tolist())
        release_dates.append(pd.Timestamp.max)

        reviews['clean_version'] = pd.cut(
            reviews[review_date_col],
            bins=release_dates,
            labels=releases[release_date_col].sort_values().unique(),
            right=False # Don't include reviews that happen on the next review day in the previous bin [x, y)
        )

        reviews['clean_version'] = pd.to_datetime(reviews['clean_version'])
        releases['clean_version'] = releases[release_date_col]


    if app_name != "Firefox":
        releases["clean_version"] = releases[PATCH_COLUMNS.get("Version")].apply(clean_version)
    versions = releases['clean_version'].dropna().unique()

    # Prepare lists to hold results
    cluster_summary_list = []  # holds one dict per cluster with summary info
    clustered_reviews_list = []  # holds the individual review clusters

    # Cluster reviews for each version
    for version in versions:
        version_reviews = reviews[reviews['clean_version'] == version]
        print(f"\nProcessing version: {version} - {len(version_reviews)} reviews")

        if len(version_reviews) < 5:
            print(f"Skipping version {version} (not enough reviews)")
            continue

        version_embeddings = np.array(version_reviews['embedding'].tolist())

        # Cluster with HDBSCAN
        # If you want an explanation:
        # https://hdbscan.readthedocs.io/en/latest/how_hdbscan_works.html
        clusterer = hdbscan.HDBSCAN(min_cluster_size=5, prediction_data=True)
        labels = clusterer.fit_predict(version_embeddings)

        version_reviews = version_reviews.copy()
        version_reviews['cluster'] = labels

        # Filter out noise points (label == -1)
        clustered_reviews = version_reviews[version_reviews['cluster'] != -1]

        if clustered_reviews.empty:
            print(f"No good clusters found for version {version}")
            continue

        print(f"Found {clustered_reviews['cluster'].nunique()} clusters for version {version}")

        # For each cluster, determine representative phrases (using TF-IDF) and update reviews with it.
        for cluster_id in sorted(clustered_reviews['cluster'].unique()):
            # Select reviews in the current cluster
            cluster_subset = clustered_reviews[clustered_reviews['cluster'] == cluster_id]
            cluster_texts = cluster_subset['cleaned_content'].tolist()

            # Remove boring and uninformative reviews from phrase extraction
            # Author note: Quite a bit of filtering was needed for this to make this visualizaiton feature not totally useless
            filtered_texts = [t for t in cluster_texts if t not in BORING_REVIEWS and is_informative(t)]
            if not filtered_texts:
                print(f"Skipping cluster {cluster_id} in version {version} (not enough informative reviews)")
                continue

            # Extract top terms using TF-IDF
            # Explanation: https://www.learndatasci.com/glossary/tf-idf-term-frequency-inverse-document-frequency/
            # This isn't perfect, but can help summarize for us.
            tfidf = TfidfVectorizer(ngram_range=(3,4), strip_accents='unicode', max_features=5, stop_words='english')
            tfidf_matrix = tfidf.fit_transform(filtered_texts)
            top_terms = tfidf.get_feature_names_out()
            cluster_label = ", ".join(top_terms)

            # Get the average score of the cluster
            avg_score = cluster_subset[REVIEW_COLUMNS["Rating"]].mean()

            if not is_valid_label(cluster_label):
                print(f"Cluster {cluster_id} in version {version} filtered out due to nonsensical label: {cluster_label}")
                continue

            print(f"Version {version} - Cluster {cluster_id}: {cluster_label} - Average Score: {avg_score}")

            # Record a summary for this cluster
            cluster_summary_list.append({
                "version": version,
                "cluster_id": cluster_id,
                "cluster_label": cluster_label,
                "num_reviews": len(cluster_subset),
                "avg_score": avg_score
            })

            # Add the cluster label to each review in this cluster subset
            cluster_subset = cluster_subset.copy()
            cluster_subset['cluster_label'] = cluster_label

            # Append to global reviews list
            clustered_reviews_list.append(cluster_subset)

    # Combine all the clustered reviews and cluster summaries into DataFrames
    if clustered_reviews_list:
        all_clustered_reviews = pd.concat(clustered_reviews_list, ignore_index=True)
        # Save the detailed review clustering to CSV
        all_clustered_reviews.to_csv(f"./Clusters/{app_name}_clustered_reviews_output.csv", index=False)
        print(f"Saved detailed clustered reviews to 'Clusters/{app_name}_clustered_reviews_output.csv'")
    else:
        print("No clustered reviews to save.")

    if cluster_summary_list:
        cluster_summary_df = pd.DataFrame(cluster_summary_list)
        # Save the cluster summary to CSV
        cluster_summary_df.to_csv(f"./Clusters/{app_name}_cluster_summary.csv", index=False)
        print(f"Saved cluster summary to 'Clusters/{app_name}_cluster_summary.csv'")
    else:
        print("No cluster summaries to save.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cluster reviews for a specific app.')
    parser.add_argument('app_name', type=str, help='Name of the app to process (e.g., Zoom, Webex, Firefox)')
    args = parser.parse_args()
    create_cluster(args.app_name)