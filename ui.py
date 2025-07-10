import streamlit as st
import requests
import time
import json
from datetime import datetime
import pandas as pd

# Configure Streamlit page
st.set_page_config(
    page_title="PDF Processing - GitHub Org Extractor",
    page_icon="📄",
    layout="wide"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

def upload_pdf(file):
    """Upload PDF to the API and return job ID."""
    files = {"file": ("document.pdf", file, "application/pdf")}
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/documents/upload", files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Upload failed: {str(e)}")
        return None

def get_job_status(job_id):
    """Get job status from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/jobs/{job_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to get job status: {str(e)}")
        return None

def get_queue_status():
    """Get queue status from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/queue/status")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to get queue status: {str(e)}")
        return None

def format_timestamp(timestamp_str):
    """Format timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

def display_job_card(job_data):
    """Display job information in a card format."""
    status = job_data.get("status", "unknown")
    
    # Status color mapping
    status_colors = {
        "queued": "🔵",
        "processing": "🟡", 
        "completed": "🟢",
        "failed": "🔴"
    }
    
    status_icon = status_colors.get(status, "⚪")
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"{status_icon} {job_data['original_filename']}")
            st.write(f"**Job ID:** `{job_data['job_id']}`")
            st.write(f"**Status:** {status.title()}")
            st.write(f"**Uploaded:** {format_timestamp(job_data['timestamp'])}")
            
            if job_data.get("message"):
                st.info(job_data["message"])
            
            if status == "completed":
                if job_data.get("extracted_company_username"):
                    st.success(f"**GitHub Org Found:** {job_data['extracted_company_username']}")
                    
                    if job_data.get("github_members"):
                        members = job_data["github_members"]
                        st.write(f"**Members Found:** {len(members)}")
                        
                        # Display members in expandable section
                        with st.expander("View Organization Members"):
                            if len(members) > 0:
                                # Create DataFrame for better display
                                df = pd.DataFrame({"GitHub Username": members})
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.write("No public members found")
                    else:
                        st.write("**Members:** No members found")
                else:
                    st.warning("No GitHub organization found in the PDF")
        
        with col2:
            if status in ["queued", "processing"]:
                st.button("🔄 Refresh", key=f"refresh_{job_data['job_id']}")

def main():
    # Header
    st.title("📄 PDF GitHub Organization Extractor")
    st.markdown("Upload PDF documents to extract GitHub organization information using AI")
    
    # Sidebar for queue status
    with st.sidebar:
        st.header("🔧 System Status")
        
        if st.button("🔄 Refresh Status"):
            st.rerun()
        
        queue_status = get_queue_status()
        if queue_status:
            st.metric("Queue Size", queue_status.get("queue_size", 0))
            st.metric("Worker Status", "🟢 Running" if queue_status.get("worker_running") else "🔴 Stopped")
            
            # Job statistics
            if queue_status.get("job_statistics"):
                st.subheader("📊 Job Statistics")
                stats = queue_status["job_statistics"]
                
                for status, count in stats.items():
                    icon = {"queued": "🔵", "processing": "🟡", "completed": "🟢", "failed": "🔴"}.get(status, "⚪")
                    st.metric(f"{icon} {status.title()}", count)
    
    # Main content area
    tab1, tab2 = st.tabs(["📤 Upload PDF", "📋 Job History"])
    
    with tab1:
        st.header("Upload PDF Document")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a PDF that mentions a GitHub organization"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.write(f"**File:** {uploaded_file.name}")
            st.write(f"**Size:** {uploaded_file.size} bytes")
            
            # Upload button
            if st.button("🚀 Process PDF", type="primary"):
                with st.spinner("Uploading PDF..."):
                    result = upload_pdf(uploaded_file)
                
                if result:
                    st.success("✅ PDF uploaded successfully!")
                    st.json(result)
                    
                    # Store job ID in session state for tracking
                    if "job_ids" not in st.session_state:
                        st.session_state.job_ids = []
                    
                    if result["job_id"] not in st.session_state.job_ids:
                        st.session_state.job_ids.append(result["job_id"])
                    
                    st.info("💡 Switch to the 'Job History' tab to monitor progress")
    
    with tab2:
        st.header("Job History & Status")
        
        # Input for manual job ID lookup
        with st.expander("🔍 Look up specific Job ID"):
            manual_job_id = st.text_input("Enter Job ID:")
            if st.button("Look Up Job") and manual_job_id:
                job_data = get_job_status(manual_job_id)
                if job_data:
                    display_job_card(job_data)
                else:
                    st.error("Job not found")
        
        # Display tracked jobs
        if "job_ids" in st.session_state and st.session_state.job_ids:
            st.subheader("Your Jobs")
            
            # Auto-refresh option
            auto_refresh = st.checkbox("🔄 Auto-refresh every 10 seconds")
            
            if auto_refresh:
                # Auto-refresh placeholder
                placeholder = st.empty()
                
                # Display jobs with auto-refresh
                for i, job_id in enumerate(reversed(st.session_state.job_ids)):
                    job_data = get_job_status(job_id)
                    if job_data:
                        with placeholder.container():
                            display_job_card(job_data)
                            if i < len(st.session_state.job_ids) - 1:
                                st.divider()
                
                # Auto-refresh
                time.sleep(10)
                st.rerun()
            else:
                # Display jobs without auto-refresh
                for i, job_id in enumerate(reversed(st.session_state.job_ids)):
                    job_data = get_job_status(job_id)
                    if job_data:
                        display_job_card(job_data)
                        if i < len(st.session_state.job_ids) - 1:
                            st.divider()
        else:
            st.info("No jobs found. Upload a PDF to get started!")
            
        # Clear history button
        if st.button("🗑️ Clear Job History"):
            st.session_state.job_ids = []
            st.success("Job history cleared!")
            st.rerun()

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            <p>PDF GitHub Organization Extractor | Built with FastAPI & Streamlit</p>
            <p>API Documentation: <a href='http://localhost:8000/docs' target='_blank'>http://localhost:8000/docs</a></p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    # Check if API is accessible
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code != 200:
            st.error(f"⚠️ Cannot connect to API at {API_BASE_URL}")
            st.info("Please make sure the FastAPI server is running: `uvicorn main:app --reload`")
    except requests.exceptions.RequestException:
        st.error(f"⚠️ Cannot connect to API at {API_BASE_URL}")
        st.info("Please make sure the FastAPI server is running: `uvicorn main:app --reload`")
    
    main() 