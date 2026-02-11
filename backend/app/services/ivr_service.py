"""
IVR (Interactive Voice Response) Service
Uses gTTS for text-to-speech in Hindi/Tamil/Telugu
Simple phone tree for case status and lawyer contact
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import os
import uuid
import logging

# Configure logging
ivr_logger = logging.getLogger("IVR_SYSTEM")


class IVRState(str, Enum):
    """IVR call states"""
    WELCOME = "welcome"
    LANGUAGE_SELECT = "language_select"
    MAIN_MENU = "main_menu"
    CASE_STATUS = "case_status"
    ENTER_CASE_ID = "enter_case_id"
    SPEAK_TO_LAWYER = "speak_to_lawyer"
    TRANSFER = "transfer"
    GOODBYE = "goodbye"


@dataclass
class IVRCall:
    """IVR call session"""
    id: str
    phone_number: str
    state: IVRState
    language: str
    dtmf_input: str  # Collected digits
    context: Dict
    started_at: datetime
    ended_at: Optional[datetime] = None


class IVRService:
    """
    IVR System with gTTS text-to-speech
    Simulates phone tree navigation
    """
    
    def __init__(self):
        self.calls: Dict[str, IVRCall] = {}
        self.gtts_available = False
        
        # Check if gTTS is available
        try:
            from gtts import gTTS
            self.gtts_available = True
        except ImportError:
            ivr_logger.warning("gTTS not installed. TTS will be simulated.")
        
        # IVR prompts in multiple languages
        self.prompts = {
            "en": {
                "welcome": "Welcome to DOER Land Dispute Resolution. Press 1 for English. Press 2 for Hindi.",
                "main_menu": "Press 1 to check case status. Press 2 to speak to a lawyer. Press 3 to file a new case. Press 0 for main menu.",
                "case_status": "Please enter your 5-digit case number followed by the hash key.",
                "case_found": "Your case {case_id} is in {phase} phase. Status is {status}. Press 0 to return to main menu.",
                "case_not_found": "Sorry, case not found. Please check your case number and try again. Press 0 for main menu.",
                "transfer_lawyer": "Please hold while we connect you to your assigned lawyer. This call may be recorded for quality purposes.",
                "goodbye": "Thank you for calling DOER. Goodbye.",
                "invalid": "Invalid input. Please try again.",
            },
            "hi": {
                "welcome": "DOER भूमि विवाद समाधान में आपका स्वागत है। अंग्रेजी के लिए 1 दबाएं। हिंदी के लिए 2 दबाएं।",
                "main_menu": "केस की स्थिति जानने के लिए 1 दबाएं। वकील से बात करने के लिए 2 दबाएं। नया केस दर्ज करने के लिए 3 दबाएं।",
                "case_status": "कृपया अपना 5 अंकों का केस नंबर हैश कुंजी के साथ दर्ज करें।",
                "case_found": "आपका केस {case_id} {phase} चरण में है। स्थिति {status} है। मुख्य मेनू के लिए 0 दबाएं।",
                "case_not_found": "क्षमा करें, केस नहीं मिला। कृपया अपना केस नंबर जांचें। मुख्य मेनू के लिए 0 दबाएं।",
                "transfer_lawyer": "कृपया प्रतीक्षा करें, हम आपको आपके वकील से जोड़ रहे हैं।",
                "goodbye": "DOER को कॉल करने के लिए धन्यवाद। अलविदा।",
                "invalid": "अमान्य इनपुट। कृपया पुनः प्रयास करें।",
            },
            "ta": {
                "welcome": "DOER நில தகராறு தீர்வுக்கு வரவேற்கிறோம். ஆங்கிலத்திற்கு 1 அழுத்தவும். தமிழுக்கு 3 அழுத்தவும்.",
                "main_menu": "வழக்கு நிலைக்கு 1 அழுத்தவும். வழக்கறிஞர் தொடர்புக்கு 2 அழுத்தவும்.",
            },
        }
        
        # Mock cases (shared with SMS gateway)
        self.mock_cases = {
            "00142": {
                "case_id": "CASE-2026-00142",
                "status": "Active",
                "phase": "Legal Analysis",
                "lawyer_phone": "+91-9876543210",
            },
        }
    
    async def generate_audio(self, text: str, language: str = "en") -> Optional[str]:
        """
        Generate audio file using gTTS
        Returns path to generated audio file
        """
        if not self.gtts_available:
            ivr_logger.info(f"[TTS SIMULATION] Language: {language}")
            ivr_logger.info(f"[TTS SIMULATION] Text: {text}")
            return None
        
        try:
            from gtts import gTTS
            
            # Map language codes
            lang_map = {"en": "en", "hi": "hi", "ta": "ta", "te": "te"}
            gtts_lang = lang_map.get(language, "en")
            
            # Generate audio
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            
            # Save to temp file
            audio_dir = "/tmp/doer_ivr_audio"
            os.makedirs(audio_dir, exist_ok=True)
            filename = f"{audio_dir}/{uuid.uuid4()}.mp3"
            tts.save(filename)
            
            ivr_logger.info(f"🔊 Audio generated: {filename}")
            return filename
            
        except Exception as e:
            ivr_logger.error(f"TTS generation error: {e}")
            return None
    
    async def start_call(self, phone_number: str) -> IVRCall:
        """Start a new IVR call session"""
        call = IVRCall(
            id=str(uuid.uuid4()),
            phone_number=phone_number,
            state=IVRState.WELCOME,
            language="en",
            dtmf_input="",
            context={},
            started_at=datetime.now(),
        )
        self.calls[call.id] = call
        
        ivr_logger.info(f"\n{'='*50}")
        ivr_logger.info(f"📞 IVR CALL STARTED: {phone_number}")
        ivr_logger.info(f"{'='*50}")
        
        # Play welcome prompt
        prompt = self.prompts["en"]["welcome"]
        await self.generate_audio(prompt, "en")
        
        return call
    
    async def process_dtmf(self, call_id: str, digit: str) -> Dict:
        """Process DTMF input (phone keypad press)"""
        call = self.calls.get(call_id)
        if not call:
            return {"error": "Call not found"}
        
        ivr_logger.info(f"📱 DTMF Input: {digit}")
        
        response = {"state": call.state.value, "prompt": "", "audio_file": None}
        
        # State machine processing
        if call.state == IVRState.WELCOME:
            if digit == "1":
                call.language = "en"
            elif digit == "2":
                call.language = "hi"
            elif digit == "3":
                call.language = "ta"
            else:
                response["prompt"] = self.prompts[call.language]["invalid"]
                return response
            
            call.state = IVRState.MAIN_MENU
            response["prompt"] = self.prompts[call.language]["main_menu"]
        
        elif call.state == IVRState.MAIN_MENU:
            if digit == "1":
                call.state = IVRState.ENTER_CASE_ID
                response["prompt"] = self.prompts[call.language]["case_status"]
            elif digit == "2":
                call.state = IVRState.TRANSFER
                response["prompt"] = self.prompts[call.language]["transfer_lawyer"]
                response["action"] = "transfer_to_lawyer"
            elif digit == "3":
                response["prompt"] = "For new cases, please use the DOER app or send an SMS to our number."
            elif digit == "0":
                response["prompt"] = self.prompts[call.language]["main_menu"]
            else:
                response["prompt"] = self.prompts[call.language]["invalid"]
        
        elif call.state == IVRState.ENTER_CASE_ID:
            if digit == "#":
                # End of case ID input
                case_num = call.dtmf_input
                call.dtmf_input = ""
                
                if case_num in self.mock_cases:
                    case = self.mock_cases[case_num]
                    response["prompt"] = self.prompts[call.language]["case_found"].format(
                        case_id=case["case_id"],
                        phase=case["phase"],
                        status=case["status"],
                    )
                else:
                    response["prompt"] = self.prompts[call.language]["case_not_found"]
                
                call.state = IVRState.MAIN_MENU
            elif digit == "0":
                call.dtmf_input = ""
                call.state = IVRState.MAIN_MENU
                response["prompt"] = self.prompts[call.language]["main_menu"]
            else:
                call.dtmf_input += digit
                response["prompt"] = f"Entered: {call.dtmf_input}"
        
        # Generate audio for response
        if response["prompt"]:
            audio_file = await self.generate_audio(response["prompt"], call.language)
            response["audio_file"] = audio_file
        
        response["state"] = call.state.value
        return response
    
    async def end_call(self, call_id: str):
        """End IVR call session"""
        call = self.calls.get(call_id)
        if call:
            call.ended_at = datetime.now()
            call.state = IVRState.GOODBYE
            
            ivr_logger.info(f"\n{'='*50}")
            ivr_logger.info(f"📞 IVR CALL ENDED: {call.phone_number}")
            ivr_logger.info(f"Duration: {(call.ended_at - call.started_at).seconds}s")
            ivr_logger.info(f"{'='*50}")
    
    def get_call(self, call_id: str) -> Optional[IVRCall]:
        """Get call by ID"""
        return self.calls.get(call_id)


# Singleton instance
_ivr_service: Optional[IVRService] = None

def get_ivr_service() -> IVRService:
    global _ivr_service
    if _ivr_service is None:
        _ivr_service = IVRService()
    return _ivr_service
