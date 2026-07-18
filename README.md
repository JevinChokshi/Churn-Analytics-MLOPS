Customer Churn Prediction & Retention Automation

An end-to-end customer churn analytics and automation platform that simulates real-world SaaS data, builds a layered data warehouse, trains a machine learning model to predict customer churn, explains the primary frustration drivers behind each prediction using SHAP, and automates customer retention workflows.

The platform combines **synthetic data engineering, PostgreSQL data warehousing, exploratory data analysis, machine learning, explainable AI, n8n workflow automation, and Streamlit-based operational decision-making**.

---

## 🚀 Project Overview

Customer churn is rarely caused by a single event. It is usually the result of multiple behavioral, product, support, billing, and engagement signals accumulated over time.

This project simulates a real-world SaaS analytics environment and builds an automated churn intelligence platform capable of:

* Generating realistic synthetic customer and product data
* Ingesting raw CSV data into PostgreSQL
* Transforming raw data through a layered warehouse architecture
* Creating analytical customer-level feature matrices
* Predicting customer churn probabilities
* Explaining the primary frustration drivers for individual customers
* Automatically scoring customers on a daily schedule
* Updating prediction results in the analytics database
* Allowing Customer Success and Sales teams to audit predictions
* Automatically sending relevant customer lists to business teams

---

# 🏗️ End-to-End Architecture


┌─────────────────────────┐
│  Synthetic Data Source  │
│      create_data.py     │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     Raw CSV Tables      │
│        data/raw         │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Staging Layer (stg)   │
│      staging.ipynb      │
│  SQLAlchemy + psycopg2  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Intermediate Layer (int)│
│       SQL Models        │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│       Mart Layer        │
│ dim_users               │
│ fct_daily_user_snapshot │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Analytics Layer       │
│ churn_feature_matrix    │
│ churn_predictions       │
│ churn_audit_action      │
└────────────┬────────────┘
             │
             ├──────────────────────┐
             ▼                      ▼
┌─────────────────────┐   ┌──────────────────────┐
│ EDA & ML Training   │   │ Daily n8n Automation  │
│ Jupyter Notebook    │   │ Churn Prediction      │
└──────────┬──────────┘   └──────────┬───────────┘
           │                         │
           ▼                         ▼
┌─────────────────────┐   ┌──────────────────────┐
│ XGBoost ML Pipeline │   │ Updated Predictions  │
│ + SHAP Explainability│  │ Analytics Database   │
└──────────┬──────────┘   └──────────┬───────────┘
           │                         │
           └────────────┬────────────┘
                        ▼
              ┌─────────────────────┐
              │   Streamlit App     │
              │ Prediction Auditing │
              │ Action Management   │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │     n8n Webhook      │
              │ Automated Email      │
              │ Customer Success     │
              │ Sales Teams          │
              └─────────────────────┘


---

# 🔄 Data Pipeline

## 1. Synthetic Data Generation

The project begins by generating a realistic synthetic SaaS dataset using Python.

The data generation script simulates multiple operational systems commonly found in a modern SaaS company, including:

* User accounts and profiles
* Authentication events
* Login activity
* Session activity
* Product usage
* Clickstream behavior
* Mobile application activity
* Subscription lifecycle events
* Billing invoices
* Payment transactions
* Customer support tickets
* Support ticket events
* User feedback submissions
* Notification delivery
* Feature flag exposure
* Experiment assignments
* Application error logs
* Device profiles
* Frontend performance events

The generated data is designed to mimic real-world data relationships and customer behavior patterns, allowing the entire analytics and machine learning pipeline to be developed without relying on proprietary customer data.

### Script


scripts/create_data.py


Generated raw files are stored in:


data/raw/


---

# 2. Raw Data Ingestion into the Staging Layer

The generated CSV datasets are loaded into PostgreSQL using a Jupyter Notebook.

The staging process uses:

* `SQLAlchemy`
* `psycopg2`
* `pandas`

The purpose of the staging layer is to preserve the raw source data in a structured database environment before applying business logic or transformations.


CSV Files
    │
    ▼
Python / Pandas
    │
    ▼
SQLAlchemy
    │
    ▼
