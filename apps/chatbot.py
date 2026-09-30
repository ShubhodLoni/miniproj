from langchain_groq import ChatGroq
import os
import streamlit as st
import json
import re
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

llm=ChatGroq(model="openai/gpt-oss-20b")

st.title("AI email analyzer")
st.markdown("This app uses the Groq LLM to analyze emails and provide insights.")

sender = st.text_input("Sender Email")

subject = st.text_input("Subject")


email_text = st.text_area("enter the mail text here",height=250)
urls = re.findall(r'https?://[^\s]+', email_text)
if st.button("Analyze"):
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
    
    try:
        result = json.loads(response.content)

        history={
            "timestamp":datetime.now().strftime("%Y-%M-%D %H-%m-%S"),
            "sender":sender,
            "subject":subject,
            "risk_score":result["risk_score"],
            "classification":result["classification"],
            "threat_type":result["threat_type"]

        }
        df=pd.DataFrame([history])
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

        st.metric("Risk Score", result["risk_score"])
        classification = result["classification"].strip().lower()
        score=result["risk_score"]
        if score == 0:
            st.success(f"🟢 Legitimate")
        elif score <= 3:
            st.info(f"🔵 Low Risk")
        elif score <= 6:
            st.warning(f"🟡 Medium Risk")
        elif score <= 8:
            st.warning(f"🟠 High Risk")
        else: 
            st.error(f"🔴 Critical")
            
        st.write("### Reasons")
        reasons = result.get("reasons",[])
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

        st.button("View History")
        if os.path.exists("history.csv"):
            history_df = pd.read_csv("history.csv")
            st.dataframe(history_df)
         
    except Exception as e:
        st.error("Could not parse AI response")
        st.write("Raw Response:")
        st.code(response.content)
        st.write(e)

  