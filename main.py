import streamlit as st
from PIL import Image
import os
import zipfile
import io
import threading

# Function to convert bytes to a human-readable format
def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

# Lossless compression function
def lossless_compression(img, img_format):
    """
    Performs lossless compression on an image.

    Args:
    img (PIL.Image): Input image.
    img_format (str): Image format.

    Returns:
    PIL.Image: Compressed image.
    int: Space saved (in bytes)
    """
    # Convert image to RGB mode (in case of RGBA)
    img = img.convert('RGB')

    # Save the original image to a buffer
    original_buffer = io.BytesIO()
    img.save(original_buffer, format=img_format)
    original_size = len(original_buffer.getvalue())

    # Save the image with optimized settings (lossless compression)
    compressed_buffer = io.BytesIO()
    img.save(compressed_buffer, format=img_format, optimize=True)
    compressed_size = len(compressed_buffer.getvalue())

    return compressed_buffer, original_size - compressed_size

# Function to process images in parallel
def process_images(uploaded_files):
    compressed_images = []
    space_saved = []

    for uploaded_file in uploaded_files:
        img_format = uploaded_file.name.split('.')[-1]

        if img_format.lower() in ['jpg', 'jpeg']:
            # For JPEG images, read in binary mode
            img_data = uploaded_file.getvalue()
            img = Image.open(io.BytesIO(img_data))
        else:
            # For other formats, open normally
            img = Image.open(uploaded_file)

        # Get image format from file name
        img_format = img.format.lower()

        # Perform compression
        compressed_img, saved = lossless_compression(img, img_format)
        compressed_images.append(compressed_img)
        space_saved.append(saved)

    return compressed_images, space_saved

# Main Streamlit app
def main():
    st.set_page_config(
        page_title="Image Compression Tool",
        page_icon="🗜️",
        layout="wide",
    )
    st.title("🗜️ Image Compression Tool", anchor=False)

    session_state = st.session_state
    if not hasattr(session_state, 'processed_images'):
        session_state.processed_images = None

    uploaded_files = st.file_uploader("Upload Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        if session_state.processed_images is None:
            with st.spinner("Processing..."):
                # Process images in parallel using threads
                compressed_images, space_saved = process_images(uploaded_files)
                session_state.processed_images = {
                    "compressed_images": compressed_images,
                    "space_saved": space_saved,
                    "original_filenames": [file.name for file in uploaded_files]
                }
        else:
            compressed_images = session_state.processed_images["compressed_images"]
            space_saved = session_state.processed_images["space_saved"]

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, compressed_img in enumerate(compressed_images):
                original_filename = session_state.processed_images["original_filenames"][i]
                filename, file_extension = os.path.splitext(original_filename)
                img_extension = file_extension[1:]  # Remove the dot
                optimized_filename = f"{filename}_optimized.{img_extension}"
                zip_file.writestr(optimized_filename, compressed_img.getvalue())
        zip_buffer.seek(0)

        st.download_button(
            label="Download Compressed Images",
            type="primary",
            data=zip_buffer,
            file_name="compressed_images.zip",
            mime="application/zip"
        )

        st.subheader("Compressed Images", anchor=False)
        num_images = len(compressed_images)
        num_rows = (num_images + 3) // 4
        for i in range(num_rows):
            cols = st.columns(4)
            for j in range(4):
                index = i * 4 + j
                if index < num_images:
                    original_filename = session_state.processed_images["original_filenames"][index]
                    cols[j].image(compressed_images[index], caption=f"{original_filename} -- Space Saved: {sizeof_fmt(space_saved[index])}", width=200)

if __name__ == "__main__":
    main()
