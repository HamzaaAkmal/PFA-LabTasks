# --- Keep all previous necessary imports ---
import streamlit as st
import cv2
import easyocr
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from ultralytics import YOLO
import numpy as np
import os
import logging

# --- Configuration ---
YOLO_MODEL_PATH = "best.pt"
FONT_DIR = "fonts"
FONT_REGULAR_PATH = os.path.join(FONT_DIR, "Poppins-Regular.ttf")
FONT_BOLD_PATH = os.path.join(FONT_DIR, "Poppins-Bold.ttf")
# URDU_FONT_PATH REMOVED
SLIP_FILENAME = "generated_parking_slip.png"
OCR_LANGUAGES = ['en']

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- load_yolo_model, load_easyocr_reader, detect_and_ocr functions remain the same ---
# ... (Paste the previous working versions of these functions here) ...
@st.cache_resource
def load_yolo_model(model_path):
    # ... (same as before) ...
    if not os.path.exists(model_path):
        st.error(f"💥 **Error:** YOLO model file not found at `{model_path}`.")
        logger.error(f"YOLO model file not found at {model_path}")
        return None
    try:
        model = YOLO(model_path)
        logger.info(f"YOLO model loaded successfully from {model_path}")
        return model
    except Exception as e:
        st.error(f"💥 **Error:** Failed to load YOLO model. Details: {e}")
        logger.error(f"Failed to load YOLO model from {model_path}: {e}")
        return None

@st.cache_resource
def load_easyocr_reader(languages=['en'], gpu=True):
     # ... (same as before) ...
    try:
        reader = easyocr.Reader(languages, gpu=gpu)
        logger.info(f"EasyOCR reader loaded successfully for languages: {languages}. GPU={'Enabled' if gpu else 'Disabled'}")
        if gpu and reader.device != 'cuda':
             logger.warning("GPU was requested for EasyOCR, but it seems to be running on CPU.")
             st.info("ℹ️ EasyOCR is running on CPU. For faster processing, ensure PyTorch with CUDA support is installed and a GPU is available.")
        elif not gpu and reader.device == 'cuda':
             logger.info("EasyOCR is running on GPU even though GPU was set to False.")
        return reader
    except ModuleNotFoundError as e:
        st.error(f"💥 **Error:** EasyOCR or its dependencies (like PyTorch) not found. Please install them. Details: {e}")
        logger.error(f"Failed to load EasyOCR reader: {e}")
        st.error("Please install PyTorch and EasyOCR: `pip install easyocr torch torchvision torchaudio` (adjust PyTorch command based on your system/CUDA).")
        return None
    except Exception as e:
        st.error(f"💥 **Error:** Failed to initialize EasyOCR reader. Check internet connection or installation. Details: {e}")
        logger.error(f"Failed to initialize EasyOCR reader: {e}", exc_info=True)
        return None

def detect_and_ocr(image_np, yolo_model, easyocr_reader):
    # ... (same as before - using EasyOCR) ...
    plate_text = ""
    cropped_plate_img = None
    box = None
    processed_for_ocr_img = None # Keep consistent return structure

    if easyocr_reader is None:
        return None, "OCR Error (Reader not loaded)", None, None

    try:
        # Detect with YOLO
        results = yolo_model(image_np, save=False, verbose=False)
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)

        if len(boxes) == 0:
            logger.warning("No number plate detected in the image.")
            return None, "No plate detected", None, None

        x1, y1, x2, y2 = boxes[0]
        box = (x1, y1, x2, y2)
        padding = 2
        y1_pad = max(0, y1 - padding)
        y2_pad = min(image_np.shape[0], y2 + padding)
        x1_pad = max(0, x1 - padding)
        x2_pad = min(image_np.shape[1], x2 + padding)
        cropped_plate_img = image_np[y1_pad:y2_pad, x1_pad:x2_pad]
        processed_for_ocr_img = cropped_plate_img

        if cropped_plate_img.size == 0:
             logger.warning("Cropped image is empty. Skipping OCR.")
             return box, "Crop Error", cropped_plate_img, processed_for_ocr_img

        logger.info(f"Running EasyOCR on cropped plate...")
        ocr_results = easyocr_reader.readtext(
            processed_for_ocr_img, detail=1, paragraph=False
            )
        logger.info(f"EasyOCR Raw Results: {ocr_results}")

        if not ocr_results:
            plate_text = "OCR failed (EasyOCR found no text)"
            logger.warning("EasyOCR processing resulted in empty results.")
        else:
            filtered_texts = []
            confidence_threshold = 0.2
            for (bbox, text, prob) in ocr_results:
                 logger.info(f"Detected text: '{text}' with confidence {prob:.4f}")
                 if prob >= confidence_threshold:
                     cleaned_text = ''.join(filter(str.isalnum, text)).upper()
                     if cleaned_text:
                         filtered_texts.append(cleaned_text)
                 else:
                     logger.info(f"Ignoring text '{text}' due to low confidence ({prob:.4f})")

            if filtered_texts:
                plate_text = ' '.join(filtered_texts)
                logger.info(f"Combined & Filtered OCR Result: '{plate_text}'")
            else:
                plate_text = "OCR failed (Low confidence or non-alphanumeric)"
                logger.warning("EasyOCR text filtered to empty or had low confidence.")

    except Exception as e:
        st.error(f"⚠️ An error occurred during detection or EasyOCR processing: {e}")
        logger.error(f"Error in detect_and_ocr: {e}", exc_info=True)
        plate_text = "Processing Error"
        return box, plate_text, cropped_plate_img, processed_for_ocr_img

    return box, plate_text, cropped_plate_img, processed_for_ocr_img


