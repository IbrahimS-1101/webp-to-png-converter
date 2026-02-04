import streamlit as st
from PIL import Image
import io
import zipfile

st.set_page_config(
    page_title="WebP to PNG Converter",
    page_icon="🖼️",
    layout="centered"
)

st.title("🖼️ WebP to PNG Converter")
st.markdown("Convert your WebP images to PNG format - free and private!")

st.info("ℹ️ Your images are processed in memory and never stored on our servers.")

# Initialize session state for converted images
if 'converted_images' not in st.session_state:
    st.session_state.converted_images = []

# File uploader
uploaded_files = st.file_uploader(
    "Choose WebP image(s)",
    type=['webp'],
    accept_multiple_files=True,
    help="You can select multiple WebP files at once"
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")
    
    # Add a convert button
    if st.button("Convert to PNG", type="primary"):
        st.session_state.converted_images = []  # Clear previous conversions
        
        with st.spinner("Converting images..."):
            for uploaded_file in uploaded_files:
                try:
                    # Open the WebP image
                    image = Image.open(uploaded_file)
                    
                    # Convert to PNG in memory
                    png_buffer = io.BytesIO()
                    
                    # Handle transparency if present
                    if image.mode in ('RGBA', 'LA', 'P'):
                        image.save(png_buffer, format='PNG')
                    else:
                        # Convert to RGB if no transparency
                        rgb_image = image.convert('RGB')
                        rgb_image.save(png_buffer, format='PNG')
                    
                    png_buffer.seek(0)
                    
                    # Generate output filename
                    output_filename = uploaded_file.name.rsplit('.', 1)[0] + '.png'
                    
                    # Store converted image in session state
                    st.session_state.converted_images.append({
                        'filename': output_filename,
                        'data': png_buffer.getvalue()
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error converting {uploaded_file.name}: {str(e)}")
    
    # Display converted images with download buttons
    if st.session_state.converted_images:
        st.markdown("---")
        st.subheader("Converted Images")
        
        # Batch download button (if more than one file)
        if len(st.session_state.converted_images) > 1:
            # Create zip file in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for img in st.session_state.converted_images:
                    zip_file.writestr(img['filename'], img['data'])
            
            zip_buffer.seek(0)
            
            st.download_button(
                label=f"📦 Download All ({len(st.session_state.converted_images)} files as ZIP)",
                data=zip_buffer,
                file_name="converted_images.zip",
                mime="application/zip",
                type="primary"
            )
            st.markdown("---")
        
        # Individual download buttons
        for idx, img in enumerate(st.session_state.converted_images):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📄 {img['filename']}")
            with col2:
                st.download_button(
                    label="Download",
                    data=img['data'],
                    file_name=img['filename'],
                    mime="image/png",
                    key=f"download_{idx}"
                )
    
    # Show preview section
    if uploaded_files and len(uploaded_files) <= 5:  # Only show previews for small batches
        st.markdown("---")
        st.subheader("Preview")
        for uploaded_file in uploaded_files:
            try:
                image = Image.open(uploaded_file)
                st.image(image, caption=uploaded_file.name, use_container_width=True)
            except:
                pass

else:
    st.markdown("""
    ### How to use:
    1. Click the upload button above
    2. Select one or more WebP images
    3. Click "Convert to PNG"
    4. Download your converted files
    
    ### Features:
    - ✨ Convert multiple files at once
    - 🔒 Complete privacy - no server storage
    - 🎨 Preserves transparency
    - 💯 100% free to use
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
    Made with a lot of ☕ by Ibrahim Samir
    </div>
    """,
    unsafe_allow_html=True
)