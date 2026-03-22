# 🌐 Language Translator Chatbot

A serverless language translation chatbot built on AWS, using **Amazon Lex** for conversational AI, **AWS Lambda** for business logic, and **Amazon Translate** for real-time text translation. Users interact with the chatbot naturally — it collects the target language and input text, then returns the translated result instantly.

---

## 📐 Architecture

```
User → Amazon Lex → AWS Lambda → Amazon Translate → Translated Response → User
```

**Flow:**
1. User sends a message to the Lex chatbot
2. Lex identifies the `TranslationIntent` and collects two slots: `language` and `text`
3. On fulfillment, Lex invokes the Lambda function with the slot values
4. Lambda validates inputs, maps the language name to an Amazon Translate language code, and calls the Translate API
5. The translated text is returned to Lex and displayed to the user

---

## ☁️ AWS Services Used

| Service | Purpose |
|---|---|
| Amazon Lex V2 | Conversational interface — intent, utterances, slots |
| AWS Lambda (Python 3.12) | Business logic — input validation, translation, error handling |
| Amazon Translate | Real-time text translation |
| AWS IAM | Least-privilege role for Lambda execution |
| Amazon CloudWatch | Structured logging of Lambda executions |

---

## 🌍 Supported Languages

| Language | Amazon Translate Code |
|---|---|
| French | `fr` |
| Japanese | `ja` |
| Chinese | `zh` |
| Spanish | `es` |
| Sinhala | `si` |

> **Extending support:** To add a new language, add it to the `language_codes` dictionary in `lambda_function.py` and add the same value to the `language` slot type in Lex.

---

## 🔐 Security Design

A **custom least-privilege IAM role** (`TranslateLambdaAccess`) was created for the Lambda function with only the permissions it actually needs:

- `translate:TranslateText` — the single Translate API action used
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` — via `AWSLambdaBasicExecutionRole`

This intentionally avoids broad managed policies like `TranslateFullAccess`, which grant unnecessary permissions such as creating/deleting translation terminology. See [`iam-policy.json`](./iam-policy.json) for the full policy document.

---

## 📁 Repository Structure

```
├── lambda_function.py      # Lambda handler — translation logic
├── iam-policy.json         # Least-privilege IAM policy for Lambda role
├── test-event.json         # Sample Lex V2 event for local Lambda testing
└── README.md
```

---

## 🚀 Deployment Guide

### Prerequisites
- AWS account with access to Lex, Lambda, Translate, and IAM
- Python 3.12 runtime available in your AWS region

### Step 1 — Create the IAM Role
1. Navigate to **IAM → Roles → Create Role**
2. Trusted entity: **AWS Service → Lambda**
3. Attach `AWSLambdaBasicExecutionRole` (managed policy)
4. Add the inline policy from [`iam-policy.json`](./iam-policy.json) to restrict Translate access to `translate:TranslateText` only
5. Name the role `TranslateLambdaAccess`

### Step 2 — Create the Lambda Function
1. Navigate to **Lambda → Create Function**
2. Runtime: **Python 3.12**
3. Execution role: select `TranslateLambdaAccess`
4. Paste the code from [`lambda_function.py`](./lambda_function.py)
5. Click **Deploy**
6. Test using the event in [`test-event.json`](./test-event.json)

### Step 3 — Create the Lex Bot
1. Navigate to **Amazon Lex → Create Bot → Create a blank bot**
2. Bot name: `TextTranslator`
3. IAM: Create a role with basic Lex permissions
4. COPPA: No
5. Language: English (US)

### Step 4 — Configure the Intent
1. Create intent named `TranslationIntent`
2. Add sample utterances:
   - `I want to translate`
   - `Can you help me translate`
   - `Translate for me`
   - `I want to translate in {language}`
   - `Translate in {language}`
   - `Can you translate in {language} for me?`
3. Create a custom slot type named `language` with values: French, Japanese, Chinese, Spanish, Sinhala
4. Add slots in priority order:
   - Priority 1: `language` (type: `language`) — prompt: *"In which language would you like to translate the text?"*
   - Priority 2: `text` (type: `AMAZON.FreeFormInput`) — prompt: *"Please input the text you want to translate."*
5. Initial response: `Sure...!!! I can help you with that.`
6. Fulfillment: Enable Lambda, set success message to `Your request has been completed successfully`
7. Closing response: `I hope the translation was helpful!`
8. Save Intent

### Step 5 — Connect Lambda to the Bot Alias
1. Navigate to your bot → **Aliases → TestBotAlias**
2. Under **Languages → English (US)**, select your Lambda function
3. Version: `$LATEST`
4. Save

### Step 6 — Build and Test
1. Click **Build**
2. Click **Test** and start a conversation

---

## 💬 Example Conversation

```
User:  I want to translate
Bot:   Sure...!!! I can help you with that.
Bot:   In which language would you like to translate the text?
User:  French
Bot:   Please input the text you want to translate.
User:  Hello
Bot:   Bonjour
Bot:   I hope the translation was helpful!
```

---

## 🧪 Testing

The Lambda function can be tested independently using the test event in [`test-event.json`](./test-event.json), which replicates the exact Lex V2 event format passed to Lambda.

**Test scenarios:**

| Scenario | Input | Expected Output |
|---|---|---|
| Happy path | text: "Hello", language: "French" | "Bonjour" |
| Empty input | text: "", language: "French" | Error: "Input text is empty." |
| Unsupported language | text: "Hello", language: "Arabic" | Error: "Unsupported language: Arabic" |
| Auto language detection | text: "Bonjour", language: "Japanese" | Translated from French to Japanese |

> **Note:** `SourceLanguageCode='auto'` was chosen deliberately — Amazon Translate auto-detects the source language, so the chatbot works regardless of what language the user types in.

---

## 🔧 Troubleshooting

**Build error: slot names in utterances not valid**
Ensure slot references in utterances use lowercase and are separated by whitespace — e.g. `{language}`, not `{Language}` or `translate in{language}`.

**Build error: slot priority not defined**
In the Lex intent, slots must have an explicit priority order. Drag `language` above `text` in the Slots section so language = priority 1.

**Lambda works in isolation but chatbot doesn't call it**
In Lex V2, Lambda must be attached at the alias level. Navigate to **Aliases → TestBotAlias → Languages → English (US)** and select your Lambda function there.

**Chatbot returns Lex fulfilment message instead of translated text**
Confirm "Use a Lambda function for fulfillment" is checked under Fulfillment → Advanced Options in the intent. Lambda's response overrides the Lex-level message.

---

## 📌 Key Engineering Decisions

- **Least-privilege IAM** — custom inline policy scoped to `translate:TranslateText` only, rather than the broad `TranslateFullAccess` managed policy
- **Auto source language detection** — `SourceLanguageCode='auto'` allows users to type in any language without needing to specify the source
- **Structured error logging** — Python `logging` module used instead of `print()` for CloudWatch-compatible structured logs
- **Slot-in-utterance design** — utterances like `I want to translate in {language}` allow Lex to skip the language prompt if already provided, reducing conversation turns
- **Validated error handling** — Lambda validates empty input and unsupported languages before calling the Translate API, returning meaningful error messages to the user

---

## 📜 License

MIT