# --- Slip Generation --- ENHANCED & MODIFIED ---
def create_parking_slip(plate_text, entry_time_obj, filename=SLIP_FILENAME):
    """Generates an enhanced, modern parking slip image."""
    # --- Style Configuration ---
    slip_width, slip_height = 600, 400 # Adjusted size
    bg_color = "#F8F9FA" # Very light gray background
    primary_color = "#2C3E50" # Dark Slate Blue
    secondary_color = "#7F8C8D" # Grayish Cyan
    accent_color = "#BDC3C7" # Silver Gray for borders/dividers
    border_margin = 20
    content_padding_x = 35
    value_start_x = 280 # X position where values start (for alignment)
    border_radius = 10 # For rounded corners
    icon_color = primary_color

    slip = Image.new("RGB", (slip_width, slip_height), bg_color)
    draw = ImageDraw.Draw(slip)

    # --- Load Fonts ---
    font_title, font_text, font_small, font_icon, font_value_bold = None, None, None, None, None
    fonts_ok = True
    try:
        if os.path.exists(FONT_REGULAR_PATH) and os.path.exists(FONT_BOLD_PATH):
            font_title = ImageFont.truetype(FONT_BOLD_PATH, 34)
            font_text = ImageFont.truetype(FONT_REGULAR_PATH, 18) # Regular text size
            font_value_bold = ImageFont.truetype(FONT_BOLD_PATH, 20) # Bold for important values
            font_small = ImageFont.truetype(FONT_REGULAR_PATH, 13)
            font_icon = ImageFont.truetype(FONT_REGULAR_PATH, 20) # Icon size
            logger.info("Loaded Poppins fonts.")
        else:
            raise IOError("Poppins font files not found.")
    except Exception as e:
        logger.warning(f"Poppins fonts not loaded ({e}). Trying Arial fallback.")
        fonts_ok = False
        try:
            font_title = ImageFont.truetype("arialbd.ttf", 32)
            font_text = ImageFont.truetype("arial.ttf", 17)
            font_value_bold = ImageFont.truetype("arialbd.ttf", 19)
            font_small = ImageFont.truetype("arial.ttf", 13)
            font_icon = ImageFont.truetype("arial.ttf", 19)
        except IOError:
            logger.error("Arial fallback fonts not found. Using PIL default.")
            # PIL default doesn't have bold/regular variants easily, use default for all
            font_title = font_text = font_value_bold = font_small = font_icon = ImageFont.load_default()

    if not fonts_ok:
         st.info("ℹ️ Custom Poppins fonts not found or failed to load. Using default fonts. Appearance may vary.")

    # --- Draw Background & Border ---
    # Optional: Draw a subtle texture or pattern here if desired
    # Draw main rounded border
    draw.rounded_rectangle(
        (border_margin, border_margin, slip_width - border_margin, slip_height - border_margin),
        radius=border_radius,
        outline=accent_color,
        width=2 # Slightly thicker border
    )

    # --- Header ---
    y_pos = border_margin + 25
    header_text = "PARKING RECEIPT"
    header_bbox = draw.textbbox((0, 0), header_text, font=font_title)
    header_width = header_bbox[2] - header_bbox[0]
    draw.text(((slip_width - header_width) / 2, y_pos), header_text, font=font_title, fill=primary_color)
    y_pos += (header_bbox[3] - header_bbox[1]) + 15

    # --- Divider ---
    draw.line([(content_padding_x, y_pos), (slip_width - content_padding_x, y_pos)], fill=accent_color, width=1)
    y_pos += 25

    # --- Content Rows ---
    display_plate_text = plate_text if plate_text and "failed" not in plate_text.lower() and "error" not in plate_text.lower() else "N/A"
    content_items = [
        ("🚗", "Vehicle Plate", display_plate_text, font_value_bold), # Icon changed, label changed
        ("📅", "Entry Time", entry_time_obj.strftime("%d %b %Y, %H:%M:%S"), font_text), # Value font changed
        ("💰", "Parking Fee", "Rs. 30.00", font_text), # Value font changed
    ]
    row_height = 50 # Spacing between rows

    for icon, label, value, value_font in content_items:
        icon_y_adjust = 3 # Fine-tune vertical icon alignment
        label_y_adjust = 0
        value_y_adjust = 0

        # Draw Icon
        if font_icon:
            draw.text((content_padding_x, y_pos + icon_y_adjust), icon, font=font_icon, fill=icon_color)

        # Draw Label
        label_x = content_padding_x + 40 # Space after icon
        if font_text:
            draw.text((label_x, y_pos + label_y_adjust), label, font=font_text, fill=secondary_color)

        # Draw Value
        if value_font:
             # Ensure value doesn't overflow - truncate if necessary (optional)
            # max_value_width = slip_width - value_start_x - content_padding_x
            # value_bbox = draw.textbbox((0,0), value, font=value_font)
            # if value_bbox[2] > max_value_width:
            #     # Simple truncation logic (improve if needed)
            #     value = value[:int(len(value) * max_value_width / value_bbox[2]) - 3] + "..."
            draw.text((value_start_x, y_pos + value_y_adjust), value, font=value_font, fill=primary_color)

        y_pos += row_height

    # --- QR Code Placeholder Section ---
    y_pos += 5 # Space before QR section
    qr_section_y_start = y_pos
    qr_size = 80
    qr_margin = 15
    qr_x = slip_width - border_margin - content_padding_x - qr_size # Position on the right
    qr_y = qr_section_y_start

    # Draw QR Box
    draw.rectangle(
        (qr_x, qr_y, qr_x + qr_size, qr_y + qr_size),
        outline=accent_color,
        width=1
    )
    # Draw simple QR pattern inside (visual cue)
    draw.line([(qr_x+5, qr_y+5), (qr_x+qr_size-5, qr_y+qr_size-5)], fill=accent_color)
    draw.line([(qr_x+qr_size-5, qr_y+5), (qr_x+5, qr_y+qr_size-5)], fill=accent_color)
    draw.text((qr_x + 18, qr_y + 30), "SCAN", font=font_small, fill=secondary_color) # Text inside

    # Draw Text next to QR
    qr_text_x = content_padding_x
    qr_text_y = qr_y + 15
    qr_text = "Scan for details or payment."
    if font_text:
         draw.text((qr_text_x, qr_text_y), qr_text, font=font_text, fill=secondary_color)
         qr_text_y += 30
         # Add another line? e.g., Transaction ID
         # trans_id = "ID: XXXXXXXX"
         # draw.text((qr_text_x, qr_text_y), trans_id, font=font_small, fill=secondary_color)

    # --- Footer ---
    # Position footer based on the bottom edge
    footer_y = slip_height - border_margin - 25
    powered_by_text = "Powered by Downlabs"
    if font_small:
        pb_bbox = draw.textbbox((0,0), powered_by_text, font=font_small)
        pb_width = pb_bbox[2] - pb_bbox[0]
        draw.text(((slip_width - pb_width) / 2, footer_y), powered_by_text, font=font_small, fill=secondary_color)

    # --- Save the slip ---
    try:
        slip.save(filename)
        logger.info(f"Parking slip saved as {filename}")
        return filename
    except Exception as e:
        st.error(f"❌ Failed to save the parking slip image: {e}")
        logger.error(f"Failed to save parking slip image {filename}: {e}")
        return None


