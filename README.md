
# Sistema Gratificacoes - Full Streamlit App ready for GitHub/Streamlit Cloud

This repository contains a complete Streamlit application that implements:
- User authentication (SQLite + bcrypt) with initial admin/admin account
- Admin panel: manage users and set metas per seller
- Upload Excel with sales data and automatic calculation of gratifications (rules: proportional base up to 100% and bonus on excess)
- Generate PDF reports (ReportLab) and download or send via SMTP
- Placeholders for Power BI integration (Power BI REST API)
- Dockerfile and GitHub Actions workflow example for scheduling

## How to use
1. Clone the repo to your machine or upload to GitHub.
2. Set environment variables (optional but recommended) for SMTP:
   - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, RECIPIENTS
3. Run locally:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. Deploy on Streamlit Cloud: connect your GitHub repo and deploy. Set environment variables in the Streamlit Cloud UI.

## Notes
- The app uses SQLite for simplicity. For production, migrate to a centralized DB (Postgres) if needed.
- Power BI integration requires Azure AD App registration. See powerbi.py for placeholders.
