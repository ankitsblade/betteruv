import fitz
from PIL import Image
import cv2
import numpy as np


def document_preview() -> dict[str, object]:
    page = Image.new("RGB", (16, 16), color="white")
    arr = np.asarray(page)
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    doc = fitz.open()
    return {
        "pixels": int(bgr.size),
        "pages": int(doc.page_count),
    }