PostgreSQL
    │
    ▼
stg Schema


### Notebook


scripts/staging.ipynb


---

# 3. Layered Data Warehouse Architecture

The raw data is transformed using a layered data warehouse architecture.


stg → int → mart → analytics


Each layer has a specific purpose.

---

## 🟦 Staging Layer — `stg`

The staging layer contains the raw source tables loaded from CSV files.

The data is kept close to its original structure and acts as the foundation for downstream transformations.

---

## 🟨 Intermediate Layer — `int`

The intermediate layer applies transformations and creates reusable daily-level business entities.

Current intermediate tables include:

* `billing_and_revenue_daily`
* `customer_support_daily`
* `subscription_lifecycle_daily`
* `user_activity_daily`
* `user_profiles`

These tables consolidate raw events into meaningful customer-level metrics.

For example:

Raw events such as:


Login Events
Clickstream Events
Product Sessions
Mobile Events


can be transformed into:


Daily User Activity


Similarly:


Invoices
Payments
Subscription Events


can be transformed into:


Daily Billing and Revenue Metrics


---

## 🟩 Mart Layer — `mart`

The mart layer contains business-oriented analytical tables.

Current mart tables include:

### `dim_users`

A customer dimension containing consolidated customer-level attributes.

### `fct_daily_user_snapshot`

A daily snapshot of customer activity and behavioral metrics.

This layer acts as the foundation for building the machine learning feature matrix.

---

## 🟥 Analytics Layer — `analytics`

The analytics layer contains tables specifically designed for analysis, machine learning, predictions, and operational decision-making.

### `churn_feature_matrix`

The final feature matrix used for churn prediction.

### `churn_predictions`

Stores customer-level churn predictions, including:

* Customer identifier
* Churn probability
* Risk classification
* Prediction timestamp
* Model version
* SHAP-based explanation information

### `churn_audit_action`

Stores operational decisions made by business users after reviewing predictions.

This enables the prediction system to become part of an operational workflow rather than simply producing a static machine learning output.

---

# 4. Exploratory Data Analysis & Machine Learning

The analytical and machine learning workflow is implemented in:


scripts/EDA and model training.ipynb


The notebook uses the analytics-layer feature matrix:


analytics.churn_feature_matrix


---

## 📊 Exploratory Data Analysis

The EDA process investigates:

* Customer behavior patterns
* Churn distribution
* Usage trends
* Support ticket behavior
* Billing and payment behavior
* Subscription lifecycle patterns
* Engagement patterns
* Feature relationships
* Customer segments
* Potential churn indicators

The objective is to understand what behavioral and operational patterns are associated with customer churn before training the machine learning model.

---

# 🤖 Churn Prediction Model

The project uses a calibrated XGBoost machine learning pipeline to predict the probability that a customer will churn.

The model pipeline is stored at:

app/models/calibrated_xgboost_pipeline.joblib


The model generates a churn probability for each customer.

Example:


Customer ID: 100245
Churn Probability: 0.87
Risk Category: High Risk


The probability-based approach allows business teams to prioritize customers instead of treating churn as a simple binary prediction.

For example:


0.00 - 0.30  → Low Risk
0.30 - 0.70  → Medium Risk
0.70 - 1.00  → High Risk


---

# 🔍 Explainable AI with SHAP

The model also uses SHAP explainability to identify the primary factors influencing an individual customer's churn prediction.

For each customer, the system can identify potential frustration drivers such as:

* Declining product usage
* Increasing support ticket volume
* Negative feedback
* Payment failures
* Reduced login activity
* Subscription inactivity
* Application errors
* Poor product performance
* Reduced session duration

Instead of only displaying:


Churn Probability: 87%


the system can provide:

Churn Probability: 87%

Primary Frustration Drivers:
1. Declining product usage
2. Multiple unresolved support tickets
3. Negative user feedback


This makes the predictions more actionable for Customer Success and Sales teams.

---

# ⚙️ Daily Automated Prediction Pipeline

The project uses `n8n` to automate the daily prediction workflow.

The workflow is scheduled using a daily trigger.


