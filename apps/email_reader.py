from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

CREDENTIALS_PATH = os.path.join(
    BASE_DIR,
    "credentials.json"
)

def get_latest_emails():
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_PATH,
        SCOPES
    )

    creds = flow.run_local_server(port=0)

    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    results = service.users().messages().list(
        userId="me",
        maxResults=10
    ).execute()

    messages = results.get("messages", [])

    email_list = []

    for message in messages:
        msg = service.users().messages().get(
            userId="me",
            id=message["id"]
        ).execute()

        sender = ""
        subject = ""

        headers = msg["payload"]["headers"]

        for header in headers:
            if header["name"] == "From":
                sender = header["value"]

            elif header["name"] == "Subject":
                subject = header["value"]

        body = msg.get("snippet", "")

        email_list.append({
            "sender": sender,
            "subject": subject,
            "body": body
        })

    return email_list