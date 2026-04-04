import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from config import config_by_name
from app.council.engine import CouncilEngine

# Mocking the User and DB if necessary, or just using deliberate directly
def run_experiments():
    # Setup flask app context
    app = Flask(__name__)
    # We load test config or dev config
    # We will just manually set config
    app.config['MLFLOW_TRACKING_URI'] = 'file:./mlruns'
    app.config['MLFLOW_EXPERIMENT_NAME'] = 'Protofolio_Bulk_Experiments'
    
    # We use a mocked API key or real one depending on env
    
    with app.app_context():
        engine = CouncilEngine()
        
        test_cases = [
            {"user_id": 1, "goal": "I want a Frontend architecture portfolio focusing on React and animations."},
            {"user_id": 2, "goal": "Backend developer portfolio highlighting FastAPI, Postgres and highly scalable systems."},
            {"user_id": 3, "goal": "Full-stack developer portfolio with Next.js, Prisma, and Tailwind CSS."},
            {"user_id": 4, "goal": "Data Science portfolio showcasing Machine Learning, Pandas, and Data Visualization."},
            {"user_id": 5, "goal": "DevOps engineer portfolio demonstrating Kubernetes, Docker, CI/CD pipelines, and AWS Terraform configuration."},
            {"user_id": 6, "goal": "Mobile app developer portfolio highlighting Flutter cross-platform architecture and UI/UX polish."},
            {"user_id": 7, "goal": "Cybersecurity analyst portfolio with pentesting reports, network security architectures, and ISO 27001 compliance standards."},
            {"user_id": 8, "goal": "Game developer portfolio showcasing Unity C#, 3D rendering pipelines, and multiplayer networking."},
            {"user_id": 9, "goal": "Simple generic junior developer portfolio just listing basic HTML, CSS, and some JavaScript projects."},
            {"user_id": 10, "goal": "Senior backend Staff Engineer portfolio emphasizing system design, leading 20+ engineering teams, and microservices decoupling."},
            {"user_id": 11, "goal": "AI/ML researcher portfolio with academic paper citations, PyTorch custom transformer models, and deep learning algorithms."},
            {"user_id": 12, "goal": "Web3/Blockchain developer portfolio showing Solidity smart contracts, DeFi protocols, and decentralized applications (dApps)."},
            {"user_id": 13, "goal": "UI/UX Designer portfolio heavily emphasizing user research, wireframing in Figma, and high-fidelity interactive prototypes."},
            {"user_id": 14, "goal": "Cloud Architect portfolio focusing on GCP, multi-region database replication, and serverless compute strategies."},
            {"user_id": 15, "goal": "Embedded systems engineer portfolio dealing with C/C++, IoT devices, RTOS, and hardware-software interfacing."},
            {"user_id": 16, "goal": "E-commerce platform engineer portfolio focusing on Stripe integration, high-load payment processing, and scalable inventory caching."}
        ]
        
        import random
        for case in test_cases:
            # Seed some varied memory to change resume_complexity_chars
            complexity = random.choice(["junior", "senior", "expert", "specialist"])
            mock_resume = f"User {case['user_id']} is a {complexity} {case['goal']}. "
            mock_resume += "Experienced in " + ", ".join(random.sample(["Docker", "AWS", "Python", "React", "SQL", "CI/CD"], k=random.randint(2, 5)))
            engine.memory.add_fact(case['user_id'], mock_resume)

        for case in test_cases:
            print(f"Running experiment for goal: {case['goal']}")
            result = engine.deliberate(user_id=case['user_id'], user_input=case['goal'])
            
            blueprint = result.get('blueprint', {})
            score = engine._calculate_quality_score(blueprint)
            
            print(f"-> Generated blueprint with score: {score}")

if __name__ == "__main__":
    run_experiments()
