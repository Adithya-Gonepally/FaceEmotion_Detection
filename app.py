import streamlit as st
from PIL import Image
from ultralytics import YOLO
import tempfile
import os
import cv2
import base64

from auth.authenticator import (
    register_user, authenticate, get_users, approve_user, remove_user
)

# Load model once
@st.cache_resource
def load_model():
    return YOLO("Emotions.pt")

# Encode local image to base64
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    return f"data:image/jpg;base64,{encoded}"

# Set background and custom styles
def set_bg():
    image_data = get_base64_image("image.jpg")
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{image_data}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        .stForm {{
            background-color: rgba(0, 0, 0, 0.5);
            padding: 2rem 3rem;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            width: 100%;
            max-width: 450px;
            margin: 0 auto;
            margin-top: 1rem;
        }}

        .stTextInput input, .stPasswordInput input {{
            background-color: rgba(255, 255, 255, 0.15);
            color: white;
            border-radius: 10px;
            padding: 0.5rem;
            border: none;
        }}

        label, .stForm span {{
            color: white !important;
        }}

        .css-18e3th9 {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }}

        .stFileUploader {{
            width: 100%;
            max-width: 400px;
            padding: 1rem;
            border: 2px dashed #ffffff;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            color: #ffffff;
            font-size: 1rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .stFileUploader:hover {{
            background: rgba(255, 255, 255, 0.3);
            border-color: #ffffff;
        }}

        .file-uploader-wrapper {{
            display: flex;
            justify-content: center;
            width: 100%;
            margin-top: 2rem;
        }}

        @media screen and (max-width: 768px) {{
            .stForm {{
                max-width: 100%;
                padding: 1rem;
            }}
            .stFileUploader {{
                font-size: 0.9rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Emotion detection from image
def detect_emotion():
    st.subheader("Upload Image for Emotion Detection")

    st.markdown('<div class="file-uploader-wrapper">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            image.save(temp_file.name)
            temp_path = temp_file.name
        model = load_model()
        results = model(temp_path)
        result_image_bgr = results[0].plot()
        result_image_rgb = cv2.cvtColor(result_image_bgr, cv2.COLOR_BGR2RGB)
        st.image(result_image_rgb, caption="Detection Results", use_container_width=True)
        os.remove(temp_path)

# Registration UI
def register():
    st.markdown("""
        <div style='text-align: center; margin-top: 2rem;'>
            <h1 style='color: white; font-size: 3rem; margin-bottom: 0.5rem;'>Face Emotion Detection App</h1>
            <h3 style='color: #ffffffcc; margin-bottom: 1.5rem;'>Register</h3>
        </div>
    """, unsafe_allow_html=True)

    with st.form("register_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Register")
        if submit:
            if username and password:
                success, msg = register_user(username, password)
                if success:
                    st.success(msg)
                else:
                    st.warning(msg)
            else:
                st.error("Both fields are required.")

# Login UI
def login():
    st.markdown("""
        <div style='text-align: center; margin-top: 2rem;'>
            <h1 style='color: white; font-size: 3rem; margin-bottom: 0.5rem;'>Face Emotion Detection App</h1>
            <h3 style='color: #ffffffcc; margin-bottom: 1.5rem;'>Login</h3>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        valid, info = authenticate(username, password)
        if valid:
            if info["approved"]:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = info["role"]
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.warning("Awaiting admin approval.")
        else:
            st.error("Invalid credentials.")

# Admin panel
def admin_panel():
    st.subheader("👑 Admin Panel – User Management")

    users_df = get_users(include_all=True)

    if users_df.empty:
        st.info("No users found in the system.")
        return

    users_df["Status"] = users_df["approved"].apply(lambda x: "✅ Approved" if x else "⏳ Pending")
    users_df_display = users_df[["username", "role", "Status"]]

    st.markdown("### 👥 All Registered Users")
    st.dataframe(users_df_display, use_container_width=True)

    # Pending approvals section
    pending_df = users_df[users_df["approved"] == False]

    if not pending_df.empty:
        st.markdown("### 🛠 Pending Approvals")
        for _, row in pending_df.iterrows():
            username = row["username"]
            col1, col2 = st.columns(2)
            if col1.button(f"Approve {username}", key=f"approve_{username}"):
                approve_user(username)
                st.success(f"{username} approved.")
                st.rerun()
            if col2.button(f"Remove {username}", key=f"remove_{username}"):
                remove_user(username)
                st.warning(f"{username} removed.")
                st.rerun()
    else:
        st.success("✅ No users pending approval.")

# Main UI
def main():
    set_bg()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        menu = ["Login", "Register"]
        choice = st.sidebar.selectbox("Menu", menu)
        if choice == "Login":
            login()
        else:
            register()
    else:
        st.sidebar.write(f"Logged in as: **{st.session_state.username}** ({st.session_state.role})")
        if st.sidebar.button("Logout"):
            st.session_state.clear()
            st.rerun()

        if st.session_state.role == "admin":
            admin_panel()
        else:
            detect_emotion()

if __name__ == "__main__":
    main()
