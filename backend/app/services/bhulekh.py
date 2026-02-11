"""
Bhulekh Integration Service - Mock Version
Land record verification with LRU caching and rate limiting
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from functools import lru_cache
from enum import Enum
import json
import asyncio
import random
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BHULEKH")


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    PARTIAL_MATCH = "partial_match"
    NOT_FOUND = "not_found"
    DISCREPANCY = "discrepancy"
    ERROR = "error"


@dataclass
class LandRecord:
    state: str
    district: str
    tehsil: str
    village: str
    khasra: str
    owner: str
    area_acres: float
    cultivation: str
    encumbrances: str
    
    def to_dict(self):
        return self.__dict__


@dataclass 
class VerificationResult:
    status: VerificationStatus
    record: Optional[LandRecord]
    confidence: float
    discrepancies: List[str]
    verification_id: str
    timestamp: datetime
    raw_response: Optional[Dict] = None


class RateLimiter:
    """Simple rate limiter with exponential backoff"""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[datetime] = []
        self.backoff_until: Optional[datetime] = None
    
    def can_proceed(self) -> bool:
        now = datetime.now()
        
        # Check backoff
        if self.backoff_until and now < self.backoff_until:
            return False
        
        # Clean old requests
        cutoff = now.timestamp() - self.window_seconds
        self.requests = [r for r in self.requests if r.timestamp() > cutoff]
        
        return len(self.requests) < self.max_requests
    
    def record_request(self):
        self.requests.append(datetime.now())
    
    def trigger_backoff(self, seconds: int = 30):
        from datetime import timedelta
        self.backoff_until = datetime.now() + timedelta(seconds=seconds)
        logger.warning(f"Rate limit exceeded. Backoff for {seconds}s")


class BhulekService:
    """
    Mock Bhulekh Integration
    - LRU cache for land records
    - Rate limiting with exponential backoff
    - Developer mode for raw responses
    """
    
    def __init__(self):
        self.records: Dict[str, LandRecord] = {}
        self.rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
        self.developer_mode = False
        self._load_records()
    
    def _load_records(self):
        """Load land records from JSON file"""
        data_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "data", "land_records.json"
        )
        
        try:
            with open(data_path, 'r') as f:
                data = json.load(f)
                for r in data.get("records", []):
                    key = self._make_key(
                        r["state"], r["district"], 
                        r["tehsil"], r["village"], r["khasra"]
                    )
                    self.records[key] = LandRecord(**r)
            logger.info(f"Loaded {len(self.records)} land records")
        except Exception as e:
            logger.error(f"Failed to load records: {e}")
    
    def _make_key(self, state: str, district: str, tehsil: str, 
                  village: str, khasra: str) -> str:
        """Create lookup key from location details"""
        return f"{state.lower()}:{district.lower()}:{tehsil.lower()}:{village.lower()}:{khasra.lower()}"
    
    @lru_cache(maxsize=100)
    def _cached_lookup(self, key: str) -> Optional[Dict]:
        """LRU cached lookup"""
        record = self.records.get(key)
        if record:
            return record.to_dict()
        return None
    
    async def verify_land_record(
        self,
        state: str,
        district: str,
        tehsil: str,
        village: str,
        khasra: str,
        claimed_owner: Optional[str] = None,
        claimed_area: Optional[float] = None,
    ) -> VerificationResult:
        """
        Verify land record against Bhulekh database
        """
        import uuid
        
        # Check rate limit
        if not self.rate_limiter.can_proceed():
            return VerificationResult(
                status=VerificationStatus.ERROR,
                record=None,
                confidence=0,
                discrepancies=["Rate limit exceeded. Please try again later."],
                verification_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
            )
        
        self.rate_limiter.record_request()
        
        # Simulate API latency
        await asyncio.sleep(random.uniform(0.2, 0.8))
        
        # Lookup record
        key = self._make_key(state, district, tehsil, village, khasra)
        record_dict = self._cached_lookup(key)
        
        raw_response = {
            "api": "bhulekh_mock",
            "request": {"state": state, "district": district, 
                       "tehsil": tehsil, "village": village, "khasra": khasra},
            "cache_hit": key in self._cached_lookup.cache_info()._asdict().get('hits', 0),
        } if self.developer_mode else None
        
        if not record_dict:
            return VerificationResult(
                status=VerificationStatus.NOT_FOUND,
                record=None,
                confidence=0,
                discrepancies=["Land record not found in database"],
                verification_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                raw_response=raw_response,
            )
        
        record = LandRecord(**record_dict)
        discrepancies = []
        confidence = 1.0
        
        # Check owner match
        if claimed_owner:
            if claimed_owner.lower() != record.owner.lower():
                discrepancies.append(
                    f"Owner mismatch: claimed '{claimed_owner}', actual '{record.owner}'"
                )
                confidence -= 0.4
        
        # Check area match
        if claimed_area:
            diff = abs(claimed_area - record.area_acres)
            if diff > 0.5:
                discrepancies.append(
                    f"Area mismatch: claimed {claimed_area} acres, actual {record.area_acres} acres"
                )
                confidence -= 0.3
        
        # Check encumbrances
        if record.encumbrances and record.encumbrances != "None":
            discrepancies.append(f"Encumbrance found: {record.encumbrances}")
            confidence -= 0.2
        
        # Determine status
        if not discrepancies:
            status = VerificationStatus.VERIFIED
        elif confidence > 0.5:
            status = VerificationStatus.PARTIAL_MATCH
        else:
            status = VerificationStatus.DISCREPANCY
        
        if raw_response:
            raw_response["response"] = record_dict
            raw_response["cache_info"] = str(self._cached_lookup.cache_info())
        
        return VerificationResult(
            status=status,
            record=record,
            confidence=max(0, confidence),
            discrepancies=discrepancies,
            verification_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            raw_response=raw_response,
        )
    
    def set_developer_mode(self, enabled: bool):
        """Toggle developer mode for raw API responses"""
        self.developer_mode = enabled
        logger.info(f"Developer mode: {'ON' if enabled else 'OFF'}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        info = self._cached_lookup.cache_info()
        return {
            "hits": info.hits,
            "misses": info.misses,
            "maxsize": info.maxsize,
            "currsize": info.currsize,
            "hit_rate": info.hits / (info.hits + info.misses) if (info.hits + info.misses) > 0 else 0,
        }
    
    def clear_cache(self):
        """Clear LRU cache"""
        self._cached_lookup.cache_clear()
        logger.info("Cache cleared")
    
    def search_records(self, state: str = None, district: str = None,
                       owner: str = None, limit: int = 10) -> List[LandRecord]:
        """Search records by criteria"""
        results = []
        for record in self.records.values():
            if state and record.state.lower() != state.lower():
                continue
            if district and record.district.lower() != district.lower():
                continue
            if owner and owner.lower() not in record.owner.lower():
                continue
            results.append(record)
            if len(results) >= limit:
                break
        return results


# Singleton
_bhulekh_service: Optional[BhulekService] = None

def get_bhulekh_service() -> BhulekService:
    global _bhulekh_service
    if _bhulekh_service is None:
        _bhulekh_service = BhulekService()
    return _bhulekh_service
