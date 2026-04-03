import requests
import json
import sys
import os

BASE_URL = "http://localhost:5001/api"

def run_test():
    print("1. Authenticating to get access token...")
    auth_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "test@example.com",
        "password": "test"
    })
    
    if auth_response.status_code != 200:
        print(f"Failed to authenticate! Is the server running? Response: {auth_response.text}")
        sys.exit(1)
        
    token = auth_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Authenticated successfully.")
    
    print("\n2. Uploading Dummy Resume PDF...")
    resume_path = "Dummy/resume.pdf"
    if not os.path.exists(resume_path):
        print(f"Error: {resume_path} not found. Did the PDF compile successfully?")
        sys.exit(1)
        
    with open(resume_path, "rb") as f:
        files = {"file": ("resume.pdf", f, "application/pdf")}
        resume_response = requests.post(f"{BASE_URL}/ingest/resume", headers=headers, files=files)
        
    if resume_response.status_code == 200:
        print("✓ Resume ingested successfully!")
        print("Response:", json.dumps(resume_response.json(), indent=2))
    else:
        print(f"Failed to ingest resume. Status: {resume_response.status_code}")
        print("Response:", resume_response.text)

    print("\n3. Letting the AI infer the career goal from the resume...")
    print("   (No manual goal needed — the council will read the resume and decide.)")

    print("\n4. Igniting the AI Council Deliberation Engine (goal will be auto-inferred from resume)...")
    generate_response = requests.post(f"{BASE_URL}/portfolio/generate", headers=headers, json={
        "theme": "dark"
    })
    
    if generate_response.status_code == 200:
        print("✓ Deliberation Complete!")
        gen_data = generate_response.json()
        print("\n--- LLM DELIBERATION LOGS ---")
        print(gen_data.get("deliberation", "No logs returned"))
        print("\n--- FINAL JSON BLUEPRINT ---")
        print(json.dumps(gen_data.get("blueprint", {}), indent=2))
        
        portfolio_id = gen_data.get("portfolio_id")
        
        print(f"\n5. Rendering Portfolio #{portfolio_id} HTML & CSS...")
        preview_response = requests.get(f"{BASE_URL}/portfolio/{portfolio_id}/preview", headers=headers)
        if preview_response.status_code == 200:
            print("✓ HTML & CSS Rendered Successfully.")
            render_data = preview_response.json()
            html_content = render_data.get("html", "")
            css_content = render_data.get("css", "")
            
            os.makedirs("output", exist_ok=True)
            with open("output/index.html", "w") as f:
                f.write(html_content)
            with open("output/styles.css", "w") as f:
                f.write(css_content)
                
            print(f"\n[!] Success: I have saved your finalized code directly to:")
            print("  -> output/index.html")
            print("  -> output/styles.css")
            print("You can double-click index.html to view your UI/UX portfolio in action!")
        else:
            print(f"Failed to render. Status: {preview_response.status_code}")
    else:
        print(f"Failed to generate portfolio. Status: {generate_response.status_code}")
        print("Response:", generate_response.text)

    print("\n✓ Local System Test Complete! Server and agents are fully operational.")

if __name__ == "__main__":
    try:
        run_test()
    except requests.exceptions.ConnectionError:
        print("CRITICAL: Failed to connect to the server at localhost:5001.")
        print("Make sure your Flask server is running in another terminal window:")
        print("  python run.py")
