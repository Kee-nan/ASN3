# Assignment 3: Team Yellow 🟡
### CS 5128/6028: Large Scale Software Engineering

---
# Team Members
- Niharika Mysore Gowda
- Nishit Grover
- Keenan Herbe
- Anay Abhijit Joshi
- Aidan Kovacic
- Anwar Sayeed Mohammed
- Arya Narke
- Tristan Pommering
- Daksh Prajapati
- Ethan Reed
- Russell Toney

---

<!---#--->

# Temporal Traceability Map/Graph 🕒✨  
#### *Tracing Software Features to User Feedback in Time*

<!---
Should be able to git clone into your workspace 
Create a virtual environment and pip install the depencencies in the requirements.txt file

Each folder, releases and reveiws, have both an excel file and a CSV file for each companies respective thing
--->

This repository contains the source code and data for **ASN3** - a novel temporal visualization that maps **software feature releases** to corresponding **user app reviews** over time. Designed to enhance traceability and sentiment analysis, this tool enables stakeholders to quickly assess how users react to specific feature rollouts.

---


## 🔍 Project Overview

Our visualization introduces:
- 💎 **Diamonds** for representing feature releases.  
- 🔴 **Circles** for clustering related user reviews.  
- 📈 **X-axis** encoding time and versioning.  
- 📊 **Y-axis** showing average user ratings (sentiment).

Bubble **size** reflects the number of reviews, while **version node size** represents the number of features released. This layout allows intuitive exploration of **temporal traceability** between product changes and user feedback...

---

## 🗂️ Data Included

This repository includes:
- 📂 `Releases/` folder - CSV and Excel files for feature release data  
- 📂 `Reviews/` folder - CSV and Excel files for user app reviews
- 📂 `Clusters/` folder - CSV files that contain the output of `review_clustering.py`
---


## 💻 **Apps covered (Jan 2022 – Jan 2024):**
- **Zoom**: 571 features, 153,779 reviews  
- **Webex**: 258 features, 55,558 reviews  
- **Firefox**: 171 features, 56,382 reviews

---


<!---
## 📂 To use this repository
- Setup a virtualenv `python -m venv venv`
- Run `source venv/bin/activate`
- Pip install `pip install -r requirements.txt`
- Run `python main.py <app_name>`
- Click on the link provided in console by the application.
--->


## 🚀 To Use This Repository

Follow these steps to set up and run the app locally:

```bash
# 1. Clone the repo
git clone https://github.com/Kee-nan/ASN3

# 2. Use git-lfs to get CSV files
git lfs install # If you don't have git-lfs set up
git lfs pull # Get files

# 3. Setup virtual environment
python -m venv venv
source venv/bin/activate   # For Mac/Linux
# OR
.\venv\Scripts\activate    # For Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the application
python main.py <app_name>
# OR
python3 main.py <app_name>

# 6. Click on the link provided in console by the application.
```
### NOTE IF GIT LFS DOES NOT WORK:
We've noticed that we're sometimes being rate-limited by GitHub for LFS, meaning you cannot pull any of the CSVs.
If this happens to you, we have a Google Drive folder that holds all of the CSVs. [Google Drive Link](https://drive.google.com/drive/folders/1m8kfVwJXnWNPBFtJpnz6KkS-Y843mjKt?usp=sharing)

This drive link contains the CSVs for `Releases/`, `Clusters/` and `Reviews/` and should be able to be dragged and dropped into the repository.
We apologize for the inconvenience. 

We have attempted to fix this by looking into Git LFs objects settings based on similar issues we found people had on stack overflow, but the github has since removed it.
Attempting to find an alternative solution, ChatGPT produced this outcome:

"
The "Include Git LFS objects" checkbox used to be available in the "Repository Settings > Archives" section on GitHub, 
allowing you to include Large File Storage (LFS) objects when generating repository archives like ZIP or tarballs. 
However, as of recent updates:
🔍 This checkbox no longer exists in the GitHub UI.
GitHub has changed how Git LFS objects are handled in repository archives:

✅ What's the current behavior?
When downloading an archive (ZIP or tarball) from the main branch or any commit, Git LFS objects are not included by default.
If you need the LFS objects, you should clone the repository using Git and Git LFS rather than downloading it as a ZIP.

💡 What should you do instead?
To get a repo with LFS files included, do this:

git lfs install
git clone https://github.com/username/repository.git

That way, Git LFS will download all the actual LFS-tracked files.
If you still need to create an archive with LFS files included (for deployment, distribution, etc.), you'll have to:
Clone the repo locally with LFS.
Ensure all LFS files are pulled (git lfs pull if needed).
Manually zip it:

zip -r your-archive-name.zip your-repo-folder
"

We hope that, should you have issues with this, one of the provided solutions can help
Thank you for your understanding.
---


## 🤩 Temporal Traceability in Practice: Who Benefits and How?

- 🔷 **Clear Visual Language** - Diamonds for features, circles for reviews.
- 📊 **Sentiment Clusters** - Easily explore positive and negative feedback.
- 📌 **Precise Traceability** - Know exactly when a feature was released and how users reacted.
- ⚙️ **Designed for Stakeholders** - Useful for Product Managers, QA (Quality Assurance) Analysts, UX Teams, etc.
- 🔍 **Interactive Insights** - Quickly drill down without switching tools.
- 🧩 **Unified View** - All data in one place to save time and effort.

---

### ℹ️ More Detailed Overview

The software-feature and app-review datasets are provided as follows:

<!---
- Features
- App Reviews
--->

- **Features**
  - **Zoom** released features (from Jan, 2022 to Jan, 2024; `571` total features provided);
  - **Webex** released features (from Jan, 2022 to Dec, 2023; `258` total features provided); and
  - **Firefox** released features (from Jan, 2022 to Jan, 2024; `171` total features provided).

- **App Reviews**
  - **Zoom** (from Jan, 2022 to Jan, 2024; `153,779` total reviews provided);
  - **Webex** (from Jan, 2022 to Dec, 2023; `55,558` total reviews provided); and
  - **Firefox** (from Jan, 2022 to Jan, 2024; `56,382` total reviews provided).


---

