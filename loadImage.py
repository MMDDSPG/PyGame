from PIL import Image
import numpy as np
def load_and_resize_image(path, width, height):
    img = Image.open(path).convert("RGB")
    img = img.resize((width, height), Image.LANCZOS)
    arr = np.array(img)
    return arr