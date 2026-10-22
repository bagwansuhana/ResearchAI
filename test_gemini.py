from agents.gemini_client import get_gemini_client


client = get_gemini_client()

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Reply with exactly: Gemini connection successful."
)

print(response.text)