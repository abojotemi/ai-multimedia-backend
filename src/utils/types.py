from typing import Literal

FileType = Literal["image" , "video" , "audio" , "file", "unknown"]
ProcessType = Literal["pending", "uploading", "processing", "completed", "failed"]