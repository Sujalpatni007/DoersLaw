"""
DOER Platform - Mock Land Records Service

Simulates integration with Bhulekh/land registry APIs.
Uses JSON files for sample data during development.

FEATURES:
- Load records from local JSON files
- Search by survey number, khasra, owner name
- 20+ sample records across 3 states

PRODUCTION UPGRADES:
- Integrate with actual state Bhulekh APIs
- Implement caching with Redis
- Add rate limiting per state API
- Handle API failures gracefully
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class LandRecord:
    """Represents a land record from government database."""
    survey_number: str
    khasra_number: str
    owner_name: str
    owner_name_hindi: Optional[str]
    father_name: Optional[str]
    area_acres: float
    area_bigha: Optional[float]
    village: str
    tehsil: str
    district: str
    state: str
    land_type: str  # agricultural, residential, commercial
    mutation_date: Optional[str]
    encumbrances: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "survey_number": self.survey_number,
            "khasra_number": self.khasra_number,
            "owner_name": self.owner_name,
            "owner_name_hindi": self.owner_name_hindi,
            "father_name": self.father_name,
            "area_acres": self.area_acres,
            "area_bigha": self.area_bigha,
            "village": self.village,
            "tehsil": self.tehsil,
            "district": self.district,
            "state": self.state,
            "land_type": self.land_type,
            "mutation_date": self.mutation_date,
            "encumbrances": self.encumbrances
        }


# Sample land records for demo
SAMPLE_LAND_RECORDS = [
    # Maharashtra
    LandRecord("MH/PUN/101/1", "101/1", "Rajesh Kumar Patil", "राजेश कुमार पाटिल", "Suresh Patil", 2.5, None, "Wagholi", "Haveli", "Pune", "Maharashtra", "agricultural", "2020-05-15", []),
    LandRecord("MH/PUN/101/2", "101/2", "Sunita Devi Patil", "सुनीता देवी पाटिल", "Late Mahesh Patil", 1.25, None, "Wagholi", "Haveli", "Pune", "Maharashtra", "residential", "2021-08-20", []),
    LandRecord("MH/PUN/102/1", "102/1", "Amit Sharma", "अमित शर्मा", "Ramesh Sharma", 5.0, None, "Lohagaon", "Haveli", "Pune", "Maharashtra", "agricultural", "2019-03-10", ["Bank Mortgage - HDFC"]),
    LandRecord("MH/MUM/201/1", "201/1", "Priya Singh", "प्रिया सिंह", "Vikram Singh", 0.5, None, "Andheri", "Andheri", "Mumbai", "Maharashtra", "commercial", "2022-01-05", []),
    LandRecord("MH/MUM/201/2", "201/2", "Mohammad Ali Khan", "मोहम्मद अली खान", "Ibrahim Khan", 0.75, None, "Bandra", "Bandra", "Mumbai", "Maharashtra", "residential", "2018-11-25", []),
    LandRecord("MH/NGP/301/1", "301/1", "Ganesh Rao", "गणेश राव", "Venkat Rao", 10.0, None, "Kamptee", "Kamptee", "Nagpur", "Maharashtra", "agricultural", "2017-06-30", []),
    LandRecord("MH/NGP/301/2", "301/2", "Lakshmi Bai", "लक्ष्मी बाई", "Late Shyam Rao", 3.5, None, "Kamptee", "Kamptee", "Nagpur", "Maharashtra", "agricultural", "2019-09-12", ["Court Case Pending"]),
    
    # Uttar Pradesh
    LandRecord("UP/LKO/401/1", "401/1", "Ram Prasad Verma", "राम प्रसाद वर्मा", "Shiv Prasad Verma", 4.0, 16.0, "Chinhat", "Lucknow", "Lucknow", "Uttar Pradesh", "agricultural", "2020-02-28", []),
    LandRecord("UP/LKO/401/2", "401/2", "Geeta Devi", "गीता देवी", "Late Mohan Lal", 2.0, 8.0, "Chinhat", "Lucknow", "Lucknow", "Uttar Pradesh", "residential", "2021-04-15", []),
    LandRecord("UP/VNS/501/1", "501/1", "Anil Kumar Pandey", "अनिल कुमार पाण्डेय", "Brij Mohan Pandey", 6.0, 24.0, "Sarnath", "Varanasi", "Varanasi", "Uttar Pradesh", "agricultural", "2018-07-20", ["Revenue Dues Pending"]),
    LandRecord("UP/VNS/501/2", "501/2", "Kavita Singh", "कविता सिंह", "Rajendra Singh", 1.5, 6.0, "Ramnagar", "Varanasi", "Varanasi", "Uttar Pradesh", "residential", "2022-03-08", []),
    LandRecord("UP/AGR/601/1", "601/1", "Suresh Chandra", "सुरेश चंद्र", "Hari Chandra", 8.0, 32.0, "Fatehpur Sikri", "Agra", "Agra", "Uttar Pradesh", "agricultural", "2019-10-25", []),
    LandRecord("UP/AGR/601/2", "601/2", "Meena Kumari", "मीना कुमारी", "Ram Das", 3.0, 12.0, "Dayalbagh", "Agra", "Agra", "Uttar Pradesh", "residential", "2020-12-10", []),
    
    # Karnataka
    LandRecord("KA/BLR/701/1", "701/1", "Venkatesh Murthy", "वेंकटेश मूर्ति", "Narayana Murthy", 3.0, None, "Whitefield", "Bangalore East", "Bangalore", "Karnataka", "commercial", "2021-06-15", ["Bank Mortgage - SBI"]),
    LandRecord("KA/BLR/701/2", "701/2", "Lakshmi Narayana", "लक्ष्मी नारायण", "Krishna Murthy", 2.0, None, "Electronics City", "Bangalore South", "Bangalore", "Karnataka", "residential", "2020-09-30", []),
    LandRecord("KA/MYS/801/1", "801/1", "Ramakrishna Sharma", "रामकृष्ण शर्मा", "Gopal Sharma", 15.0, None, "Nanjangud", "Nanjangud", "Mysore", "Karnataka", "agricultural", "2018-04-12", []),
    LandRecord("KA/MYS/801/2", "801/2", "Savitri Devi", "सावित्री देवी", "Late Rajan", 4.5, None, "Hunsur", "Hunsur", "Mysore", "Karnataka", "agricultural", "2019-11-08", ["Family Dispute"]),
    LandRecord("KA/HUB/901/1", "901/1", "Basavaraj Patil", "बसवराज पाटिल", "Siddaramaiah", 12.0, None, "Hubli", "Hubli", "Hubli-Dharwad", "Karnataka", "agricultural", "2017-08-22", []),
    LandRecord("KA/HUB/901/2", "901/2", "Jayamma", "जयम्मा", "Late Hanumantappa", 5.0, None, "Dharwad", "Dharwad", "Hubli-Dharwad", "Karnataka", "residential", "2020-07-18", []),
    LandRecord("KA/BLR/702/1", "702/1", "Tech Solutions Pvt Ltd", "टेक सॉल्यूशंस प्रा. लि.", "N/A", 1.5, None, "Marathahalli", "Bangalore East", "Bangalore", "Karnataka", "commercial", "2022-02-14", []),
]


class LandRecordsService:
    """
    Mock Bhulekh API service for land record lookup.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the land records service.
        
        Args:
            data_dir: Directory for JSON data files
        """
        self.data_dir = Path(data_dir or Path(__file__).parent.parent.parent / "data" / "mock_land_records")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._records: Dict[str, LandRecord] = {}
        
        # Load or create sample data
        self._initialize_records()
    
    def _initialize_records(self):
        """Load records from files or use sample data."""
        # Index by survey number for quick lookup
        for record in SAMPLE_LAND_RECORDS:
            self._records[record.survey_number] = record
            # Also index by khasra for flexible lookup
            self._records[f"khasra_{record.khasra_number}"] = record
        
        # Save to JSON files for inspection
        self._save_sample_data()
    
    def _save_sample_data(self):
        """Save sample data to JSON files organized by state/district."""
        # Group by state and district
        by_state_district: Dict[str, Dict[str, List[Dict]]] = {}
        
        for record in SAMPLE_LAND_RECORDS:
            state_key = record.state.lower().replace(" ", "_")
            district_key = record.district.lower().replace(" ", "_")
            
            if state_key not in by_state_district:
                by_state_district[state_key] = {}
            if district_key not in by_state_district[state_key]:
                by_state_district[state_key][district_key] = []
            
            by_state_district[state_key][district_key].append(record.to_dict())
        
        # Save to files
        for state, districts in by_state_district.items():
            state_dir = self.data_dir / state
            state_dir.mkdir(parents=True, exist_ok=True)
            
            for district, records in districts.items():
                file_path = state_dir / f"{district}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(records, f, indent=2, ensure_ascii=False)
    
    def search_by_survey_number(self, survey_number: str) -> Optional[Dict[str, Any]]:
        """
        Search for a record by survey number.
        
        Args:
            survey_number: Full or partial survey number
            
        Returns:
            Land record if found
        """
        # Exact match
        if survey_number in self._records:
            return self._records[survey_number].to_dict()
        
        # Partial match
        for key, record in self._records.items():
            if survey_number in key or survey_number in record.survey_number:
                return record.to_dict()
        
        return None
    
    def search_by_khasra(self, khasra_number: str) -> Optional[Dict[str, Any]]:
        """Search for a record by khasra number."""
        key = f"khasra_{khasra_number}"
        if key in self._records:
            return self._records[key].to_dict()
        
        # Partial match
        for record in SAMPLE_LAND_RECORDS:
            if khasra_number in record.khasra_number:
                return record.to_dict()
        
        return None
    
    def search_by_owner(self, owner_name: str) -> List[Dict[str, Any]]:
        """
        Search for records by owner name.
        
        Args:
            owner_name: Full or partial owner name (English or Hindi)
            
        Returns:
            List of matching records
        """
        results = []
        search_lower = owner_name.lower()
        
        for record in SAMPLE_LAND_RECORDS:
            if (search_lower in record.owner_name.lower() or 
                (record.owner_name_hindi and owner_name in record.owner_name_hindi)):
                results.append(record.to_dict())
        
        return results
    
    def search_by_location(
        self,
        village: Optional[str] = None,
        district: Optional[str] = None,
        state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search records by location.
        
        Returns:
            List of matching records
        """
        results = []
        
        for record in SAMPLE_LAND_RECORDS:
            match = True
            
            if village and village.lower() not in record.village.lower():
                match = False
            if district and district.lower() not in record.district.lower():
                match = False
            if state and state.lower() not in record.state.lower():
                match = False
            
            if match:
                results.append(record.to_dict())
        
        return results
    
    def get_record(
        self,
        survey_number: Optional[str] = None,
        khasra_number: Optional[str] = None,
        owner_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific land record using various identifiers.
        
        Args:
            survey_number: Survey number to search
            khasra_number: Khasra number to search
            owner_name: Owner name to search
            
        Returns:
            First matching record or None
        """
        if survey_number:
            result = self.search_by_survey_number(survey_number)
            if result:
                return result
        
        if khasra_number:
            result = self.search_by_khasra(khasra_number)
            if result:
                return result
        
        if owner_name:
            results = self.search_by_owner(owner_name)
            if results:
                return results[0]
        
        return None
    
    def list_all_records(self) -> List[Dict[str, Any]]:
        """Get all sample records."""
        return [record.to_dict() for record in SAMPLE_LAND_RECORDS]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the records database."""
        states = set()
        districts = set()
        total_area = 0.0
        
        for record in SAMPLE_LAND_RECORDS:
            states.add(record.state)
            districts.add(record.district)
            total_area += record.area_acres
        
        return {
            "total_records": len(SAMPLE_LAND_RECORDS),
            "states": list(states),
            "district_count": len(districts),
            "total_area_acres": total_area
        }


# Singleton instance
_service: Optional[LandRecordsService] = None


def get_land_records_service() -> LandRecordsService:
    """Get or create the land records service instance."""
    global _service
    if _service is None:
        _service = LandRecordsService()
    return _service
