# app.py
# Streamlit app to upload a PDF, pick pages by spec (e.g., "1,3-5,10") or range,
# then download a new PDF with only those pages.

import io
from typing import List
import streamlit as st
from pypdf import PdfReader, PdfWriter

# ---------- Helpers ----------
def parse_page_spec(spec: str) -> List[int]:
    """
    Parse a page spec like '1,3-5,10' into a list of 1-based page numbers.
    Supports ascending and descending ranges: '7-4' -> 7,6,5,4.
    Keeps order and duplicates as typed by the user.
    """
    if not spec:
        return []
    pages: List[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = int(start_s)
            end = int(end_s)
            step = 1 if start <= end else -1
            pages.extend(list(range(start, end + step, step)))
        else:
            pages.append(int(part))
    return pages

def extract_pages_from_pdf(pdf_bytes: bytes, pages_1based: List[int]) -> bytes:
    """
    Given a PDF (bytes) and a 1-based list of page indices, return a new PDF (bytes)
    that contains those pages in the specified order.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))

    # Try decrypting with empty password if encrypted
    if reader.is_encrypted:
        try:
            reader.decrypt("")  # empty password
        except Exception as e:
            raise RuntimeError(
                f"PDF is encrypted and cannot be opened without a password: {e}"
            )

    total_pages = len(reader.pages)

    # Validate page numbers are in range
    for p in pages_1based:
        if p < 1 or p > total_pages:
            raise ValueError(f"Page {p} is out of range (1..{total_pages}).")

    writer = PdfWriter()
    for p in pages_1based:
        writer.add_page(reader.pages[p - 1])  # convert 1-based -> 0-based

    # Optional metadata
    writer.add_metadata({
        "/Title": "Extracted Pages",
        "/Producer": "pypdf",
    })

    out_buf = io.BytesIO()
    writer.write(out_buf)
    out_buf.seek(0)
    return out_buf.read()

# ---------- UI ----------
st.set_page_config(page_title="PDF Page splitter", page_icon="📄", layout="centered")
st.title("📄 PDF Page Picker")
st.caption("Upload a PDF, choose pages (by spec or range), and download a new PDF.")

uploaded = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded is not None:
    # Read file into memory
    pdf_bytes = uploaded.read()

    # Peek total pages for validation hints
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        st.info(f"Total pages detected: **{total_pages}**")
    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
        st.stop()

    mode = st.radio(
        "Selection mode",
        options=["By page spec (e.g., 1,3-5,10)", "By start-end range"],
        horizontal=False,
    )

    selected_pages: List[int] = []

    if mode == "By page spec (e.g., 1,3-5,10)":
        spec = st.text_input(
            "Pages (1-based). Example: 1,3-5,10 or descending like 7-4",
            placeholder="1,3-5,10"
        )
        if spec:
            try:
                selected_pages = parse_page_spec(spec)
            except Exception as e:
                st.error(f"Invalid spec: {e}")

    else:
        col1, col2 = st.columns(2)
        with col1:
            start = st.number_input("Start page (1-based)", min_value=1, step=1, value=1)
        with col2:
            end = st.number_input("End page (1-based)", min_value=1, step=1, value=1)

        # Build list from start..end (supports descending ranges)
        if start <= end:
            selected_pages = list(range(int(start), int(end) + 1))
        else:
            selected_pages = list(range(int(start), int(end) - 1, -1))

    if selected_pages:
        st.write("Selected pages (in order):", selected_pages)

        # Extra validation & hints
        bad = [p for p in selected_pages if p < 1 or p > total_pages]
        if bad:
            st.error(f"Out-of-range pages: {bad} (valid range is 1..{total_pages})")
        else:
            # Generate on demand
            if st.button("✂️ Extract and build PDF"):
                try:
                    out_bytes = extract_pages_from_pdf(pdf_bytes, selected_pages)
                    st.success(f"Built PDF with {len(selected_pages)} page(s).")
                    st.download_button(
                        label="⬇️ Download result",
                        data=out_bytes,
                        file_name="extracted_pages.pdf",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.error(f"Failed to build PDF: {e}")
    else:
        st.warning("Pick some pages first.")
else:
    st.info("Please upload a PDF to get started.")
