from openai import AsyncOpenAI, APIError
from config import config

openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

system_prompt = """You are a helpful and professional virtual assistant inside a Telegram bot. Your job is to guide users through the process of purchasing car insurance.

Be polite, concise, and user-friendly. Respond in a friendly, conversational tone but remain informative and clear.

You will:
- Explain what documents are needed (passport and vehicle registration)
- Guide them through uploading photos. Photos should be uploaded one at a time.
- Confirm extracted details with them. Display the extracted data in a clear and structured format.
- Ask for agreement on a fixed insurance price of 100 USD
- Generate and deliver a dummy policy if everything is confirmed

Do not explain how the system works internally.
Assume the user already knows they are talking to a bot and just wants help.
Your answers should sound natural, but focused — avoid unnecessary filler or repetition.
In the end of every message, there is current state of the conversation, which you can use to determine what to say next. DONT REPEAT THE STATE IN YOUR ANSWERS.
"""

confrimation_prompt = """
You are interpreting a user's response to decide if they confirmed or rejected something that was asked earlier.

You will be given:
- The original message that was shown to the user (containing the extracted data or a fixed insurance price)
- The user's reply to that message

Your job is to determine if the user clearly agreed or confirmed what was asked.

Examples of confirmation: "Yes", "Looks good", "Proceed", "That's fine", "Okay", "I agree"

Interpret the user's reply liberally: accept common casual affirmations like "yeah", "yep", "sure", "okay", "fine", "looks good", "proceed" as confirmation.
Only reject if the user clearly disagrees
Respond exactly with "confirmed" or "rejected".

If the user's reply confirms what was asked, respond with exactly: "confirmed"  
If the user's reply rejects, questions, hesitates, or is ambiguous — respond with: "rejected"

Your reply must be exactly one word: "confirmed" or "rejected" without any additional text or explanation.
"""

policy_prompt = """
You are an insurance assistant bot.

Generate a dummy car insurance policy using this structure:

---
Policy Number: POL-2025-0001
Issue Date: July 16, 2025

Policyholder:
- Full Name: 
- Passport Number: 

Vehicle:
- Make/Model: 
- VIN: 
- Registration Number: 

Coverage:
- Type: Basic Car Insurance
- Validity: 1 Year
- Price: 100 USD

Note: This is a dummy document generated for demonstration purposes only.
---

Format the document cleanly. No extra explanations.
"""



async def generate_response(prompt: str):
    try:
        response = await openai_client.responses.create(
            model="gpt-3.5-turbo",
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}],
                },
            ],
            text={"format": {"type": "text"}},
            reasoning={},
            tools=[

            ],
            temperature=1,
            max_output_tokens=2048,
            top_p=1,
            store=False,
        )
        return response.output_text
    except APIError as e:
        print(f"OpenAI API error: {e}")
        return "Sorry, I couldn't process your request at the moment."

async def generate_policy(passport_data, vehicle_data):
    try:
        response = await openai_client.responses.create(
            model="gpt-3.5-turbo",
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": policy_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": f"Passport data: {passport_data}, Vehicle data: {vehicle_data}"}],
                },
            ],
            text={"format": {"type": "text"}},
            reasoning={},
            tools=[],
            temperature=1,
            max_output_tokens=2048,
            top_p=1,
            store=False,
        )
        return response.output_text
    except APIError as e:
        print(f"OpenAI API error: {e}")
        return "Sorry, I couldn't process your request at the moment."
    
async def confirm_details(user_response: str):
    try:
        response = await openai_client.responses.create(
            model="gpt-3.5-turbo",
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": confrimation_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_response}],
                },
            ],
            text={"format": {"type": "text"}},
            reasoning={},
            tools=[],
            temperature=1,
            max_output_tokens=2048,
            top_p=1,
            store=False,
        )
        return response.output_text.strip().lower()
    except APIError as e:
        print(f"OpenAI API error: {e}")
        return "rejected"  # Default to rejected on error