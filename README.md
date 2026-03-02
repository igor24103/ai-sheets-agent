# AI Sheets Agent

> 🤖 AI-powered business automation that reads leads from Google Sheets, scores them with GPT/Llama, and writes results back — with Telegram notifications.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-000000)
![Google Sheets](https://img.shields.io/badge/Google-Sheets%20API-34A853?logo=googlesheets&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ What does it do?

Automates lead qualification for sales teams:

1. **📊 Reads** new leads from a Google Sheet
2. **🤖 Scores** each lead (1-10) using AI (GPT-4o or local Llama 3)
3. **📝 Classifies** as Hot 🔥 / Warm 🟡 / Cold 🔵
4. **✍️ Generates** personalized follow-up email drafts
5. **📈 Writes** results back to the sheet + analytics dashboard
6. **🔔 Notifies** via Telegram when hot leads are detected

### Before & After

```
BEFORE (Google Sheet - "Leads"):
┌──────────┬────────────────────┬──────────┬─────────────────────────────┬────────┐
│ Name     │ Email              │ Company  │ Message                     │ Status │
├──────────┼────────────────────┼──────────┼─────────────────────────────┼────────┤
│ John D.  │ john@startup.io    │ StartupX │ Need AI integration for CRM │        │
│ Alice M. │ alice@bigcorp.com  │ BigCorp  │ Exploring automation tools  │        │
│ Bob K.   │ bob@gmail.com      │          │ How much does this cost?    │        │
└──────────┴────────────────────┴──────────┴─────────────────────────────┴────────┘

AFTER (processed by AI agent):
┌──────────┬───────────┬───────┬──────────┬──────────────────────────────────────────┐
│ Name     │ Status    │ Score │ Category │ Analysis                                 │
├──────────┼───────────┼───────┼──────────┼──────────────────────────────────────────┤
│ John D.  │ processed │ 9     │ 🔥 hot   │ Enterprise lead, specific AI need        │
│ Alice M. │ processed │ 7     │ 🟡 warm  │ Large company exploring, needs nurturing │
│ Bob K.   │ processed │ 3     │ 🔵 cold  │ No company, vague inquiry, price shopper │
└──────────┴───────────┴───────┴──────────┴──────────────────────────────────────────┘
```

---

## 🏗 Architecture

```
                    ┌──────────────────┐
                    │  Google Sheets   │
                    │  (Leads Sheet)   │
                    └────────┬─────────┘
                             │ Read unprocessed leads
                    ┌────────▼─────────┐
                    │   SheetsManager  │
                    │   (sheets.py)    │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │    AI Agent      │◄──── OpenAI API (GPT-4o)
                    │   (agent.py)     │◄──── OR Ollama (Llama 3)
                    └────────┬─────────┘
                             │ Score + Classify + Draft Response
                    ┌────────▼─────────┐
                    │   Main Runner    │
                    │   (main.py)      │
                    └───┬─────────┬────┘
                        │         │
               ┌────────▼──┐  ┌──▼──────────┐
               │  Write     │  │  Telegram   │
               │  Results   │  │  Alerts     │
               │  to Sheet  │  │  (notifier) │
               └────────────┘  └─────────────┘
```

### Project Structure

```
ai-sheets-agent/
├── main.py           # CLI entry point (--watch, --dry-run, --provider)
├── agent.py          # AI scoring engine (OpenAI + Ollama)
├── sheets.py         # Google Sheets API wrapper
├── notifier.py       # Telegram notification service
├── config.py         # Configuration management
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variables template
└── .gitignore
```

---

## 🚀 Quick Start

### 1. Google Sheets Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Google Sheets API**
3. Create a **Service Account** → Download `credentials.json`
4. Create a Google Sheet with headers: `Name | Email | Company | Message | Status | Score | Category | Analysis | AI_Response`
5. Share the sheet with your service account email

### 2. Install & Configure

```bash
git clone https://github.com/yourusername/ai-sheets-agent.git
cd ai-sheets-agent

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials
```

### 3. Run

```bash
# Process leads once
python main.py

# Watch mode — poll every 5 minutes
python main.py --watch

# Preview without writing changes
python main.py --dry-run

# Use local Ollama instead of OpenAI
python main.py --provider ollama
```

---

## 🤖 AI Providers

| Provider | Model | Speed | Cost | Privacy |
|----------|-------|-------|------|---------|
| **OpenAI** | GPT-4o-mini | ⚡ Fast | ~$0.001/lead | Cloud |
| **Ollama** | Llama 3 (8B) | 🐢 Slower | Free | 🔒 Local |

Switch between providers via `AI_PROVIDER` in `.env` or `--provider` CLI flag.

---

## 📊 Output

The agent writes to 3 sheet tabs:

| Sheet | Purpose |
|-------|---------|
| **Leads** | Source data + AI results (score, category, analysis, response) |
| **Processed** | Historical log of all processed leads with timestamps |
| **Analytics** | Summary dashboard (total, hot/warm/cold counts, avg score) |

---

## 🔔 Notifications

When a **hot lead** (score ≥ 8) is detected, you get an instant Telegram alert:

```
🔥 Hot Lead Detected!

👤 John Doe
🏢 TechCorp Inc.
📧 john@techcorp.com
⭐ Score: 9/10

📊 Enterprise client with specific AI integration needs — high buying intent
```

---

## 🔧 Customization

### Custom AI Instructions

The agent supports custom processing beyond lead scoring:

```python
from agent import AIAgent

agent = AIAgent()

# Classify customer feedback
result = agent.classify_sentiment("Your product saved our team 20 hours/week!")
# → "positive"

# Custom data processing
result = agent.process_custom(
    data="Revenue: $50K, Churn: 5%, NPS: 72",
    instructions="Analyze these SaaS metrics and suggest improvement areas"
)
```

---

## 📄 License

MIT License — free to use and modify.
