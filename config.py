# Paths to CSV files
# These are the variables to use that are just the relative paths to the csv files
REVIEW_FILES = {
    "webex_reviews": "Reviews/Webex_reviews.csv",
    "firefox_reviews": "Reviews/Firefox_reviews.csv",
    "zoom_reviews": "Reviews/Zoom_reviews.csv",
}

RELEASE_FILES = {
    "webex_releases": "Releases/Webex_releases.csv",
    "firefox_releases": "Releases/Firefox_releases.csv",
    "zoom_releases": "Releases/Zoom_releases.csv",
}

# Common column names
# Feel free to add more here as they become useful for abbrieviating the names of different columns in the excel files

REVIEW_COLUMNS = {
    "Rating": "score", # score is the 1-5 star rating they left for their review
    "Date": "at", # at is the date the review was left
    "Version": "appVersion",
    "Description": "content",
}

PATCH_COLUMNS = {
    "Date": "Release Date", # Date the patch was released
    "Version": "Release Version", # Version the Company made for this releae
    "Description": "Feature Description",
}
