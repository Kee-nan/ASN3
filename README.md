# Assignment 3: Team Yellow 🟡
### CS 5128/6028: Large Scale Software Engineering

#

# Temporal Traceability Map 🕒✨  
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

# 2. Setup virtual environment
python -m venv venv
source venv/bin/activate   # For Mac/Linux
# OR
.\venv\Scripts\activate    # For Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py <app_name>
# OR
python3 main.py <app_name>

# 5. Click on the link provided in console by the application.
```

---


## 🤩 Temporal Traceability in Practice: Who Benefits and How?

- 🔷 **Clear Visual Language** - Diamonds for features, circles for reviews.
- 📊 **Sentiment Clusters** - Easily explore positive and negative feedback.
- 📌 **Precise Traceability** - Know exactly when a feature was released and how users reacted.
- ⚙️ **Designed for Stakeholders** - Useful for Product Managers, QA (Quality Assurance) Analysts, UX Teams, etc.
- 🔍 **Interactive Insights** - Quickly drill down without switching tools.
- 🧩 **Unified View** - All data in one place to save time and effort.

---



