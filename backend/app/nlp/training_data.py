"""
DOER Platform - Synthetic Training Data for Intent Classification

Generates training data for the dispute classifier.
Includes examples in English and transliterated Hindi.

PRODUCTION UPGRADES:
- Use actual annotated legal documents
- Implement active learning for continuous improvement
- Add data augmentation techniques
"""

from typing import List, Tuple


# Dispute categories with descriptions
INTENT_CATEGORIES = {
    "ownership_dispute": "Disputes about who owns the land",
    "boundary_dispute": "Disagreements about land boundaries",
    "inheritance_dispute": "Conflicts over inherited property",
    "encroachment": "Illegal occupation of land",
    "title_issue": "Problems with land title/deed documents"
}


def generate_training_data() -> List[Tuple[str, str]]:
    """
    Generate synthetic training data for intent classification.
    
    Returns:
        List of (text, intent) tuples
    """
    training_data = []
    
    # Ownership Dispute Examples (50 samples)
    ownership_samples = [
        "The land belongs to my family but someone else claims it",
        "My neighbor is claiming ownership of my agricultural land",
        "Two parties are fighting over who owns this plot",
        "There is a dispute about land ownership between brothers",
        "The government says the land is theirs but we have documents",
        "Someone sold land that belongs to our family",
        "Multiple ownership claims on the same piece of land",
        "The property was sold twice by different people",
        "Fake documents were used to claim our land",
        "Ownership dispute over ancestral property",
        "Who is the real owner of this 5 acre farm",
        "Dispute between landlord and tenant over ownership",
        "My father's land was illegally transferred",
        "False ownership claim on my property",
        "Two deed holders for the same land parcel",
        "Someone forged documents to take my land",
        "Government denying our ownership rights",
        "Village land being claimed by private party",
        "Trust land ownership is being disputed",
        "Corporate claiming ownership of tribal land",
        "Mujhe apni zameen ka ownership chahiye",
        "Meri property par kisi aur ne claim kiya hai",
        "Zameen ka malik kaun hai dispute",
        "Land ownership ke papers galat hain",
        "Do log ek hi zameen claim kar rahe hain",
        "Property ke documents mein naam galat hai",
        "Mera land records mein naam nahi hai",
        "Puri zameen meri hai lekin kuch hissa disputed hai",
        "Ownership transfer mein fraud hua",
        "Government land ko private property bata rahe hain",
        "I am the legal owner but records show someone else",
        "Disputed ownership between cousins",
        "Agricultural land ownership conflict",
        "Residential plot ownership issue",
        "Joint ownership causing problems",
        "Partition dispute for family land",
        "Survey number shows different owner",
        "Patta not in my name despite being owner",
        "Land mutation dispute",
        "Revenue records dispute about ownership",
        "Who owns this commercial property",
        "Industrial land ownership unclear",
        "Heritage property ownership fight",
        "Charitable trust land being claimed",
        "Temple land ownership dispute",
        "Church property under dispute",
        "Waqf board land claim issue",
        "Forest land ownership problem",
        "Coastal land ownership dispute",
        "Mining land ownership conflict"
    ]
    
    # Boundary Dispute Examples (50 samples)
    boundary_samples = [
        "My neighbor has moved the boundary fence",
        "The wall between our properties is in wrong place",
        "Survey shows different boundary than what exists",
        "Neighbor built on my side of the land",
        "Boundary markers have been removed",
        "Dispute about where my land ends",
        "The compound wall encroaches my property",
        "Road construction changed our boundaries",
        "Canal construction affected land boundary",
        "Survey number boundaries don't match ground",
        "Neighbor claims 2 feet of my land",
        "Fencing dispute between adjacent plots",
        "Common wall ownership dispute",
        "Pathway between properties is disputed",
        "River changed course affecting boundaries",
        "Erosion changed the land boundary",
        "Mountain boundary dispute",
        "Forest edge boundary unclear",
        "Village boundaries overlap",
        "Taluka boundary affecting land claim",
        "Padosi ne hadd paar kar li hai",
        "Meri zameen ki boundary galat hai",
        "Deewar mere side mein aa gayi",
        "Survey mein alag boundary hai",
        "Bade ne zameen hadap li boundary change karke",
        "Kheti ki zameen ka haddi vivad",
        "Nala boundary dispute",
        "Sadak ne boundary badal di",
        "Khet ki mez dispute",
        "Boundary pillars hata diye gaye",
        "The survey is wrong about boundaries",
        "GPS coordinates don't match deed",
        "Physical boundary differs from records",
        "Neighbor's construction on boundary line",
        "Tree on boundary causing problems",
        "Water tank built on boundary",
        "Drain pipe on wrong side of boundary",
        "Parking area boundary dispute",
        "Gate opening on boundary wall",
        "Height of boundary wall disputed",
        "Compound wall ownership unclear",
        "Shared driveway boundary issue",
        "Farm boundary with government land",
        "Railway boundary dispute",
        "Highway boundary acquisition",
        "Airport land boundary issue",
        "Military area boundary problems",
        "Industrial zone boundary dispute",
        "SEZ boundary affecting property",
        "Smart city project boundary issues"
    ]
    
    # Inheritance Dispute Examples (50 samples)
    inheritance_samples = [
        "My father died and siblings are fighting over land",
        "Ancestral property division dispute",
        "Will was not followed properly",
        "Sister wants share in father's property",
        "Daughter denied inheritance rights",
        "Step children inheritance dispute",
        "Second wife claiming property",
        "Adopted child denied inheritance",
        "Hindu succession act dispute",
        "Muslim inheritance law dispute",
        "Christian inheritance fight",
        "Mother in law taking all property",
        "Father gave everything to one son",
        "Unequal partition of ancestral land",
        "Grandfather's land distribution issue",
        "Great grandfather's property dispute",
        "Joint family property partition",
        "HUF property distribution problem",
        "Karta misusing joint property",
        "Property given to one branch only",
        "Baap ki property ka jhagda",
        "Pitaji ke baad zameen ka batwara",
        "Bhai behno mein property dispute",
        "Pushtaini zameen ka vivad",
        "Wasiyat naam galat hai",
        "Mata ji ki property mein hissa chahiye",
        "Sautele bhai ko zyada mila",
        "Ladki ko property nahi di",
        "Hindu law ke hisab se partition",
        "Muslim law mein inheritance issue",
        "Father's will is being contested",
        "No will and family fighting",
        "Oral will dispute",
        "Registered will challenged",
        "Coerced will allegation",
        "Mental capacity at will time disputed",
        "Witness to will unavailable",
        "Will beneficiary died before testator",
        "Conditional bequest in will",
        "Life estate vs absolute estate dispute",
        "Widow's rights in husband's property",
        "Son in law claiming property",
        "Daughter in law inheritance rights",
        "Illegitimate child inheritance claim",
        "Missing heir suddenly appearing",
        "Presumption of death and inheritance",
        "NRI inheritance complications",
        "Foreign property inheritance",
        "Agricultural land inheritance by female",
        "Tenancy rights inheritance"
    ]
    
    # Encroachment Examples (50 samples)
    encroachment_samples = [
        "Someone has occupied my vacant land",
        "Squatters living on my property",
        "Neighbor extended his house on my land",
        "Illegal construction on my plot",
        "Slum developed on private property",
        "Government land encroached by builder",
        "Forest land encroachment",
        "Lake bed encroachment",
        "River bed encroachment",
        "Road side encroachment",
        "My property is being illegally used",
        "Unauthorized possession of land",
        "Trespassers refusing to leave",
        "Commercial use of encroached land",
        "Parking on my private property",
        "Storage on encroached land",
        "Shop built on footpath",
        "Residential colony on government land",
        "Temple built on private land",
        "Religious structure encroachment",
        "Meri zameen par kabza ho gaya",
        "Plot par jhuggi ban gayi",
        "Padosi ne meri zameen hadap li",
        "Khali zameen par construction",
        "Sarkari zameen par encroachment",
        "Mere khet mein dukan ban gayi",
        "Vacant plot par slum aa gaya",
        "Jungle zameen par kabza",
        "Nadi ke pass encroachment",
        "Government land par private construction",
        "Illegal occupation of property for 10 years",
        "Tenant not vacating and claiming ownership",
        "Adverse possession claim on my land",
        "Caretaker claiming property rights",
        "Servant quarters encroachment",
        "Watchman occupying land",
        "Driver quarters on my land",
        "Unauthorized cultivation on fallow land",
        "Grazing land being encroached",
        "Common area encroachment in society",
        "Staircase landing encroached",
        "Balcony extended illegally",
        "Parking spot encroached",
        "Garden area encroached",
        "Terrace encroachment",
        "Basement extended illegally",
        "Shop extension on footpath",
        "Factory encroaching nearby land",
        "Hotel using public land",
        "School built on encroached land"
    ]
    
    # Title Issue Examples (50 samples)
    title_samples = [
        "My property deed has wrong information",
        "Sale deed was never registered",
        "Title is not clear",
        "Property has mortgage issues",
        "Previous owner had loans on property",
        "Land records don't match deed",
        "Khata number is disputed",
        "Survey number incorrect in deed",
        "Property has legal notices",
        "Court case pending on property",
        "Title insurance claim",
        "Chain of title broken",
        "Missing link deed",
        "Gift deed challenged",
        "Settlement deed disputed",
        "Partition deed incorrect",
        "Power of attorney misused",
        "GPA sale is invalid",
        "Sub registrar refused registration",
        "Stamp duty evasion issue",
        "Property ke kagaz galat hain",
        "Registry nahi hui properly",
        "Deed mein naam galat hai",
        "Zameen par loan tha",
        "Purane malik ne fraud kiya",
        "Land records update nahi hai",
        "Khata mein galti hai",
        "Survey number match nahi karta",
        "Court stay hai property par",
        "Legal notice aaya hai",
        "Title search shows problems",
        "Encumbrance on property",
        "Lien on the land",
        "Charge registered on property",
        "Mortgage not discharged",
        "Bank NPA property",
        "SARFAESI action on property",
        "Attachment order on land",
        "Revenue recovery pending",
        "Tax arrears on property",
        "Conversion of land use issue",
        "Agricultural to non-agri pending",
        "NA order not obtained",
        "Building permission issue",
        "FSI violation",
        "Unauthorized construction",
        "Occupancy certificate missing",
        "Completion certificate not issued",
        "RERA registration pending",
        "Layout approval not taken"
    ]
    
    # Combine all data
    for text in ownership_samples:
        training_data.append((text, "ownership_dispute"))
    
    for text in boundary_samples:
        training_data.append((text, "boundary_dispute"))
    
    for text in inheritance_samples:
        training_data.append((text, "inheritance_dispute"))
    
    for text in encroachment_samples:
        training_data.append((text, "encroachment"))
    
    for text in title_samples:
        training_data.append((text, "title_issue"))
    
    return training_data


def get_training_texts_and_labels() -> Tuple[List[str], List[str]]:
    """
    Get training texts and labels as separate lists.
    
    Returns:
        Tuple of (texts, labels)
    """
    data = generate_training_data()
    texts = [item[0] for item in data]
    labels = [item[1] for item in data]
    return texts, labels
