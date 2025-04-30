import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")
# Configuration
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True,
)


def upload_file(file, resource_type: str = "image"):
    upload_result = cloudinary.uploader.upload(file, resource_type=resource_type)
    return upload_result


# {
#     "asset_id": "e0005941583938f1655b2c993ff0e450",
#     "public_id": "upeh7kytuxhtqowadndb",
#     "version": 1745755777,
#     "version_id": "85f96e64b8d528aa65675a8733917465",
#     "signature": "92f68780af7d3caa0b5570b014d0f0304e283663",
#     "width": 1920,
#     "height": 1080,
#     "format": "webm",
#     "resource_type": "video",
#     "created_at": "2025-04-27T12:09:37Z",
#     "tags": [],
#     "pages": 0,
#     "bytes": 1862518,
#     "type": "upload",
#     "etag": "2b77f7eec18243a36abfbfc3e995f0ee",
#     "placeholder": False,
#     "url": "http://res.cloudinary.com/dhzgncfkp/video/upload/v1745755777/upeh7kytuxhtqowadndb.webm",
#     "secure_url": "https://res.cloudinary.com/dhzgncfkp/video/upload/v1745755777/upeh7kytuxhtqowadndb.webm",
#     "playback_url": "https://res.cloudinary.com/dhzgncfkp/video/upload/sp_auto/v1745755777/upeh7kytuxhtqowadndb.m3u8",
#     "asset_folder": "",
#     "display_name": "upeh7kytuxhtqowadndb",
#     "audio": {},
#     "video": {
#         "pix_format": "yuv420p",
#         "codec": "vp8",
#         "level": -99,
#         "profile": "0",
#         "dar": "16:9",
#         "time_base": "1/1000",
#     },
#     "frame_rate": 1000.0,
#     "bit_rate": 345682,
#     "duration": 43.103532,
#     "rotation": 0,
#     "original_filename": "stream",
#     "api_key": "852279936257297",
# }

# {
#     "asset_id": "650b1272f58dbfdde89786bb560b822a",
#     "public_id": "vnejbpbtzbkxe9po7ujp",
#     "version": 1745756007,
#     "version_id": "85d5c37a53c5f5516b66c1b6c7c0310b",
#     "signature": "607e64879a3108ffb0a20d45795139c94a49563a",
#     "width": 612,
#     "height": 792,
#     "format": "pdf",
#     "resource_type": "image",
#     "created_at": "2025-04-27T12:13:27Z",
#     "tags": [],
#     "pages": 406,
#     "bytes": 2725248,
#     "type": "upload",
#     "etag": "12cbb3386b15984384744ac9012d844b",
#     "placeholder": False,
#     "url": "http://res.cloudinary.com/dhzgncfkp/image/upload/v1745756007/vnejbpbtzbkxe9po7ujp.pdf",
#     "secure_url": "https://res.cloudinary.com/dhzgncfkp/image/upload/v1745756007/vnejbpbtzbkxe9po7ujp.pdf",
#     "asset_folder": "",
#     "display_name": "vnejbpbtzbkxe9po7ujp",
#     "original_filename": "stream",
#     "api_key": "852279936257297",
# }
