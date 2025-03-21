import streamlit as st
from streamlit_option_menu import option_menu
import pymongo
import pandas as pd
import base64
from datetime import datetime  # Import datetime for date comparison

# MongoDB connection
client = pymongo.MongoClient(st.secrets["database"]["clientlink"])
studentsDB = client["StudentsDB"]
studentsCollection = studentsDB["StudentsCollection"]
validationDB = client["validationDB"]
scheduledDB = client["ScheduledExams"]
halltickets = client['HallTicketsDB']

# Streamlit app layout
st.set_page_config(page_title="Hall Ticket Management", layout="wide")

# Sidebar for navigation
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",
        options=["Login", "See Schedule", "See Status", "Download Hall Ticket", "See Rooms"],
        icons=["house", "calendar", "info-circle", "download", "building"],
        menu_icon="cast",
        default_index=0,
    )

# Session state to store user information
if "roll_number" not in st.session_state:
    st.session_state.roll_number = None
if "batch" not in st.session_state:
    st.session_state.batch = None
if "branch" not in st.session_state:
    st.session_state.branch = None
if "semester" not in st.session_state:
    st.session_state.semester = None

# Login Page
if selected == "Login":
    st.title("Login")
    col1, col2 = st.columns([1, 2],border=True)

    with col1:
        roll_number = st.text_input("Enter Roll Number")
        if st.button("Login"):
            student = studentsCollection.find_one({"roll_number": roll_number}, {"_id": 0})
            if student:
                st.session_state.roll_number = student["roll_number"]
                st.session_state.batch = student["batch"]
                st.session_state.branch = student["branch"]
                st.session_state.semester = student["semester"]
                st.success("Login Successful!")
            else:
                st.error("Invalid Roll Number")

    with col2:
        if st.session_state.roll_number:
            student = studentsCollection.find_one({"roll_number": st.session_state.roll_number}, {"_id": 0})
            st.subheader("Student Information")
            st.write(f"**Roll Number:** {student['roll_number']}")
            st.write(f"**Full Name:** {student['fullname']}")
            st.write(f"**Batch:** {student['batch']}")
            st.write(f"**Branch:** {student['branch']}")
            st.write(f"**Semester:** {student['semester']}")
            st.write(f"**Email ID:** {student['email_id']}")
            st.write(f"**Phone Number:** {student['phone_number']}")

# See Schedule Page
elif selected == "See Schedule":
    st.title("See Schedule")
    col1, col2 = st.columns([1, 2],border=True)

    with col1:
        if st.session_state.roll_number:
            collections = validationDB.list_collection_names()
            filtered_collections = [
                col for col in collections
                if st.session_state.batch in col and st.session_state.branch in col and str(st.session_state.semester) in col
            ]
            selected_collection = st.selectbox("Select Collection", filtered_collections)
            if st.button("Fetch Schedule"):
                with col2:
                    documents = validationDB[selected_collection].find({"hall_ticket_number": st.session_state.roll_number})
                    schedule_data = []
                    for doc in documents:
                        schedule_data.append({
                            "Date": doc["date"],
                            "Time": doc["time"],
                            "Subject": doc["subject"],
                            "Subject Code": doc["subject_code"],
                            "Credits": doc["subject_credits"],
                            "Type": doc["subject_types"],
                            "Semester": doc["semester"],
                            "Branch": doc["branch"],
                            "Batch": doc["batch"]
                        })
                    if schedule_data:
                        df = pd.DataFrame(schedule_data)
                        st.dataframe(df)
                    else:
                        st.warning("No schedule found for this student.")
        else:
            st.warning("Please login first.")

# See Status Page
elif selected == "See Status":
    st.title("See Status")
    col1, col2 = st.columns([1, 2],border=True)

    with col1:
        if st.session_state.roll_number:
            collections = validationDB.list_collection_names()
            filtered_collections = [
                col for col in collections
                if st.session_state.batch in col and st.session_state.branch in col and str(st.session_state.semester) in col
            ]
            selected_collection = st.selectbox("Select Collection", filtered_collections)
            if st.button("Fetch Status"):
                with col2:
                    document = validationDB[selected_collection].find_one({"hall_ticket_number": st.session_state.roll_number})
                    if document:
                        status_data = {
                            "Face Recognition Status": document.get("studentFaceRecognitionStatus", "N/A"),
                            "QR Code Status": document.get("studentQRCodeStatus", "N/A"),
                            "Thumb Status": document.get("studentThumbStatus", "N/A"),
                            "Final Status": document.get("StudentsFinalStatus", "N/A"),
                            "Booklet Number": document.get("studentBooketNumber", "N/A")
                        }
                        df = pd.DataFrame([status_data])
                        st.dataframe(df)
                    else:
                        st.warning("No status found for this student.")
        else:
            st.warning("Please login first.")

# Download Hall Ticket Page
elif selected == "Download Hall Ticket":
    st.title("Download Hall Ticket")
    if st.session_state.roll_number:
        hall_ticket_collections = halltickets.list_collection_names()
        selected_collection = st.selectbox("Select Hall Ticket Collection", hall_ticket_collections)
        if st.button("Download"):
            hall_ticket = halltickets[selected_collection].find_one({"roll_number": st.session_state.roll_number}, {"hall_ticket": 1, "_id": 0})
            if hall_ticket:
                # Decode the base64-encoded PDF data
                pdf_binary = base64.b64decode(hall_ticket["hall_ticket"])
                # Provide a download button for the PDF
                st.download_button(
                    label="Download Hall Ticket",
                    data=pdf_binary,
                    file_name=f"{st.session_state.roll_number}_hall_ticket.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("No hall ticket found for this student.")
    else:
        st.warning("Please login first.")

# See Rooms Page
elif selected == "See Rooms":
    st.title("See Rooms")
    col1, col2 = st.columns([1, 2],border=True)

    with col1:
        if st.session_state.roll_number:
            collections = validationDB.list_collection_names()
            filtered_collections = [
                col for col in collections
                if st.session_state.batch in col and st.session_state.branch in col and str(st.session_state.semester) in col
            ]
            selected_collection = st.selectbox("Select Collection", filtered_collections)
            if st.button("Fetch Room Details"):
                with col2:
                    documents = validationDB[selected_collection].find({"hall_ticket_number": st.session_state.roll_number})
                    room_data = []
                    for doc in documents:
                        room_data.append({
                            "Date": doc["date"],
                            "Time": doc["time"],
                            "Subject": doc["subject"]
                        })
                    if room_data:
                        df = pd.DataFrame(room_data)
                        st.dataframe(df)

                        # Get the current date
                        current_date = datetime.now().date()

                        # Selectbox for subjects
                        subjects = df["Subject"].unique().tolist()
                        selected_subject = st.selectbox("Select Subject", subjects)

                        # Filter data for the selected subject
                        subject_data = df[df["Subject"] == selected_subject].iloc[0]
                        exam_date = datetime.strptime(subject_data["Date"], "%Y-%m-%d").date()

                        # Check if the exam date is in the past, present, or future
                        if exam_date < current_date:
                            st.warning(f"The exam for {selected_subject} was completed on {exam_date}.")
                        elif exam_date == current_date:
                            room_number = doc.get("room_number", "N/A")
                            if room_number != "N/A":
                                st.success(f"Your room number for {selected_subject} today is: **{room_number}**")
                            else:
                                st.warning("Room number not available for today.")
                        else:
                            st.info(f"You can view your room number for {selected_subject} on {exam_date}.")
                    else:
                        st.warning("No room details found for this student.")
        else:
            st.warning("Please login first.")
