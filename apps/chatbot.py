from langchain_groq import ChatGroq
import os
import streamlit as st
import json
import re
import pandas as pd
from datetime import datetime
from email_reader import get_latest_emails
from dotenv import load_dotenv
load_dotenv()

llm=ChatGroq(model="openai/gpt-oss-20b")

def analyze_email(sender, subject, email_text, urls):
        prompt = f"""
            You are a cybersecurity email analysis expert.

            Analyze the email for:

            1. Phishing attempts
            2. Credential theft
            3. Suspicious URLs
            4. Social engineering
            5. Urgency tactics
            6. Sender impersonation
            7. Financial scams

            Risk Score Rules:
            0 = Legitimate
            1-3 = Low Risk
            4-6 = Medium Risk
            7-8 = High Risk
            9-10 = Critical

            Return ONLY valid JSON.

            {{
                "risk_score": 0,
                "classification": "",
                "threat_type": "",
                "reasons": []
            }}

            Sender: {sender}

            Subject: {subject}

            URLs found:
            {urls}

            Email Content:
            {email_text}
        """

        response=llm.invoke(prompt)
        return response.content


def detect_intent(sender, subject, email_text):

    prompt = f"""
    You are an email intent classifier.

    Classify the email into ONE of these categories:

    - Interview Invitation
    - Interview Follow-up
    - Customer Query
    - Support Ticket
    - Meeting Request
    - Newsletter
    - Promotional Email
    - Order Confirmation
    - Account Notification
    - Bank Alert
    - OTP

    Return ONLY valid JSON.

    {{
        "intent": "",
        "reason": ""
    }}

    Sender:
    {sender}

    Subject:
    {subject}

    Email:
    {email_text}
    """

    response = llm.invoke(prompt)
    return response.content


def decision_agent(risk_score, intent):

    if risk_score >= 7:
        return "Threat", "⚠️ Email is suspicious or high risk. Do not reply."

    if intent in [
        "Newsletter",
        "Promotional Email",
        "OTP",
        "Bank Alert",
        "Order Confirmation",
        "Account Notification"
    ]:
        return "No Reply Needed", f"This is an informational email ({intent}). No reply required."

    if intent in [
        "Interview Invitation",
        "Interview Follow-up",
        "Customer Query",
        "Support Ticket",
        "Meeting Request"
    ]:
        return "Reply Recommended", f"This email requires a response ({intent})."

    return "No Reply Needed", "No reply required for this email type."


def generate_reply(sender, subject, email_text):

    prompt = f"""
    Generate a professional email response.

    Return only the email body.

    Sender:
    {sender}

    Subject:
    {subject}

    Email:
    {email_text}
    """

    response = llm.invoke(prompt)

    return response.content


st.title("AI email analyzer")
st.markdown("This app uses the Groq LLM to analyze emails and provide insights.")

tab1, tab2 = st.tabs(
    ["📬 Gmail Analysis", "✍️ Manual Analysis"]
)


with tab1:

    if st.button("Analyze Last 10 Emails"):

        emails = get_latest_emails()

        rows = []

        for email in emails:

            urls = re.findall(
                r'https?://[^\s]+',
                email["body"]
            )

            try:
                response = analyze_email(
                    email["sender"],
                    email["subject"],
                    email["body"],
                    urls
                )
                response = response.replace("```json", "")
                response = response.replace("```", "")
                response = response.strip()

                result = json.loads(response)

                rows.append({
                    "Sender": email["sender"],
                    "Subject": email["subject"],
                    "Risk Score": result["risk_score"],
                    "Classification": result["classification"],
                    "Threat Type": result["threat_type"]
                })

            except Exception as e:
                rows.append({
                    "Sender": email["sender"],
                    "Subject": email["subject"],
                    "Risk Score": "Error",
                    "Classification": str(e),
                    "Threat Type": "-"
                })

        st.subheader("Latest 10 Email Analysis")

        df = pd.DataFrame(rows)

        st.dataframe(
            df,
            use_container_width=True
        )

with tab2:

    sender = st.text_input(
        "Sender Email",
        value=st.session_state.get("sender", "")
    )

    subject = st.text_input(
        "Subject",
        value=st.session_state.get("subject", "")
    )

    email_text = st.text_area(
        "enter the mail text here",
        value=st.session_state.get("email", ""),
        height=250
    )

    urls = re.findall(
        r'https?://[^\s]+',
        email_text
    )

    if st.button("Analyze"):

        try:
            # Step 1: Security Analysis
            response = analyze_email(
                sender,
                subject,
                email_text,
                urls
            )

            response = response.replace("```json", "")
            response = response.replace("```", "")
            response = response.strip()

            result = json.loads(response)

            history = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sender": sender,
                "subject": subject,
                "risk_score": result["risk_score"],
                "classification": result["classification"],
                "threat_type": result["threat_type"]
            }

            df = pd.DataFrame([history])

            if os.path.exists("history.csv"):
                df.to_csv(
                    "history.csv",
                    mode="a",
                    header=False,
                    index=False
                )
            else:
                df.to_csv(
                    "history.csv",
                    index=False
                )

            st.metric(
                "Risk Score",
                result["risk_score"]
            )

            score = result["risk_score"]

            if score == 0:
                st.success("🟢 Legitimate")
            elif score <= 3:
                st.info("🔵 Low Risk")
            elif score <= 6:
                st.warning("🟡 Medium Risk")
            elif score <= 8:
                st.warning("🟠 High Risk")
            else:
                st.error("🔴 Critical")

            st.write("### Reasons")

            reasons = result.get("reasons", [])

            if reasons:
                for reason in reasons:
                    st.write(f"• {reason}")
            else:
                st.warning("No reasons returned by the model.")

            st.subheader("🔗 URLs Found")

            if urls:
                for url in urls:
                    st.write(url)
            else:
                st.write("No URLs Found")

            # Step 2: Intent Classification
            st.subheader("🧠 Intent Classification")

            intent_response = detect_intent(sender, subject, email_text)
            intent_response = intent_response.replace("```json", "")
            intent_response = intent_response.replace("```", "")
            intent_response = intent_response.strip()

            intent_result = json.loads(intent_response)

            intent = intent_result.get("intent", "Other")
            intent_reason = intent_result.get("reason", "")

            st.write(f"**Email Type:** {intent}")
            st.write(f"**Reason:** {intent_reason}")

            # Step 3: Decision Engine
            st.subheader("🤖 Decision Engine")

            decision, decision_message = decision_agent(score, intent)

            if decision == "Threat":
                st.error(f"🚨 {decision_message}")

            elif decision == "No Reply Needed":
                st.info(f"ℹ️ {decision_message}")

            elif decision == "Reply Recommended":
                st.success(f"✅ {decision_message}")

                # Step 4: Auto-generate Reply
                st.subheader("📧 AI Generated Reply")

                reply = generate_reply(sender, subject, email_text)
                st.text_area("Reply", value=reply, height=300)

            st.button("View History")

            if os.path.exists("history.csv"):
                history_df = pd.read_csv("history.csv")
                st.dataframe(history_df)

        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
