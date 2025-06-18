import os
import datetime
import json
import subprocess
from huey import SqliteHuey, crontab
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.service_account import Credentials
import settings

# Huey instance with SQLite backend
huey = SqliteHuey(filename=settings.HUEY_SQLITE)

# Google Drive API Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
GOOGLE_SERVICE_ACCOUNT_JSON = settings.GOOGLE_SERVICE_ACCOUNT_JSON
FOLDER_ID = settings.FOLDER_ID  # Folder ID where backups are stored
LOCAL_DB_PATH = settings.LOCAL_DB_PATH  # SQLite database path
LOCAL_RESTORE_PATH = settings.LOCAL_RESTORE_PATH  # Restored database path

def get_drive_service():
    """Authenticate and return a Google Drive API service instance."""
    try:
        # Parse the service account JSON from the environment variable
        service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        credentials = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        raise RuntimeError(f"Failed to authenticate Google Drive service: {e}")

# Backup Task
@huey.task()
def backup_to_drive():
    """Backs up the database and uploads to Google Drive with a date-based file name."""
    try:
        # Generate a timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        compressed_path = f'/tmp/db_backup_{timestamp}.gz'
        backup_file_name = f'db_backup_{timestamp}.gz'

        # Backup and compress the database using subprocess for security
        
        # Use subprocess instead of os.system to prevent shell injection
        subprocess.run([
            'sqlite3', LOCAL_DB_PATH, 'VACUUM INTO "/tmp/db_backup"'
        ], check=True)
        subprocess.run(['gzip', '/tmp/db_backup'], check=True)
        os.rename('/tmp/db_backup.gz', compressed_path)  # Rename to include the timestamp

        # Upload to Google Drive
        service = get_drive_service()
        file_metadata = {
            'name': backup_file_name,
            'parents': [FOLDER_ID],
        }
        media = MediaFileUpload(compressed_path, mimetype='application/gzip')
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Backup {backup_file_name} uploaded successfully.")
    except Exception as e:
        print(f"Error during backup: {e}")

# Periodic Backup Task
@huey.periodic_task(crontab(hour=0, minute=0))  # Runs nightly at midnight
def nightly_backup():
    """Backs up the database to Google Drive nightly."""
    backup_to_drive()

# Restore Task
@huey.task()
def restore_from_drive(restore_date=None):
    """
    Restores a backup from Google Drive.
    If `restore_date` is provided (YYYY-MM-DD), restores the backup closest to that date.
    """
    try:
        service = get_drive_service()

        # List all backups in the folder
        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents and mimeType='application/gzip'",
            orderBy='createdTime desc',
            pageSize=100,  # Adjust as needed
            fields='files(id, name, createdTime)'
        ).execute()

        files = results.get('files', [])
        if not files:
            print("No backup files found.")
            return

        # Filter backups by date if restore_date is provided
        if restore_date:
            restore_date = datetime.datetime.strptime(restore_date, '%Y-%m-%d')
            files = [
                f for f in files
                if restore_date.date() == datetime.datetime.fromisoformat(f['createdTime']).date()
            ]
            if not files:
                print(f"No backups found for date {restore_date.date()}.")
                return

        # Restore the latest or filtered backup
        latest_file = files[0]
        file_id = latest_file['id']
        file_name = latest_file['name']

        print(f"Downloading backup: {file_name}")
        file_path = f"/tmp/{file_name}"
        request = service.files().get_media(fileId=file_id)

        with open(file_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download progress: {int(status.progress() * 100)}%")

        # Decompress and restore using subprocess for security
        print("Decompressing the backup...")
        with open(LOCAL_RESTORE_PATH, 'wb') as restore_file:
            subprocess.run(['gunzip', '-c', file_path], stdout=restore_file, check=True)
        print(f"Backup restored successfully to: {LOCAL_RESTORE_PATH}")
    except Exception as e:
        print(f"Error during restore: {e}")

