def load_image(image_path):
    from PIL import Image, ImageOps
    import os

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"The image at {image_path} does not exist.")
    
    try:
        image = Image.open(image_path)
        image = image.convert("RGB")
        # Apply automatic contrast with a small cutoff to remove extreme outliers
        image = ImageOps.autocontrast(image, cutoff=3)
        return image
    except Exception as e:
        raise RuntimeError(f"Failed to load image: {e}")

def save_image(image, save_path):
    try:
        image.save(save_path)
    except Exception as e:
        raise RuntimeError(f"Failed to save image: {e}")

def get_image_filenames(folder_path):
    import os

    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"The path {folder_path} is not a directory.")
    
    return [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]