import argparse
import logging
import os
import asyncio
from mimetypes import guess_extension
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto

load_dotenv()
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

FILE_CATEGORIES = {
    "images": ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "heic", "raw"],
    "documents": ["pdf", "doc", "docx", "odt", "rtf", "xls", "xlsx", "csv", "ppt", "pptx", "txt", "epub"],
    "videos": ["mp4", "mkv", "avi", "mov", "wmv"],
    "audios": ["mp3", "wav", "aac", "flac", "ogg", "m4a"],
    "archives": ["zip", "rar", "7z", "tar", "gz", "bz2"],
}

def cleanup_incomplete_files(output_dir):
    if not os.path.exists(output_dir): return
    for file in os.listdir(output_dir):
        if file.endswith(".tmp"):
            os.remove(os.path.join(output_dir, file))

def check_and_download_file(client, message, file_path):
    try:
        if os.path.exists(file_path):
            logging.info(f"File already exists: {file_path}")
            return True, os.path.getsize(file_path)
        temp_file_path = file_path + ".tmp"
        downloaded_file = client.loop.run_until_complete(client.download_media(message, file=temp_file_path))
        if downloaded_file and os.path.exists(temp_file_path):
            os.rename(temp_file_path, file_path)
            logging.info(f"Downloaded: {file_path}")
            return True, os.path.getsize(file_path)
    except Exception as error:
        logging.error(f"Failed: {error}")
    return False, 0

def download_files_from_entity(entity_identifier, file_type=None, save_directory=".", message_limit=100, search_query=None):
    os.makedirs(save_directory, exist_ok=True)
    cleanup_incomplete_files(save_directory)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = TelegramClient("session_name", API_ID, API_HASH, loop=loop)
    
    with client:
        try: entity = int(entity_identifier)
        except: entity = entity_identifier
        
        count = 0
        for message in client.iter_messages(entity, limit=message_limit):
            if not message.media or not message.file: continue
            
            fname = message.file.name or str(message.id)
            ext = (guess_extension(message.file.mime_type) or "").lstrip(".")
            if ext and not fname.lower().endswith(f".{ext.lower()}"): fname += f".{ext}"

            # Filter by search query if provided
            if search_query and search_query.lower() not in fname.lower():
                continue

            file_path = os.path.join(save_directory, fname)
            success, size = check_and_download_file(client, message, file_path)
            
            if success:
                count += 1
                # If we are searching for a specific keyword, stop after the first match
                if search_query:
                    break 

    logging.info(f"Done. Downloaded {count} files.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("entity", nargs="?")
    parser.add_argument("-f", "--format")
    parser.add_argument("-o", "--output", default=".")
    parser.add_argument("-l", "--limit", type=int, default=100)
    parser.add_argument("-s", "--search", type=str) # New Search Arg
    args = parser.parse_args()
    if args.entity:
        download_files_from_entity(args.entity, args.format, args.output, args.limit, args.search)
