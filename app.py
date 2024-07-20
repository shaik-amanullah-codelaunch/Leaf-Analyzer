from dotenv import load_dotenv
load_dotenv()  # Load all the environment variables
import streamlit as st
import os
import google.generativeai as genai
from PIL import Image

# Configure the Google Gemini API
genai.configure(api_key=os.getenv("API_KEY"))

# Function to load Google Gemini Pro Vision API and get response
def get_gemini_response(input_image, prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([input_image[0], prompt])
        return response
    except Exception as e:
        st.error(f"Error in API call: {e}")
        return None

def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [
            {
                "mime_type": uploaded_file.type,
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Initialize Streamlit app
st.set_page_config(page_title="Leaf Analyzer")

st.header("Leaf Analyzer")

input_text = st.text_input("Input Prompt: ", key="input")

# Buttons for selecting upload method
use_file_uploader = st.button("Upload Image File")
use_camera = st.button("Take Image Using Camera")

# State management
if "upload_method" not in st.session_state:
    st.session_state.upload_method = None
if "show_camera" not in st.session_state:
    st.session_state.show_camera = False
if "captured_image" not in st.session_state:
    st.session_state.captured_image = None

# Update state based on button clicks
if use_file_uploader:
    st.session_state.upload_method = "file"
    st.session_state.show_camera = False
elif use_camera:
    st.session_state.upload_method = "camera"
    st.session_state.show_camera = True

# File uploader or camera input based on state
uploaded_file = None
if st.session_state.upload_method == "file":
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image.", use_column_width=True)
elif st.session_state.upload_method == "camera" and st.session_state.show_camera:
    camera_file = st.camera_input("Take a picture")
    if camera_file is not None:
        st.session_state.captured_image = camera_file
        st.session_state.show_camera = False  # Hide camera after taking a picture

# Display the captured image
if st.session_state.captured_image is not None:
    image = Image.open(st.session_state.captured_image)
    st.image(image, caption="Captured Image.", use_column_width=True)
    if st.button("Close Camera"):
        st.session_state.captured_image = None

# Center the "Analyze the Leaf" button using CSS
col1, col2, col3 = st.columns([12, 6, 10])
with col2:
    submit = st.button("Analyze the Leaf", key="analyze_button")

input_prompt = """
Please analyze this leaf image and act as an ayurvedic doctor. Provide the following details:

Morphological Features: Describe the shape, size, color, vein pattern, and margin characteristics of the leaf.
Chemical Composition: List any known active compounds such as alkaloids, flavonoids, tannins, and essential oils present in the leaf.
Medicinal Properties: Identify the therapeutic properties of the leaf, such as antibacterial, antifungal, anti-inflammatory, etc.
Diseases and Conditions: Specify the diseases and conditions that this leaf is traditionally or scientifically known to treat or alleviate.
Usage: Provide information on how the leaf is typically prepared and used for medicinal purposes (e.g., teas, poultices, extracts).
Use the latest botanical databases and research studies to ensure accurate and up-to-date information.

As you are an ayurvedic doctor, finally give a verdict on the input given by the user.
"""

# If submit button is clicked
if submit:
    # st.write("Submit button clicked")  # Debug statement
    try:
        if uploaded_file is not None:
            image_data = input_image_setup(uploaded_file)
        elif st.session_state.captured_image is not None:
            image_data = input_image_setup(st.session_state.captured_image)
        else:
            st.error("No image provided. Please upload an image or take a picture.")
            st.stop()

        response = get_gemini_response(image_data, input_prompt)
        if response is not None:
            st.subheader("The Response is")
            response_text = response.text

            # Debug response text
            # st.write("Debug Response Text:", response_text)

            categories = ["Morphological Features", "Chemical Composition", "Medicinal Properties", "Diseases and Conditions", "Usage", "Verdict"]
            response_dict = {}

            for category in categories:
                start_index = response_text.find(category)
                if start_index != -1:
                    next_start_index = len(response_text)
                    for next_category in categories:
                        next_start = response_text.find(next_category, start_index + len(category))
                        if next_start != -1 and next_start < next_start_index:
                            next_start_index = next_start
                    response_dict[category] = response_text[start_index + len(category) + 1:next_start_index].strip()
            
            with st.container():
                for category, details in response_dict.items():
                    with st.expander(category):
                        st.write(details)
        else:
            st.error("Failed to get a response from the API.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
