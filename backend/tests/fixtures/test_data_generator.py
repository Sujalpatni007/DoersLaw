"""
Test Data Generator
Creates realistic village scenarios for QA testing
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List
import uuid
import json


class VillageScenarioGenerator:
    """
    Generates realistic village dispute scenarios for QA testing
    """
    
    def __init__(self):
        self.states = {
            "Maharashtra": {
                "districts": ["Pune", "Mumbai", "Nashik", "Nagpur", "Satara"],
                "villages": ["Lohegaon", "Wagholi", "Paud", "Vani", "Baramati"],
                "surnames": ["Patil", "Deshmukh", "Jadhav", "Pawar", "Bhosale"],
                "first_names": ["Ramesh", "Sunita", "Anil", "Priya", "Mohan"],
            },
            "Uttar Pradesh": {
                "districts": ["Varanasi", "Lucknow", "Agra", "Kanpur"],
                "villages": ["Sarnath", "Kakori", "Sikandra", "Bithoor"],
                "surnames": ["Singh", "Yadav", "Sharma", "Verma", "Mishra"],
                "first_names": ["Krishna", "Sunita", "Ram", "Geeta", "Mohan"],
            },
            "Karnataka": {
                "districts": ["Bangalore", "Mysore", "Hubli", "Mangalore"],
                "villages": ["Jigani", "Bommasandra", "Hullahalli", "Hunsur"],
                "surnames": ["Reddy", "Gowda", "Rao", "Naidu", "Shetty"],
                "first_names": ["Venkat", "Lakshmi", "Krishna", "Savitha", "Ravi"],
            },
            "Tamil Nadu": {
                "districts": ["Chennai", "Coimbatore", "Madurai", "Salem"],
                "villages": ["Chromepet", "Pallavaram", "Karamadai", "Kottampatti"],
                "surnames": ["Murugan", "Selvam", "Saravanan", "Pandian", "Kumar"],
                "first_names": ["Murugan", "Lakshmi", "Saravanan", "Meena", "Rajan"],
            },
        }
        
        self.case_types = [
            ("boundary_dispute", "Boundary stones moved or disputed", ["survey_map", "land_record"]),
            ("inheritance", "Ancestral property division dispute", ["death_certificate", "will", "land_record"]),
            ("encroachment", "Illegal occupation of land", ["land_record", "photographs", "police_complaint"]),
            ("ownership_dispute", "Ownership claims conflict", ["sale_deed", "land_record", "tax_receipts"]),
            ("mutation", "Name transfer after death/sale", ["death_certificate", "land_record", "application"]),
        ]
        
        self.dispute_templates = [
            "After father's death, {party1} and {party2} dispute inherited {area} acre land in {village}",
            "{party1} claims {party2} moved boundary stones, encroaching on {area} acres",
            "{party1} found unauthorized construction by {party2} on vacant plot",
            "{party1} and {party2} both claim ownership of {area} acre plot after sale dispute",
            "{party1} unable to get mutation done after purchasing land from {party2}",
        ]
    
    def generate_person(self, state: str = None) -> Dict:
        """Generate a realistic person"""
        if not state:
            state = random.choice(list(self.states.keys()))
        
        state_data = self.states[state]
        
        return {
            "id": str(uuid.uuid4()),
            "name": f"{random.choice(state_data['first_names'])} {random.choice(state_data['surnames'])}",
            "phone": f"+91-{random.randint(9000000000, 9999999999)}",
            "village": random.choice(state_data["villages"]),
            "district": random.choice(state_data["districts"]),
            "state": state,
        }
    
    def generate_land_record(self, state: str = None) -> Dict:
        """Generate a realistic land record"""
        if not state:
            state = random.choice(list(self.states.keys()))
        
        state_data = self.states[state]
        
        return {
            "state": state,
            "district": random.choice(state_data["districts"]),
            "tehsil": random.choice(state_data["districts"]),  # Simplified
            "village": random.choice(state_data["villages"]),
            "khasra": f"{random.randint(100, 999)}/{random.randint(1, 9)}",
            "owner": f"{random.choice(state_data['first_names'])} {random.choice(state_data['surnames'])}",
            "area_acres": round(random.uniform(0.5, 10.0), 2),
            "cultivation": random.choice(["Agricultural", "Residential", "Commercial", "Barren"]),
            "encumbrances": random.choice(["None", "Bank Mortgage", "Court Stay", "None", "None"]),
        }
    
    def generate_dispute_scenario(self) -> Dict:
        """Generate a complete dispute scenario"""
        state = random.choice(list(self.states.keys()))
        
        petitioner = self.generate_person(state)
        respondent = self.generate_person(state)
        land = self.generate_land_record(state)
        
        case_type, description_template, required_docs = random.choice(self.case_types)
        
        template = random.choice(self.dispute_templates)
        description = template.format(
            party1=petitioner["name"],
            party2=respondent["name"],
            area=land["area_acres"],
            village=land["village"],
        )
        
        days_ago = random.randint(1, 90)
        
        return {
            "id": f"CASE-{datetime.now().year}-{random.randint(10000, 99999)}",
            "title": f"{case_type.replace('_', ' ').title()} - {land['village']}",
            "description": description,
            "case_type": case_type,
            "status": random.choice(["intake", "verification", "analysis", "negotiation"]),
            "priority": random.choice(["normal", "normal", "normal", "urgent"]),
            "created_at": (datetime.now() - timedelta(days=days_ago)).isoformat(),
            "petitioner": petitioner,
            "respondent": respondent,
            "land_record": land,
            "required_documents": required_docs,
            "uploaded_documents": random.sample(required_docs, min(len(required_docs), random.randint(1, len(required_docs)))),
        }
    
    def generate_low_literacy_scenario(self) -> Dict:
        """Generate scenario for low-literacy user (voice-only)"""
        scenario = self.generate_dispute_scenario()
        
        scenario["user_profile"] = {
            "literacy_level": "low",
            "preferred_language": random.choice(["hi", "ta", "te", "mr"]),
            "interaction_mode": "voice",
            "needs_assistance": True,
        }
        
        # Voice interview simulation
        scenario["voice_inputs"] = [
            "मेरे पड़ोसी ने मेरी जमीन पर कब्जा कर लिया है",  # Hindi
            "नहीं, मेरे पास कागजात है",
            "हां, मुझे वकील से बात करनी है",
        ]
        
        return scenario
    
    def generate_complex_multi_party_scenario(self) -> Dict:
        """Generate complex multi-party dispute"""
        state = random.choice(list(self.states.keys()))
        
        parties = []
        for _ in range(random.randint(3, 6)):
            parties.append(self.generate_person(state))
        
        land = self.generate_land_record(state)
        land["area_acres"] = round(random.uniform(5, 20), 2)  # Larger land
        
        return {
            "id": f"CASE-{datetime.now().year}-{random.randint(10000, 99999)}",
            "title": f"Multi-Party Inheritance - {land['village']}",
            "description": f"Complex inheritance dispute involving {len(parties)} family members over {land['area_acres']} acres",
            "case_type": "inheritance",
            "status": "analysis",
            "priority": "normal",
            "complexity": "high",
            "parties": parties,
            "land_record": land,
            "relationships": [
                {"party1": parties[0]["id"], "party2": parties[1]["id"], "relation": "siblings"},
                {"party1": parties[0]["id"], "party2": parties[2]["id"], "relation": "cousins"},
            ],
            "sub_disputes": [
                {"between": [parties[0]["id"], parties[1]["id"]], "issue": "Main property division"},
                {"between": [parties[2]["id"], parties[3]["id"]] if len(parties) > 3 else [], "issue": "Well access rights"},
            ],
        }
    
    def generate_document_heavy_scenario(self) -> Dict:
        """Generate scenario with many documents"""
        scenario = self.generate_dispute_scenario()
        
        all_doc_types = [
            "land_record", "survey_map", "sale_deed", "tax_receipts",
            "mutation_record", "court_order", "death_certificate",
            "will", "photographs", "police_complaint", "bank_statement",
            "id_proof", "witness_statement", "land_survey_report",
        ]
        
        scenario["documents"] = []
        for doc_type in random.sample(all_doc_types, random.randint(8, 12)):
            scenario["documents"].append({
                "id": str(uuid.uuid4()),
                "type": doc_type,
                "filename": f"{doc_type}_{random.randint(1, 999)}.pdf",
                "size_kb": random.randint(100, 5000),
                "uploaded_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "ocr_status": random.choice(["completed", "completed", "processing", "failed"]),
                "verified": random.choice([True, True, False]),
            })
        
        return scenario
    
    def generate_urgent_escalation_scenario(self) -> Dict:
        """Generate urgent escalation scenario"""
        scenario = self.generate_dispute_scenario()
        
        scenario["priority"] = "urgent"
        scenario["escalation"] = {
            "reason": random.choice([
                "Physical altercation between parties",
                "Imminent illegal construction",
                "Threats reported",
                "Court deadline approaching",
            ]),
            "escalated_at": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
            "escalated_by": "system_auto",
            "sla_hours": 24,
            "assigned_senior": {
                "id": random.randint(100, 199),
                "name": f"Senior Adv. {random.choice(['Sharma', 'Kulkarni', 'Rao'])}",
            },
        }
        
        return scenario
    
    def generate_test_dataset(self, count: int = 50) -> List[Dict]:
        """Generate a complete test dataset"""
        dataset = []
        
        # Mix of scenario types
        for _ in range(int(count * 0.4)):  # 40% normal
            dataset.append(self.generate_dispute_scenario())
        
        for _ in range(int(count * 0.15)):  # 15% low literacy
            dataset.append(self.generate_low_literacy_scenario())
        
        for _ in range(int(count * 0.15)):  # 15% multi-party
            dataset.append(self.generate_complex_multi_party_scenario())
        
        for _ in range(int(count * 0.15)):  # 15% document heavy
            dataset.append(self.generate_document_heavy_scenario())
        
        for _ in range(int(count * 0.15)):  # 15% urgent
            dataset.append(self.generate_urgent_escalation_scenario())
        
        return dataset
    
    def export_to_json(self, count: int = 50, filepath: str = None) -> str:
        """Export test dataset to JSON file"""
        dataset = self.generate_test_dataset(count)
        
        if not filepath:
            filepath = "/tmp/doer_test_data.json"
        
        with open(filepath, 'w') as f:
            json.dump(dataset, f, indent=2, default=str)
        
        return filepath


# Convenience function
def generate_test_data(count: int = 50) -> List[Dict]:
    """Generate test data for QA"""
    generator = VillageScenarioGenerator()
    return generator.generate_test_dataset(count)


if __name__ == "__main__":
    generator = VillageScenarioGenerator()
    filepath = generator.export_to_json(50)
    print(f"Test data exported to: {filepath}")