┌────────────────────┐
│  Daily n8n Trigger │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ Fetch New Customer │
│ Feature Data       │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ Run Churn Model    │
│ + SHAP Analysis    │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ Generate Churn     │
│ Probabilities      │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ Update analytics.  │
│ churn_predictions  │
└────────────────────┘


The automation ensures that the churn prediction table is updated regularly without requiring manual execution.

This transforms the machine learning model into a recurring operational service.

---

# 🖥️ Streamlit Prediction Audit Application

The Streamlit application provides an interface for business users to review and audit churn predictions.

The application allows users to:

* View customers at risk of churn
* Review churn probabilities
* Examine primary frustration drivers
* Review SHAP explanations
* Audit individual predictions
* Record follow-up actions
* Assign or categorize customer actions
* Prepare customer lists for outreach

The application is designed to help business teams move from:


Prediction
    ↓
Understanding
    ↓
Decision
    ↓
Action


---

# 📧 Automated Customer Outreach

After reviewing the prediction results, the Streamlit application can trigger an `n8n` webhook.

The webhook can be used to automate customer outreach workflows.

Example:


Streamlit Application
        │
        ▼
User Audits Predictions
        │
        ▼
Customer List Selected
        │
        ▼
n8n Webhook Triggered
        │
        ├───────────────┐
        ▼               ▼
Customer Success      Sales Team
Email                 Email


Different customer lists can be sent to different business teams depending on the required action.

For example:

### Customer Success

Customers requiring:

* Retention outreach
* Product assistance
* Support intervention
* Customer health review

### Sales

Customers requiring:

* Account expansion discussions
* Upgrade opportunities
* Commercial follow-up
* Account-level engagement

This creates a closed-loop workflow between analytics, machine learning, and business operations.

---

# 📁 Project Structure


C:.
│   app.py
│   config.yaml
│   requirements.txt
|   calibrated_xgboost_pipeline.joblib
│
├───app
│   │   server.py
│   │   transformers.py
│
├───data
│   │
│   ├───processed
│   │
│   ├───Analytics Table
│   │       churn_audit_action
│   │       churn_feature_matrix
│   │       churn_predictions
│   │
│   ├───INT Tables
│   │       billing_and_revenue_daily
│   │       customer_support_daily
│   │       subscription_lifecycle_daily
│   │       user_activity_daily
│   │       user_profiles
│   │
│   ├───Mart Tables
│   │       dim_users
│   │       fct_daily_user_snapshot
│   │
│   └───Prediction Table
│
├───raw
│       application_error_logs.csv
│       app_user_accounts.csv
│       app_user_profiles.csv
│       auth_login_events.csv
│       auth_session_tokens.csv
│       billing_invoices.csv
│       clickstream_events.csv
│       experiment_assignments.csv
│       feature_flag_exposures.csv
│       frontend_performance_events.csv
│       mobile_application_events.csv
│       notification_delivery_events.csv
│       payment_transactions.csv
│       product_sessions.csv
│       subscription_accounts.csv
│       subscription_state_history.csv
│       support_tickets.csv
│       support_ticket_events.csv
│       user_device_profiles.csv
│       user_feedback_submissions.csv
│       user_master_profiles.csv
│
├───scripts
│       create_data.py
│       EDA and model training.ipynb
│       staging.ipynb
│
├───SQL Queries
│       Analytics Table.sql
│       INT Tables.sql
│       Mart Tables.sql
│       Prediction Table.sql
│
└───src
        automation.py
        config.py
        db.py
        ui.py
        __init__.py


---

# 🛠️ Technology Stack

## Programming & Data

* Python
* Pandas
* NumPy
* SciPy

## Database

* PostgreSQL
* SQLAlchemy
* psycopg2

## Data Engineering

* SQL
* Staging → Intermediate → Mart → Analytics architecture
* Jupyter Notebooks

## Machine Learning

* Scikit-learn
* XGBoost
* LightGBM
* Category Encoders
* Joblib

## Explainable AI

* SHAP

## Survival Analysis

* Lifelines

## Application & API

* Streamlit
* FastAPI
* Pydantic

## Automation

* n8n
* Webhooks
* Scheduled workflows

## Visualization

* Matplotlib
* Seaborn