# --- Streamlit App ---
st.set_page_config(page_title="Smart Parking Slip", layout="wide", page_icon="🅿️")

# --- Header --- MODIFIED ---
st.title("🅿️ Enhanced Parking Slip Generator")
st.markdown("""
    Upload a vehicle image to detect the number plate (**YOLO**) and extract text (**EasyOCR**).
    A modern, enhanced parking slip will be generated.

    **Requires:** `fonts` folder with `Poppins-Regular.ttf` & `Poppins-Bold.ttf` for best results.
    *(Note: First run may take longer to download OCR models)*.
""") # Updated text
st.divider()

# --- Model Checks ---
# REMOVED Raqm Check
yolo_model = load_yolo_model(YOLO_MODEL_PATH)
easy_ocr_reader = load_easyocr_reader(languages=OCR_LANGUAGES, gpu=True)

# --- Main Area --- (Structure remains the same)
col1, col2 = st.columns(2, gap="large")

with col1:
    st.header("📤 Upload Image")
    uploaded_file = st.file_uploader(
        "Choose a vehicle image...",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Vehicle Image", use_column_width=True)

with col2:
    st.header(" R️esults & Slip")
    models_loaded = yolo_model is not None and easy_ocr_reader is not None

    if uploaded_file and models_loaded:
        # REMOVED Raqm warning
        with st.spinner("🔄 Processing Image... Detecting plate and performing EasyOCR..."):
            try:
                # ... (Image reading and OCR - same as before) ...
                file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                img_cv = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

                if img_cv is None:
                    st.error("❌ Failed to decode image. Please try another file.")
                else:
                    detection_box, plate_text_result, cropped_img, ocr_input_img = detect_and_ocr(
                        img_cv, yolo_model, easy_ocr_reader
                    )
                    current_time = datetime.now()

                    if detection_box:
                        # ... (Display detected box/crop - same as before) ...
                        x1, y1, x2, y2 = detection_box
                        img_with_box = img_cv.copy()
                        cv2.rectangle(img_with_box, (x1, y1), (x2, y2), (0, 255, 0), 3)
                        st.image(img_with_box, caption="Detected Number Plate Area", channels="BGR", use_column_width=True)
                        if cropped_img is not None:
                             st.image(cropped_img, caption=f"Cropped Plate Sent to EasyOCR", channels="BGR", use_column_width=True)

                        st.divider()
                        st.subheader(f"🆔 Extracted Plate Number:")
                        # ... (Display success/failure - same as before) ...
                        is_success = not any(err_msg in plate_text_result.lower() for err_msg in ["error", "failed", "no plate", "n/a", "crop"]) and bool(plate_text_result)

                        if is_success:
                             st.success(f"✅ **`{plate_text_result}`**")
                        else:
                            if plate_text_result == "OCR failed (EasyOCR found no text)":
                                 st.error("❌ OCR Failed: EasyOCR did not find any recognizable text.")
                            elif plate_text_result == "OCR failed (Low confidence or non-alphanumeric)":
                                 st.warning("⚠️ OCR Warning: Text found but had low confidence or contained only symbols after filtering.")
                            elif plate_text_result == "No plate detected":
                                 st.error("❌ Detection Failed: No number plate found by YOLO.")
                            else:
                                 st.warning(f"⚠️ Status: `{plate_text_result}`")

                        # --- Generate and Display Slip ---
                        if is_success:
                            # Call the ENHANCED slip function
                            slip_filepath = create_parking_slip(plate_text_result, current_time)

                            if slip_filepath and os.path.exists(slip_filepath):
                                st.divider()
                                st.subheader("🧾 Generated Parking Slip")
                                slip_image = Image.open(slip_filepath)
                                st.image(slip_image, caption="Parking Slip Preview", use_column_width=True)

                                # ... (Download button - same as before) ...
                                with open(slip_filepath, "rb") as fp:
                                    st.download_button(
                                        label="📥 Download Parking Slip",
                                        data=fp,
                                        file_name=f"Parking_Slip_{plate_text_result.replace(' ','_')}_{current_time.strftime('%Y%m%d_%H%M')}.png",
                                        mime="image/png"
                                    )
                            else:
                                st.error("❌ Failed to generate or save the parking slip.")
                        else:
                            st.info("ℹ️ Parking slip cannot be generated due to issues in plate detection or text extraction.")
                    else:
                         st.error("❌ **Detection Failed:** No number plate could be detected.")
            except Exception as e:
                st.error(f"🚫 An unexpected error occurred: {e}")
                logger.error(f"Unhandled exception: {e}", exc_info=True)

    elif not uploaded_file:
        st.info("☝️ Upload an image to begin.")
    elif not models_loaded:
         st.error("⚠️ Models failed to load. Cannot process.")

# --- Footer ---
st.divider()
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>App Developed by Downlabs | Powered by YOLO & EasyOCR</p>", unsafe_allow_html=True)