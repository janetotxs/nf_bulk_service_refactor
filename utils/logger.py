import logging
import sys
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
from googleapiclient.discovery import build
from io import StringIO
from utils.google_sheet import GSheetClient

# from smp.smp_constant import SMPConstants
from utils.env_loader import get_env_variable


def setup_logger(service_name: str, gs_client: GSheetClient = None):
    # smp = get_env_variable("ROOT_LOG_FOLDER_ID")
    logger, log_stream = setup_in_memory_logger(service_name)

    if gs_client:

        logger.gs_client = gs_client
        logger.log_stream = log_stream
        # logger.smp = smp

    else:
        logger.warning("gs_client not provided — skipping Drive upload.")

    return logger


# Full tracebacks only to the log file
def log_traceback(logger):
    import traceback

    traceback_str = traceback.format_exc()
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.acquire()
            try:
                handler.stream.write(traceback_str + "\n")
                handler.flush()
            finally:
                handler.release()


def setup_in_memory_logger(service_name: str) -> tuple[logging.Logger, StringIO]:
    log_stream = StringIO()
    logger = logging.getLogger(service_name)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt=f"[%(asctime)s,%(msecs)03d]: [{service_name}] : [%(levelname)s]:[%(filename)s:%(lineno)d - %(funcName)s()]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # In-memory handler
    stream_handler = logging.StreamHandler(log_stream)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger, log_stream


def create_drive_folder(service, name: str, parent_id: str = None) -> str:
    """Create a folder in Drive (or return existing one)."""
    query = f"mimeType='application/vnd.google-apps.folder' and trashed=false and name='{name}'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = (
        service.files()
        .list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    items = results.get("files", [])
    if items:
        return items[0]["id"]
    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id] if parent_id else [],
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder["id"]


def create_nested_drive_path(
    service, base_folder_id: str, path_parts: list[str]
) -> str:
    """Create nested folders like ['2025', '06', '20', '14'] under a base folder."""
    current_folder_id = base_folder_id
    for part in path_parts:
        current_folder_id = create_drive_folder(service, part, current_folder_id)
    return current_folder_id


def upload_log_to_drive(service, content: str, filename: str, folder_id: str):
    media = MediaIoBaseUpload(StringIO(content), mimetype="text/plain")
    file_metadata = {"name": filename, "parents": [folder_id]}
    uploaded_file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, name")
        .execute()
    )
    print(f"Uploaded log: {uploaded_file['name']} to Google Drive")


def finalize_log_upload(logger):
    # Uploads the in-memory logs to Drive after process ends.
    print("finalize_log_upload() called")
    if (
        hasattr(logger, "gs_client")
        and hasattr(logger, "log_stream")
        # and hasattr(logger, "smp")
    ):
        from googleapiclient.discovery import build
        from datetime import datetime

        drive = build("drive", "v3", credentials=logger.gs_client.credentials)
        now = datetime.now()
        filename = f"{logger.name}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.log"
        subfolders = [
            now.strftime("%Y"),
            now.strftime("%B"),
            now.strftime("%d"),
            now.strftime("%H"),
        ]
        target_folder_id = create_nested_drive_path(
            drive, get_env_variable("ROOT_LOG_FOLDER_ID"), subfolders
        )

        upload_log_to_drive(
            drive, logger.log_stream.getvalue(), filename, target_folder_id
        )
        logger.info("Logs uploaded to Google Drive.")
