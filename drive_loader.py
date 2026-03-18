"""
drive_loader.py — Google Drive PDF sync
Connects to your personal Google Drive using a service account.
Downloads PDFs from a specific folder and loads them into the knowledge base.

Setup:
1. Go to console.cloud.google.com
2. Create a project → Enable Google Drive API
3. Create a Service Account → download JSON key
4. Save the JSON key as 'service_account.json' in the kisanbot folder
5. Share your Google Drive folder with the service account email
6. Add DRIVE_FOLDER_ID to .env
"""

import os
import io
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

import pdf_loader

SCOPES         = ["https://www.googleapis.com/auth/drive.readonly"]
SERVICE_ACCOUNT_FILE = Path("service_account.json")
DATA_DIR       = Path("data")

def _get_service():
    """Build Google Drive service using service account."""
    if not SERVICE_ACCOUNT_FILE.exists():
        raise FileNotFoundError(
            "service_account.json not found. "
            "Download it from Google Cloud Console and place in kisanbot folder."
        )
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

def sync_drive_pdfs():
    """
    Download all PDFs from the Google Drive folder specified in DRIVE_FOLDER_ID.
    Skips files already downloaded. Loads new files into the knowledge base.
    """
    folder_id = os.getenv("DRIVE_FOLDER_ID")
    if not folder_id:
        print("[drive_loader] DRIVE_FOLDER_ID not set in .env — skipping Drive sync.")
        return

    try:
        service = _get_service()
        print(f"[drive_loader] Syncing PDFs from Drive folder: {folder_id}")

        # List all PDF files in the folder
        results = service.files().list(
            q=f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false",
            fields="files(id, name)"
        ).execute()

        files = results.get("files", [])
        if not files:
            print("[drive_loader] No PDFs found in Drive folder.")
            return

        DATA_DIR.mkdir(exist_ok=True)
        new_count = 0

        for file in files:
            file_name = file["name"]
            file_id   = file["id"]
            save_path = DATA_DIR / file_name

            # Skip if already downloaded
            if save_path.exists():
                print(f"[drive_loader] Already exists, skipping: {file_name}")
                continue

            # Download the PDF
            print(f"[drive_loader] Downloading: {file_name}")
            request  = service.files().get_media(fileId=file_id)
            buf      = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            # Save to data/ folder
            with open(save_path, "wb") as f:
                f.write(buf.getvalue())

            # Load into knowledge base immediately
            pdf_loader._ingest(save_path)
            new_count += 1
            print(f"[drive_loader] Loaded: {file_name}")

        print(f"[drive_loader] Sync complete. {new_count} new PDF(s) loaded.")

    except Exception as e:
        print(f"[drive_loader] Drive sync failed: {e}")
        print("[drive_loader] Continuing with existing local PDFs.")
