from hashlib import sha256
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZIP_STORED, ZipFile

import streamlit as st
from PIL import Image

from tool_ui import support_footer, tool_header

MAX_FILES = 20
MAX_PIXELS = 12_000_000
MAX_BATCH_OUTPUT_BYTES = 80 * 1024 * 1024


def png_name(original, used_names):
    stem = PurePosixPath(original.replace("\\", "/")).stem or "image"
    name = f"{stem}.png"
    suffix = 2
    while name.casefold() in used_names:
        name = f"{stem} ({suffix}).png"
        suffix += 1
    used_names.add(name.casefold())
    return name


def convert_image(upload):
    with Image.open(BytesIO(upload.getvalue()), formats=["WEBP"]) as image:
        width, height = image.size
        if width * height > MAX_PIXELS:
            raise ValueError("Image exceeds 12 megapixels.")
        animated = getattr(image, "is_animated", False)
        with image.convert("RGBA" if "A" in image.getbands() else "RGB") as frame:
            output = BytesIO()
            frame.save(output, format="PNG")
        return output.getvalue(), (width, height), animated


def convert_batch(uploads):
    converted, errors = [], []
    used_names = set()
    bytes_used = 0
    for upload in uploads:
        try:
            data, dimensions, animated = convert_image(upload)
        except ValueError as error:
            errors.append(f"{upload.name} · {error}")
            continue
        except (OSError, Image.DecompressionBombError):
            errors.append(f"{upload.name} · Could not read this WebP image.")
            continue
        if bytes_used + len(data) > MAX_BATCH_OUTPUT_BYTES:
            errors.append(f"{upload.name} · Output exceeds the batch limit. Try a smaller batch.")
            continue
        bytes_used += len(data)
        converted.append((png_name(upload.name, used_names), data, dimensions, animated))
    return converted, errors


def build_zip(converted):
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        for name, data, _, _ in converted:
            archive.writestr(name, data)
    return output.getvalue()


st.set_page_config(page_title="WebP to PNG Converter", page_icon="🖼️")
tool_header(
    "WebP to PNG",
    "Convert a batch of WebP images to PNG and keep transparent backgrounds.",
    "حوّل عدة صور من WebP إلى PNG مع الحفاظ على الشفافية. نزّل الصور منفردة أو في ملف ZIP واحد.",
)

with st.container(border=True):
    uploads = st.file_uploader("WebP images", type=["webp"], accept_multiple_files=True)
    st.caption("Up to 20 images, 15 MB and 12 megapixels each. Animated WebP exports its first frame.")
    if len(uploads) > MAX_FILES:
        st.error(f"Select up to {MAX_FILES} images per batch.")
    convert = st.button(
        "Convert to PNG", type="primary", disabled=not 0 < len(uploads) <= MAX_FILES
    )
st.caption("The app processes uploads in server memory.")

signature = tuple(
    (upload.name, getattr(upload, "file_id", None) or sha256(upload.getbuffer()).digest())
    for upload in uploads
) if len(uploads) <= MAX_FILES else None
if st.session_state.get("conversion_batch") != signature:
    st.session_state.conversion_batch = signature
    st.session_state.pop("conversion_result", None)
    st.session_state.pop("conversion_zip", None)

if convert:
    with st.spinner("Converting images…"):
        result = convert_batch(uploads)
        st.session_state.conversion_result = result
        st.session_state.conversion_zip = build_zip(result[0]) if len(result[0]) > 1 else None

if st.session_state.get("conversion_result"):
    converted, errors = st.session_state.conversion_result
    for error in errors:
        st.warning(error)
    if converted:
        st.subheader(f"Downloads · {len(converted)} ready", anchor=False)
        if st.session_state.conversion_zip:
            st.download_button(
                "Download all as ZIP", st.session_state.conversion_zip,
                "converted-images.zip", "application/zip", type="primary", on_click="ignore",
            )
        for index, (name, data, (width, height), animated) in enumerate(converted):
            with st.container(border=True):
                st.text(name)
                detail = f"{width} × {height} px · {len(data) / 1024:,.0f} KB"
                st.caption(f"{detail} · First frame" if animated else detail)
                st.download_button(
                    "Download PNG", data, name, "image/png",
                    key=f"png_{index}", on_click="ignore",
                )
                if len(converted) <= 5:
                    with st.expander("Image preview"):
                        st.image(data, width=320)

support_footer()
