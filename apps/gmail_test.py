from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json",
    SCOPES
)
creds = flow.run_local_server(port=0)
service = build("gmail", "v1", credentials=creds)
results = service.users().messages().list(
    userId="me",
    maxResults=1
).execute()
messages = results.get("messages", [])
msg = service.users().messages().get(
    userId="me",
    id=messages[0]["id"]
).execute()
headers = msg["payload"]["headers"]
sender = ""
subject = ""
body = ""
try:
    if "parts" in msg["payload"]:
        for part in msg["payload"]["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data")
                if data:
                    body = base64.urlsafe_b64decode(
                        data
                    ).decode("utf-8")
                break
except Exception as e:
    print("Body extraction error:", e)
print("\nEmail Body:\n")
print(body[:1000])
for header in headers:
    if header["name"] == "From":
        sender = header["value"]
    if header["name"] == "Subject":
        subject = header["value"]
print("Sender:", sender)
print("Subject:", subject)