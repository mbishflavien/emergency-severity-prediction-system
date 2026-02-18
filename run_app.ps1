# Run the Streamlit Application
$env:PYTHONPATH = "$PSScriptRoot"
& "$PSScriptRoot\.venv\Scripts\python.exe" -m streamlit run "$PSScriptRoot\app.py"