---

# ⚙️ Installation

Clone the repository and install the required dependencies:


pip install -r requirements.txt


Example:


python -m pip install -r requirements.txt


---

# 🔐 Configuration

Database and application configuration should be managed through environment variables or the project configuration file.

Example configuration parameters may include:

database:
  username: postgres
  password: your_password
  host: localhost
  port: 5432
  database: customer_ltv_and_churn
  schema: analytics
  source_table: churn_predictions
  audit_table: churn_action_audit

n8n:
  webhook_url: your_webhook_url
  timeout_seconds: 20
  auth_mode: header
  api_key_header: X-API-Key
  api_key_value: replace_key_value
  basic_user: ""
  basic_password: ""
  verify_ssl: false

app:
  app_user: jevin.chokshi
  app_title: Churn Command Center




Sensitive credentials should never be committed to the repository.

---

# ▶️ Running the Project

## 1. Generate Synthetic Data


python scripts/create_data.py


This generates the raw SaaS datasets in:


data/raw/


---

## 2. Load Data into PostgreSQL

Run:


scripts/staging.ipynb


This loads the raw CSV datasets into the staging schema.

---

## 3. Build Data Warehouse Tables

Execute the SQL transformations in the following order:


1. INT Tables.sql
2. Mart Tables.sql
3. Analytics Table.sql
4. Prediction Table.sql


The transformation flow is:


stg
 ↓
int
 ↓
mart
 ↓
analytics


---

## 4. Perform EDA and Train the Model

Run:


scripts/EDA and model training.ipynb


This notebook:

1. Loads the churn feature matrix
2. Performs exploratory data analysis
3. Prepares the training data
4. Trains the churn prediction model
5. Calibrates the model probabilities
6. Evaluates model performance
7. Generates SHAP explanations
8. Saves the trained model pipeline

The trained model is saved as:


app/models/calibrated_xgboost_pipeline.joblib


---

## 5. Run Daily Automation

Configure the n8n workflow with a daily trigger.

The workflow:

1. Retrieves the latest customer features
2. Runs the churn prediction pipeline
3. Generates churn probabilities
4. Generates customer-level explanations
5. Updates the analytics prediction table


analytics.churn_predictions


---

## 6. Launch the Streamlit Application

Run:


streamlit run app.py


The application allows business users to review predictions, audit customers, and trigger outreach workflows through n8n.

---

# 🎯 Business Impact

This project demonstrates how a machine learning model can be integrated into a complete operational analytics workflow.

Instead of stopping at:


Train Model → Generate Prediction


the platform extends the workflow to:


Generate Data
      ↓
Build Data Warehouse
      ↓
Create Customer Features
      ↓
Predict Churn
      ↓
Explain Prediction
      ↓
Automate Daily Scoring
      ↓
Audit Predictions
      ↓
Trigger Business Action
      ↓
Customer Retention Outreach


This makes the project representative of a real-world **end-to-end data and machine learning product**.

---

# 📌 Key Project Highlights

* Synthetic generation of realistic multi-source SaaS data
* PostgreSQL data warehouse architecture
* Layered `stg → int → mart → analytics` data modeling
* Customer-level churn feature engineering
* Calibrated XGBoost churn prediction pipeline
* Probability-based customer risk scoring
* SHAP-based explainability
* Automated daily ML predictions using n8n
* Persistent prediction storage in PostgreSQL
* Streamlit-based prediction auditing
* Automated customer outreach through n8n webhooks
* Closed-loop analytics-to-action workflow

---

# 🔮 Future Improvements

Potential future improvements include:

* Model monitoring and drift detection
* Automated model retraining
* Prediction performance tracking
* Feedback loop from customer success actions
* Churn probability calibration monitoring
* Customer lifetime value prediction
* Retention uplift modeling
* Automated treatment recommendation
* Real-time event ingestion
* CI/CD pipeline for model deployment
* Production cloud deployment
* Feature store integration
* Model registry and experiment tracking

---

## 👤 Author

**Jevin Chokshi**

This project demonstrates an end-to-end implementation of modern data engineering, machine learning, explainable AI, workflow automation, and operational analytics.
