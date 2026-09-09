"""Gmail: ongelezen mail in de inbox, met deeplink per thread."""
from __future__ import annotations

from datetime import datetime
from email.utils import parseaddr
from pathlib import Path
from zoneinfo import ZoneInfo

from ..models import Item
from ._google import load_credentials


class GmailSource:
    name = "gmail"
    label = "Gmail"
    interval = 2 * 60

    def __init__(self, *, token_file: Path, tz: ZoneInfo, max_results: int = 30):
        self.token_file, self.tz, self.max_results = token_file, tz, max_results

    def configured(self) -> bool:
        return self.token_file.exists()

    def fetch(self) -> list[Item]:
        from googleapiclient.discovery import build

        service = build("gmail", "v1", credentials=load_credentials(self.token_file), cache_discovery=False)
        listing = service.users().messages().list(
            userId="me", q="is:unread in:inbox", maxResults=self.max_results
        ).execute()
        items: list[Item] = []
        for ref in listing.get("messages", []):
            msg = service.users().messages().get(
                userId="me", id=ref["id"], format="metadata", metadataHeaders=["From", "Subject"]
            ).execute()
            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
            sender_name, sender_addr = parseaddr(headers.get("from", ""))
            received = datetime.fromtimestamp(int(msg["internalDate"]) / 1000, tz=self.tz)
            items.append(Item(
                source=self.name, external_id=msg["id"], kind="mail",
                title=headers.get("subject") or "(geen onderwerp)",
                start=received,
                url=f"https://mail.google.com/mail/u/0/#all/{msg['threadId']}",
                subtitle=sender_name or sender_addr,
                meta={"snippet": msg.get("snippet", "")[:200], "from": sender_addr},
            ))
        return items
