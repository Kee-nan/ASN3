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
- 💎 **Diamonds** for representing feature releases  
- 🔴 **Circles** for clustering related user reviews  
- 📈 **X-axis** encoding time and versioning  
- 📊 **Y-axis** showing average user ratings (sentiment)

Bubble **size** reflects the number of reviews, while **version node size** represents the number of features released. This layout allows intuitive exploration of **temporal traceability** between product changes and user feedback...

---




### To use this repository
- Setup a virtualenv `python -m venv venv`
- Run `source venv/bin/activate`
- Pip install `pip install -r requirements.txt`
- Run `python main.py <app_name>`
- Click on the link provided in console by the application.

