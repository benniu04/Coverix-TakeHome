import os
from openai import AsyncOpenAI
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class OpenAIService:
    """Service for generating conversational responses using OpenAI."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo"
    
    def _get_system_prompt(self, current_state: str, context: Dict) -> str:
        """Generate system prompt based on current conversation state."""
        
        base_prompt = """You are a friendly, professional insurance onboarding assistant. Your role is to collect information from users in a conversational way. Be concise but warm.

CRITICAL RULES:
1. You MUST ONLY ask the question specified in your current task - nothing else
2. NEVER skip ahead to other questions or topics
3. Always acknowledge what the user just provided, then IMMEDIATELY ask the EXACT question specified in your current task
4. If the user seems frustrated, upset, or asks to speak with a human, respond with empathy and include the phrase [FRUSTRATED_USER] at the start of your response
5. Validate inputs naturally (e.g., if email looks invalid, politely ask them to check it)
6. Keep responses brief - one or two sentences when asking for information
7. Don't repeat information the user has already provided
8. NEVER say things like "That's all the information I need" or "We're all set" or "Do you have any other vehicles" unless the current task explicitly says to ask that
"""
        
        state_prompts = {
            "zip_code": "Ask for their ZIP code. Validate it's a 5-digit number.",
            "full_name": "Briefly acknowledge their ZIP code, then ask for their full name.",
            "email": "Briefly acknowledge their name, then ask for their email address.",
            "vehicle_choice": "Briefly acknowledge their email, then ask if they want to provide a VIN number OR enter Year, Make, and Body Type manually.",
            "vehicle_vin": "Ask for their vehicle's VIN (17 characters).",
            "vehicle_year": "Ask for the vehicle's year.",
            "vehicle_make": "Acknowledge the year, then ask for the vehicle's make (e.g., Toyota, Ford, Honda).",
            "vehicle_body": "Acknowledge the make, then ask for the vehicle's body type (e.g., Sedan, SUV, Truck, Coupe).",
            "vehicle_use": "Acknowledge the vehicle details, then ask how they use this vehicle. Options: Commuting, Commercial, Farming, or Business.",
            "blind_spot_warning": "Acknowledge the vehicle use, then ask if the vehicle has blind spot warning equipment (Yes/No).",
            "commute_days": "Acknowledge their response, then ask how many days per week they use this vehicle for commuting.",
            "commute_miles": "Acknowledge the days, then ask about one-way miles to work/school.",
            "annual_mileage": "Acknowledge their commute distance, then ask for their estimated ANNUAL MILEAGE for this vehicle. Do NOT ask about other vehicles or license yet - ONLY ask for annual mileage.",
            "add_another_vehicle": "Acknowledge the information collected, then ask if they want to add another vehicle to their policy.",
            "license_type": "Acknowledge the vehicle information is complete, then ask about their US license type. Options: Foreign, Personal, or Commercial.",
            "license_status": "Acknowledge the license type, then ask about their license status: Valid or Suspended.",
            "complete": "Thank them warmly and let them know their information has been collected successfully. Keep it brief and positive."
        }
        
        state_instruction = state_prompts.get(current_state, "Continue the conversation naturally.")
        
        context_str = ""
        if context:
            context_str = f"\n\nCollected information so far:\n"
            for key, value in context.items():
                if value:
                    context_str += f"- {key}: {value}\n"
        
        return f"{base_prompt}\n\n=== YOUR CURRENT TASK (DO EXACTLY THIS) ===\n{state_instruction}\n===========================================\n{context_str}"
    
    async def generate_response(
        self,
        current_state: str,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        context: Dict,
        additional_context: Optional[str] = None
    ) -> str:
        """Generate a response using OpenAI."""
        
        system_prompt = self._get_system_prompt(current_state, context)
        
        if additional_context:
            system_prompt += f"\n\nAdditional context: {additional_context}"
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (last 10 messages for context)
        for msg in conversation_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback response if OpenAI fails
            fallback_responses = {
                "zip_code": "Could you please provide your ZIP code?",
                "full_name": "What is your full name?",
                "email": "What is your email address?",
                "vehicle_choice": "Would you like to enter a VIN or provide Year, Make, and Body Type?",
                "vehicle_vin": "Please enter the 17-character VIN.",
                "vehicle_year": "What year is the vehicle?",
                "vehicle_make": "What is the make of the vehicle?",
                "vehicle_body": "What is the body type?",
                "vehicle_use": "How do you use this vehicle? (Commuting, Commercial, Farming, Business)",
                "blind_spot_warning": "Does this vehicle have blind spot warning? (Yes/No)",
                "commute_days": "How many days per week do you commute?",
                "commute_miles": "How many miles is your one-way commute?",
                "annual_mileage": "Thank you! Now, what is your estimated annual mileage for this vehicle?",
                "add_another_vehicle": "Would you like to add another vehicle?",
                "license_type": "What type of US license do you have? (Foreign, Personal, Commercial)",
                "license_status": "What is your license status? (Valid/Suspended)",
                "complete": "Thank you! Your information has been collected successfully. You can now start a new session if needed."
            }
            return fallback_responses.get(current_state, "I'm sorry, could you repeat that?")
    
    async def check_frustration(self, message: str) -> bool:
        """Check if user message indicates frustration."""
        frustration_keywords = [
            "frustrated", "angry", "annoyed", "speak to human", "talk to someone",
            "real person", "agent", "representative", "this is ridiculous",
            "hate this", "stupid", "useless", "waste of time", "give up",
            "help me", "not working", "doesn't work", "broken"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in frustration_keywords)

