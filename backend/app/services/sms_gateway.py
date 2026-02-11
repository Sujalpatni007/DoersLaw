"""
SMS Gateway Service - Simulation Mode
Simulates SMS sending/receiving without actual Twilio costs
Supports conversation state tracking and IVR via gTTS
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable
from enum import Enum
import uuid
import asyncio
import logging

# Configure logging for SMS simulation
logging.basicConfig(level=logging.INFO)
sms_logger = logging.getLogger("SMS_GATEWAY")


class SMSDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ConversationState(str, Enum):
    """SMS Conversation states for state machine"""
    INITIAL = "initial"
    AWAITING_LANGUAGE = "awaiting_language"
    AWAITING_ACTION = "awaiting_action"
    CASE_STATUS = "case_status"
    NEW_CASE = "new_case"
    DESCRIBE_PROBLEM = "describe_problem"
    CONTACT_LAWYER = "contact_lawyer"
    AWAITING_DETAILS = "awaiting_details"
    CONFIRMED = "confirmed"
    ENDED = "ended"


@dataclass
class SMSMessage:
    """Individual SMS message"""
    id: str
    phone_number: str
    content: str
    direction: SMSDirection
    timestamp: datetime
    conversation_id: str
    delivered: bool = True
    read: bool = False
    metadata: Dict = field(default_factory=dict)


@dataclass
class SMSConversation:
    """SMS conversation thread with state tracking"""
    id: str
    phone_number: str
    user_id: Optional[int]
    state: ConversationState
    language: str
    messages: List[SMSMessage]
    context: Dict
    created_at: datetime
    last_activity: datetime
    case_id: Optional[int] = None


class SMSGateway:
    """
    SMS Gateway Simulation
    - Console output shows "SMS sent: [content]"
    - Stores all SMS threads in memory (production: database)
    - State machine tracks conversation context
    """
    
    def __init__(self):
        self.conversations: Dict[str, SMSConversation] = {}
        self.phone_to_conversation: Dict[str, str] = {}
        self.virtual_number = "+91-1800-DOER-LAW"
        
        # Menu templates in multiple languages
        self.menus = {
            "en": {
                "welcome": "Welcome to DOER Land Dispute Resolution!\n\nReply with:\n1. Check case status\n2. File new case\n3. Talk to lawyer\n4. Change language",
                "language_select": "Select language:\n1. English\n2. हिंदी (Hindi)\n3. தமிழ் (Tamil)\n4. తెలుగు (Telugu)",
                "case_status": "Please enter your Case ID (e.g., CASE-2026-00142):",
                "new_case": "Briefly describe your land dispute problem. We'll call you within 24 hours.",
                "contact_lawyer": "Your assigned lawyer will contact you shortly.\nFor urgent matters, call: +91-9876543210",
                "case_found": "Case {case_id}\nStatus: {status}\nPhase: {phase}\nLawyer: {lawyer}\n\nReply 0 for main menu",
                "case_not_found": "Case not found. Please check your Case ID.\n\nReply 0 for main menu",
                "problem_received": "Thank you! Your case has been registered.\nCase ID: {case_id}\nWe'll contact you within 24 hours.\n\nReply 0 for main menu",
                "invalid_option": "Invalid option. Please reply with a number from the menu.",
                "main_menu": "Reply 0 for main menu",
            },
            "hi": {
                "welcome": "DOER भूमि विवाद समाधान में आपका स्वागत है!\n\nजवाब दें:\n1. केस की स्थिति देखें\n2. नया केस दर्ज करें\n3. वकील से बात करें\n4. भाषा बदलें",
                "language_select": "भाषा चुनें:\n1. English\n2. हिंदी\n3. தமிழ்\n4. తెలుగు",
                "case_status": "कृपया अपना केस आईडी दर्ज करें (उदा. CASE-2026-00142):",
                "new_case": "अपनी भूमि विवाद समस्या का संक्षेप में वर्णन करें। हम 24 घंटे में आपसे संपर्क करेंगे।",
                "contact_lawyer": "आपके नियुक्त वकील जल्द ही आपसे संपर्क करेंगे।\nतत्काल मामलों के लिए कॉल करें: +91-9876543210",
                "problem_received": "धन्यवाद! आपका केस दर्ज हो गया है।\nकेस आईडी: {case_id}\nहम 24 घंटे में आपसे संपर्क करेंगे।\n\nमुख्य मेनू के लिए 0 दबाएं",
                "invalid_option": "अमान्य विकल्प। कृपया मेनू से एक नंबर चुनें।",
                "main_menu": "मुख्य मेनू के लिए 0 दबाएं",
            },
            "ta": {
                "welcome": "DOER நில தகராறு தீர்வுக்கு வரவேற்கிறோம்!\n\nபதில்:\n1. வழக்கு நிலை\n2. புதிய வழக்கு\n3. வழக்கறிஞர் தொடர்பு\n4. மொழி மாற்று",
                "language_select": "மொழி தேர்வு:\n1. English\n2. हिंदी\n3. தமிழ்\n4. తెలుగు",
            },
            "te": {
                "welcome": "DOER భూ వివాద పరిష్కారానికి స్వాగతం!\n\nప్రత్యుత్తరం:\n1. కేసు స్థితి\n2. కొత్త కేసు\n3. లాయర్ సంప్రదించు\n4. భాష మార్చు",
                "language_select": "భాష ఎంచుకోండి:\n1. English\n2. हिंदी\n3. தமிழ்\n4. తెలుగు",
            }
        }
        
        # Mock case database
        self.mock_cases = {
            "CASE-2026-00142": {
                "status": "Active",
                "phase": "Legal Analysis",
                "lawyer": "Adv. Rajesh Kulkarni",
            },
            "CASE-2026-00138": {
                "status": "In Progress",
                "phase": "Negotiation",
                "lawyer": "Adv. Priya Deshmukh",
            }
        }
    
    def _get_menu(self, key: str, language: str) -> str:
        """Get menu text in specified language with fallback to English"""
        lang_menus = self.menus.get(language, self.menus["en"])
        return lang_menus.get(key, self.menus["en"].get(key, ""))
    
    def _generate_case_id(self) -> str:
        """Generate a new case ID"""
        import random
        return f"CASE-2026-{random.randint(10000, 99999)}"
    
    async def send_sms(self, phone_number: str, content: str, conversation_id: str) -> SMSMessage:
        """
        Send SMS (simulation mode - outputs to console)
        """
        message = SMSMessage(
            id=str(uuid.uuid4()),
            phone_number=phone_number,
            content=content,
            direction=SMSDirection.OUTBOUND,
            timestamp=datetime.now(),
            conversation_id=conversation_id,
        )
        
        # Console output simulation
        sms_logger.info(f"\n{'='*50}")
        sms_logger.info(f"📤 SMS SENT to {phone_number}")
        sms_logger.info(f"{'='*50}")
        sms_logger.info(f"{content}")
        sms_logger.info(f"{'='*50}\n")
        
        # Store in conversation
        if conversation_id in self.conversations:
            self.conversations[conversation_id].messages.append(message)
            self.conversations[conversation_id].last_activity = datetime.now()
        
        return message
    
    async def receive_sms(self, phone_number: str, content: str) -> SMSMessage:
        """
        Receive incoming SMS and process through state machine
        """
        # Get or create conversation
        conv_id = self.phone_to_conversation.get(phone_number)
        
        if not conv_id:
            # New conversation
            conv_id = str(uuid.uuid4())
            conversation = SMSConversation(
                id=conv_id,
                phone_number=phone_number,
                user_id=None,
                state=ConversationState.INITIAL,
                language="en",
                messages=[],
                context={},
                created_at=datetime.now(),
                last_activity=datetime.now(),
            )
            self.conversations[conv_id] = conversation
            self.phone_to_conversation[phone_number] = conv_id
        
        conversation = self.conversations[conv_id]
        
        # Create inbound message
        message = SMSMessage(
            id=str(uuid.uuid4()),
            phone_number=phone_number,
            content=content,
            direction=SMSDirection.INBOUND,
            timestamp=datetime.now(),
            conversation_id=conv_id,
        )
        conversation.messages.append(message)
        conversation.last_activity = datetime.now()
        
        # Console output for received SMS
        sms_logger.info(f"\n{'='*50}")
        sms_logger.info(f"📥 SMS RECEIVED from {phone_number}")
        sms_logger.info(f"{'='*50}")
        sms_logger.info(f"{content}")
        sms_logger.info(f"{'='*50}\n")
        
        # Process through state machine
        response = await self._process_state_machine(conversation, content)
        
        # Send response
        if response:
            await self.send_sms(phone_number, response, conv_id)
        
        return message
    
    async def _process_state_machine(self, conv: SMSConversation, user_input: str) -> str:
        """Process user input through conversation state machine"""
        user_input = user_input.strip()
        lang = conv.language
        
        # Handle "0" to return to main menu
        if user_input == "0":
            conv.state = ConversationState.AWAITING_ACTION
            return self._get_menu("welcome", lang)
        
        # State: INITIAL - First contact
        if conv.state == ConversationState.INITIAL:
            conv.state = ConversationState.AWAITING_ACTION
            return self._get_menu("welcome", lang)
        
        # State: AWAITING_ACTION - Main menu
        elif conv.state == ConversationState.AWAITING_ACTION:
            if user_input == "1":
                conv.state = ConversationState.CASE_STATUS
                return self._get_menu("case_status", lang)
            elif user_input == "2":
                conv.state = ConversationState.NEW_CASE
                return self._get_menu("new_case", lang)
            elif user_input == "3":
                conv.state = ConversationState.CONTACT_LAWYER
                return self._get_menu("contact_lawyer", lang)
            elif user_input == "4":
                conv.state = ConversationState.AWAITING_LANGUAGE
                return self._get_menu("language_select", lang)
            else:
                return self._get_menu("invalid_option", lang) + "\n\n" + self._get_menu("welcome", lang)
        
        # State: AWAITING_LANGUAGE
        elif conv.state == ConversationState.AWAITING_LANGUAGE:
            lang_map = {"1": "en", "2": "hi", "3": "ta", "4": "te"}
            if user_input in lang_map:
                conv.language = lang_map[user_input]
                conv.state = ConversationState.AWAITING_ACTION
                return self._get_menu("welcome", conv.language)
            else:
                return self._get_menu("invalid_option", lang)
        
        # State: CASE_STATUS - Waiting for case ID
        elif conv.state == ConversationState.CASE_STATUS:
            case_id = user_input.upper()
            if case_id in self.mock_cases:
                case = self.mock_cases[case_id]
                conv.state = ConversationState.AWAITING_ACTION
                return self._get_menu("case_found", lang).format(
                    case_id=case_id,
                    status=case["status"],
                    phase=case["phase"],
                    lawyer=case["lawyer"]
                )
            else:
                conv.state = ConversationState.AWAITING_ACTION
                return self._get_menu("case_not_found", lang)
        
        # State: NEW_CASE - Waiting for problem description
        elif conv.state == ConversationState.NEW_CASE:
            # Store the problem description
            conv.context["problem_description"] = user_input
            new_case_id = self._generate_case_id()
            conv.case_id = new_case_id
            conv.state = ConversationState.CONFIRMED
            
            # Add to mock database
            self.mock_cases[new_case_id] = {
                "status": "Pending",
                "phase": "Intake",
                "lawyer": "Unassigned",
                "description": user_input,
            }
            
            return self._get_menu("problem_received", lang).format(case_id=new_case_id)
        
        # State: CONTACT_LAWYER
        elif conv.state == ConversationState.CONTACT_LAWYER:
            conv.state = ConversationState.AWAITING_ACTION
            return self._get_menu("welcome", lang)
        
        # State: CONFIRMED - After case creation
        elif conv.state == ConversationState.CONFIRMED:
            conv.state = ConversationState.AWAITING_ACTION
            return self._get_menu("welcome", lang)
        
        # Default fallback
        return self._get_menu("welcome", lang)
    
    def get_conversation(self, conversation_id: str) -> Optional[SMSConversation]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def get_conversation_by_phone(self, phone_number: str) -> Optional[SMSConversation]:
        """Get conversation by phone number"""
        conv_id = self.phone_to_conversation.get(phone_number)
        if conv_id:
            return self.conversations.get(conv_id)
        return None
    
    def get_all_conversations(self) -> List[SMSConversation]:
        """Get all conversations for admin panel"""
        return list(self.conversations.values())
    
    async def send_bulk_notification(self, phone_numbers: List[str], message: str) -> List[SMSMessage]:
        """Send bulk SMS notifications"""
        sent_messages = []
        for phone in phone_numbers:
            conv_id = self.phone_to_conversation.get(phone, str(uuid.uuid4()))
            msg = await self.send_sms(phone, message, conv_id)
            sent_messages.append(msg)
        return sent_messages
    
    async def send_critical_update(self, phone_number: str, case_id: str, update: str):
        """
        Send critical case update via SMS
        Used even if user has app installed (dual-channel notification)
        """
        message = f"🔔 DOER Alert\n\nCase: {case_id}\n{update}\n\nFor details, open DOER app or reply 1."
        conv_id = self.phone_to_conversation.get(phone_number, str(uuid.uuid4()))
        await self.send_sms(phone_number, message, conv_id)


# Singleton instance
_sms_gateway: Optional[SMSGateway] = None

def get_sms_gateway() -> SMSGateway:
    global _sms_gateway
    if _sms_gateway is None:
        _sms_gateway = SMSGateway()
    return _sms_gateway
