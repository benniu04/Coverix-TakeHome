import re
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from models import Conversation, Message, Vehicle, ConversationState
from services.openai_service import OpenAIService
from services.nhtsa import NHTSAService
from services.zenquotes import ZenQuotesService


class ConversationEngine:
    """Manages the conversation flow and state transitions."""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.nhtsa_service = NHTSAService()
        self.zenquotes_service = ZenQuotesService()
    
    def _get_context(self, conversation: Conversation) -> Dict[str, Any]:
        """Get current context from conversation."""
        context = {
            "zip_code": conversation.zip_code,
            "full_name": conversation.full_name,
            "email": conversation.email,
            "license_type": conversation.license_type,
            "license_status": conversation.license_status,
            "vehicles_count": len(conversation.vehicles)
        }
        return {k: v for k, v in context.items() if v is not None}
    
    def _get_current_vehicle(self, conversation: Conversation) -> Optional[Vehicle]:
        """Get the current vehicle being configured."""
        if conversation.vehicles:
            return conversation.vehicles[-1]
        return None
    
    async def _validate_and_extract(
        self, 
        state: str, 
        user_input: str,
        conversation: Conversation
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Validate user input for current state.
        Returns: (is_valid, extracted_value, error_message)
        """
        user_input = user_input.strip()
        
        if state == ConversationState.ZIP_CODE.value:
            # Extract 5-digit zip code
            match = re.search(r'\b(\d{5})\b', user_input)
            if match:
                return True, match.group(1), None
            return False, None, "Please provide a valid 5-digit ZIP code."
        
        elif state == ConversationState.FULL_NAME.value:
            # Accept any non-empty string with at least 2 characters
            if len(user_input) >= 2:
                return True, user_input, None
            return False, None, "Please provide your full name."
        
        elif state == ConversationState.EMAIL.value:
            # Basic email validation
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            match = re.search(email_pattern, user_input)
            if match:
                return True, match.group(0).lower(), None
            return False, None, "Please provide a valid email address."
        
        elif state == ConversationState.VEHICLE_CHOICE.value:
            lower = user_input.lower()
            # Check if user provided a VIN directly (17 alphanumeric characters)
            vin_match = re.search(r'\b([A-HJ-NPR-Z0-9]{17})\b', user_input.upper())
            if vin_match:
                # User provided VIN directly, validate it immediately
                vin = vin_match.group(1)
                result = await self.nhtsa_service.decode_vin(vin)
                if result.get('valid'):
                    result['vin'] = vin
                    return True, {'choice': 'vin', 'vin_data': result}, None
                return False, None, result.get('error', 'Invalid VIN.')
            elif 'vin' in lower:
                return True, 'vin', None
            elif any(word in lower for word in ['year', 'make', 'manual', 'type', 'other']):
                return True, 'manual', None
            return False, None, None  # Will re-ask
        
        elif state == ConversationState.VEHICLE_VIN.value:
            # VIN is 17 characters
            vin_match = re.search(r'\b([A-HJ-NPR-Z0-9]{17})\b', user_input.upper())
            if vin_match:
                vin = vin_match.group(1)
                # Validate with NHTSA
                result = await self.nhtsa_service.decode_vin(vin)
                if result.get('valid'):
                    result['vin'] = vin  # Include the VIN in the result
                    return True, result, None
                return False, None, result.get('error', 'Invalid VIN.')
            return False, None, "Please provide a valid 17-character VIN."
        
        elif state == ConversationState.VEHICLE_YEAR.value:
            match = re.search(r'\b(19\d{2}|20\d{2})\b', user_input)
            if match:
                year = int(match.group(1))
                if 1900 <= year <= 2026:
                    return True, year, None
            return False, None, "Please provide a valid vehicle year (e.g., 2020)."
        
        elif state == ConversationState.VEHICLE_MAKE.value:
            if len(user_input) >= 2:
                # Validate with NHTSA
                vehicle = self._get_current_vehicle(conversation)
                year = vehicle.year if vehicle else 2020
                result = await self.nhtsa_service.validate_year_make(year, user_input)
                if result.get('valid'):
                    return True, user_input.title(), None
                return False, None, result.get('error', 'Invalid make.')
            return False, None, "Please provide the vehicle make."
        
        elif state == ConversationState.VEHICLE_BODY.value:
            valid_bodies = ['sedan', 'suv', 'truck', 'coupe', 'hatchback', 'van', 
                          'wagon', 'convertible', 'minivan', 'pickup']
            lower = user_input.lower()
            for body in valid_bodies:
                if body in lower:
                    return True, body.title(), None
            # Accept any reasonable input
            if len(user_input) >= 2:
                return True, user_input.title(), None
            return False, None, "Please provide the body type (e.g., Sedan, SUV, Truck)."
        
        elif state == ConversationState.VEHICLE_USE.value:
            lower = user_input.lower()
            if 'commut' in lower:
                return True, 'commuting', None
            elif 'commercial' in lower:
                return True, 'commercial', None
            elif 'farm' in lower:
                return True, 'farming', None
            elif 'business' in lower:
                return True, 'business', None
            return False, None, "Please specify: Commuting, Commercial, Farming, or Business."
        
        elif state == ConversationState.BLIND_SPOT_WARNING.value:
            lower = user_input.lower()
            if any(word in lower for word in ['yes', 'yeah', 'yep', 'have', 'equipped', 'does']):
                return True, True, None
            elif any(word in lower for word in ['no', 'nope', 'not', "don't", "doesn't"]):
                return True, False, None
            return False, None, "Please answer Yes or No."
        
        elif state == ConversationState.COMMUTE_DAYS.value:
            match = re.search(r'\b([1-7])\b', user_input)
            if match:
                return True, int(match.group(1)), None
            return False, None, "Please provide days per week (1-7)."
        
        elif state == ConversationState.COMMUTE_MILES.value:
            match = re.search(r'\b(\d+)\b', user_input)
            if match:
                miles = int(match.group(1))
                if miles > 0:
                    return True, miles, None
            return False, None, "Please provide the one-way distance in miles."
        
        elif state == ConversationState.ANNUAL_MILEAGE.value:
            match = re.search(r'\b(\d+)\b', user_input.replace(',', ''))
            if match:
                mileage = int(match.group(1))
                if mileage > 0:
                    return True, mileage, None
            return False, None, "Please provide estimated annual mileage."
        
        elif state == ConversationState.ADD_ANOTHER_VEHICLE.value:
            lower = user_input.lower()
            if any(word in lower for word in ['yes', 'yeah', 'yep', 'another', 'add', 'more']):
                return True, True, None
            elif any(word in lower for word in ['no', 'nope', 'done', "that's all", "that's it"]):
                return True, False, None
            return False, None, "Would you like to add another vehicle? (Yes/No)"
        
        elif state == ConversationState.LICENSE_TYPE.value:
            lower = user_input.lower()
            if 'foreign' in lower:
                return True, 'foreign', None
            elif 'personal' in lower:
                return True, 'personal', None
            elif 'commercial' in lower or 'cdl' in lower:
                return True, 'commercial', None
            return False, None, "Please specify: Foreign, Personal, or Commercial."
        
        elif state == ConversationState.LICENSE_STATUS.value:
            lower = user_input.lower()
            if 'valid' in lower or 'active' in lower or 'good' in lower:
                return True, 'valid', None
            elif 'suspend' in lower:
                return True, 'suspended', None
            return False, None, "Please specify: Valid or Suspended."
        
        return True, user_input, None
    
    def _get_next_state(
        self, 
        current_state: str, 
        value: Any,
        conversation: Conversation
    ) -> str:
        """Determine the next state based on current state and value."""
        
        state_transitions = {
            ConversationState.ZIP_CODE.value: ConversationState.FULL_NAME.value,
            ConversationState.FULL_NAME.value: ConversationState.EMAIL.value,
            ConversationState.EMAIL.value: ConversationState.VEHICLE_CHOICE.value,
        }
        
        if current_state == ConversationState.VEHICLE_CHOICE.value:
            # If user provided VIN data directly, skip to VEHICLE_USE
            if isinstance(value, dict) and 'vin_data' in value:
                return ConversationState.VEHICLE_USE.value
            # If user said they want to provide VIN, go to VIN state
            elif value == 'vin':
                return ConversationState.VEHICLE_VIN.value
            # Otherwise, go to manual entry (year)
            return ConversationState.VEHICLE_YEAR.value
        
        if current_state == ConversationState.VEHICLE_VIN.value:
            return ConversationState.VEHICLE_USE.value
        
        if current_state == ConversationState.VEHICLE_YEAR.value:
            return ConversationState.VEHICLE_MAKE.value
        
        if current_state == ConversationState.VEHICLE_MAKE.value:
            return ConversationState.VEHICLE_BODY.value
        
        if current_state == ConversationState.VEHICLE_BODY.value:
            return ConversationState.VEHICLE_USE.value
        
        if current_state == ConversationState.VEHICLE_USE.value:
            return ConversationState.BLIND_SPOT_WARNING.value
        
        if current_state == ConversationState.BLIND_SPOT_WARNING.value:
            vehicle = self._get_current_vehicle(conversation)
            if vehicle and vehicle.vehicle_use == 'commuting':
                return ConversationState.COMMUTE_DAYS.value
            return ConversationState.ANNUAL_MILEAGE.value
        
        if current_state == ConversationState.COMMUTE_DAYS.value:
            return ConversationState.COMMUTE_MILES.value
        
        if current_state == ConversationState.COMMUTE_MILES.value:
            # After commute vehicle is done, ask if they want to add another
            return ConversationState.ADD_ANOTHER_VEHICLE.value
        
        if current_state == ConversationState.ANNUAL_MILEAGE.value:
            # After commercial/farming/business vehicle is done, ask if they want to add another
            return ConversationState.ADD_ANOTHER_VEHICLE.value
        
        if current_state == ConversationState.ADD_ANOTHER_VEHICLE.value:
            if value:  # User wants to add another vehicle
                return ConversationState.VEHICLE_CHOICE.value
            # User is done adding vehicles, now collect license info
            return ConversationState.LICENSE_TYPE.value
        
        if current_state == ConversationState.LICENSE_TYPE.value:
            if value == 'foreign':
                # Foreign license, skip status and complete
                return ConversationState.COMPLETE.value
            return ConversationState.LICENSE_STATUS.value
        
        if current_state == ConversationState.LICENSE_STATUS.value:
            # All done!
            return ConversationState.COMPLETE.value
        
        return state_transitions.get(current_state, current_state)
    
    async def _save_value(
        self,
        state: str,
        value: Any,
        conversation: Conversation,
        db: Session
    ):
        """Save the extracted value to the appropriate field."""
        
        if state == ConversationState.ZIP_CODE.value:
            conversation.zip_code = value
        
        elif state == ConversationState.FULL_NAME.value:
            conversation.full_name = value
        
        elif state == ConversationState.EMAIL.value:
            conversation.email = value
        
        elif state == ConversationState.VEHICLE_CHOICE.value:
            # Create a new vehicle entry
            vehicle = Vehicle(conversation_id=conversation.id)
            db.add(vehicle)
            db.commit()
            
            # If user provided VIN directly, save the VIN data
            if isinstance(value, dict) and 'vin_data' in value:
                vin_data = value['vin_data']
                vehicle.vin = vin_data.get('vin')
                vehicle.year = int(vin_data.get('year')) if vin_data.get('year') else None
                vehicle.make = vin_data.get('make')
                vehicle.body_type = vin_data.get('body_class')
                db.commit()
        
        elif state == ConversationState.VEHICLE_VIN.value:
            vehicle = self._get_current_vehicle(conversation)
            if vehicle and isinstance(value, dict):
                vehicle.vin = value.get('vin')
                vehicle.year = int(value.get('year')) if value.get('year') else None
                vehicle.make = value.get('make')
                vehicle.body_type = value.get('body_class')
        
        elif state == ConversationState.VEHICLE_YEAR.value:
            vehicle = self._get_current_vehicle(conversation)
            if vehicle:
                vehicle.year = value
        
        elif state == ConversationState.VEHICLE_MAKE.value:
            vehicle = self._get_current_vehicle(conversation)
            if vehicle:
                vehicle.make = value
        
        elif state == ConversationState.VEHICLE_BODY.value:
            vehicle = self._get_current_vehicle(conversation)
            if vehicle:
                vehicle.body_type = value
        
        elif state == ConversationState.VEHICLE_USE.value:
            vehicle = self._get_current_vehicle(conversation)
            if vehicle:
                vehicle.vehicle_use = value
        
        elif state == ConversationState.BLIND_SPOT_WARNING.value:
            vehicle = self._get_current_vehicle(conversation)
            if vehicle:
                vehicle.blind_spot_warning = value
        
        elif state == ConversationState.COMMUTE_DAYS.value:
            vehicle = self._get_current_vehicle(conversation)
            if vehicle:
                vehicle.days_per_week = value
        
        elif state == ConversationState.COMMUTE_MILES.value:
            vehicle = self._get_current_vehicle(conversation)
            if vehicle:
                vehicle.one_way_miles = value
        
        elif state == ConversationState.ANNUAL_MILEAGE.value:
            vehicle = self._get_current_vehicle(conversation)
            if vehicle:
                vehicle.annual_mileage = value
        
        elif state == ConversationState.LICENSE_TYPE.value:
            conversation.license_type = value
        
        elif state == ConversationState.LICENSE_STATUS.value:
            conversation.license_status = value
        
        db.commit()
    
    async def process_message(
        self,
        conversation: Conversation,
        user_message: str,
        db: Session
    ) -> str:
        """Process a user message and return the bot's response."""
        
        # Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_message
        )
        db.add(user_msg)
        db.commit()
        
        # Check for frustration
        is_frustrated = await self.openai_service.check_frustration(user_message)
        
        if is_frustrated:
            quote = await self.zenquotes_service.get_quote()
            response = f"I understand this can be frustrating. Here's something to brighten your day:\n\n{quote}\n\nI'm here to help. Let's continue when you're ready."
        else:
            current_state = conversation.current_state
            
            # Validate and extract value
            is_valid, value, error_msg = await self._validate_and_extract(
                current_state, user_message, conversation
            )
            
            context = self._get_context(conversation)
            conversation_history = [
                {"role": m.role, "content": m.content}
                for m in conversation.messages[-10:]
            ]
            
            additional_context = None
            
            if is_valid and value is not None:
                # Save the value
                await self._save_value(current_state, value, conversation, db)
                
                # Move to next state
                next_state = self._get_next_state(current_state, value, conversation)
                conversation.current_state = next_state
                db.commit()
                
                # Refresh context after saving
                context = self._get_context(conversation)
            else:
                if error_msg:
                    additional_context = f"The user's input was invalid. Error: {error_msg}"
            
            # Generate response using OpenAI
            response = await self.openai_service.generate_response(
                current_state=conversation.current_state,
                user_message=user_message,
                conversation_history=conversation_history,
                context=context,
                additional_context=additional_context
            )
        
        # Save assistant response
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response
        )
        db.add(assistant_msg)
        db.commit()
        
        return response
    
    async def get_welcome_message(self, conversation: Conversation, db: Session) -> str:
        """Generate the initial welcome message."""
        
        welcome = "👋 Hi there! Welcome to our insurance onboarding. I'll help you get set up quickly. Let's start with your ZIP code - what is it?"
        
        # Save the welcome message
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=welcome
        )
        db.add(assistant_msg)
        db.commit()
        
        return welcome

