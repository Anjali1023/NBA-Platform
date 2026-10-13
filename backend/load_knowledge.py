import chromadb
import uuid

client = chromadb.HttpClient(host="localhost", port=8000)
collection = client.get_or_create_collection("playbooks")

documents = [
    "High churn risk playbook: When a customer shows churn signals, immediately schedule an executive business review within 24 hours. Assign a dedicated CSM and create a success roadmap.",
    "Renewal playbook: 90 days before renewal, initiate executive engagement. Share ROI report and success metrics. Offer early renewal discount if needed.",
    "Onboarding playbook: Customers showing adoption gaps need a personalized onboarding plan. Schedule weekly check-ins for 30 days.",
    "Expansion playbook: When customer shows positive sentiment and high usage, introduce upsell opportunities like premium features or additional seats.",
    "Escalation playbook: If customer mentions support issues 3+ times, escalate to engineering team within 48 hours and provide weekly status updates.",
    "Executive outreach playbook: For accounts over 100k ARR showing risk signals, loop in VP of Customer Success for direct outreach.",
]

ids = [str(uuid.uuid4()) for _ in documents]
collection.add(documents=documents, ids=ids)
print(f"Loaded {len(documents)} playbooks into ChromaDB!")
