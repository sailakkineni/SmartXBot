import pathlib

APP = pathlib.Path(__file__).resolve().parents[1] / "frontend" / "app.py"
text = APP.read_text(encoding="utf-8")

def test_streamlit_file_uploads_update_session_state_without_stale_callbacks():
    """Regression test: file upload widgets should parse the selected file in the main render path instead of relying on stale callback-only state writes."""
    assert "on_change=handle_jd_upload" not in text
    assert "on_change=handle_res_upload" not in text
    assert "if uploaded_jd and not st.session_state.jd_text:" not in text
    assert "if uploaded_res and not st.session_state.resume_text:" not in text
