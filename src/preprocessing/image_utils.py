import cv2
import numpy as np
from PIL import Image

def preprocess_image(pil_image):
    img_cv = np.array(pil_image)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)  # we are clearing noise from image and converting it into black and white
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    denoised = cv2.medianBlur(binary, 3)

    return Image.fromarray(denoised)


