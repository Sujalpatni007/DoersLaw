"""
DOER Platform - Document Verification Service

Cross-references OCR-extracted data against land records.
Detects discrepancies and generates verification reports.

SEVERITY LEVELS:
- CRITICAL: Owner name mismatch, survey number not found
- WARNING: Area differs by >10%, encumbrances found
- INFO: Minor variations, additional information

PRODUCTION UPGRADES:
- Use fuzzy matching for names (Levenshtein distance)
- Implement confidence scoring
- Add machine learning for fraud detection
- Generate PDF verification reports
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
import re


class DiscrepancySeverity(str, Enum):
    """Severity levels for discrepancies."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Discrepancy:
    """Represents a single discrepancy found during verification."""
    field: str
    severity: DiscrepancySeverity
    message: str
    extracted_value: Optional[str]
    expected_value: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "severity": self.severity.value,
            "message": self.message,
            "extracted_value": self.extracted_value,
            "expected_value": self.expected_value
        }


@dataclass
class VerificationReport:
    """Complete verification report for a document."""
    document_id: int
    case_id: int
    verified_at: str
    is_verified: bool
    overall_status: str  # verified, issues_found, not_verifiable
    matched_record: Optional[Dict[str, Any]]
    discrepancies: List[Discrepancy] = field(default_factory=list)
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "case_id": self.case_id,
            "verified_at": self.verified_at,
            "is_verified": self.is_verified,
            "overall_status": self.overall_status,
            "matched_record": self.matched_record,
            "discrepancies": [d.to_dict() for d in self.discrepancies],
            "summary": self.summary,
            "critical_count": sum(1 for d in self.discrepancies if d.severity == DiscrepancySeverity.CRITICAL),
            "warning_count": sum(1 for d in self.discrepancies if d.severity == DiscrepancySeverity.WARNING),
            "info_count": sum(1 for d in self.discrepancies if d.severity == DiscrepancySeverity.INFO)
        }


class VerificationService:
    """
    Verify extracted document data against land records.
    """
    
    def __init__(self):
        """Initialize the verification service."""
        from app.services.land_records import get_land_records_service
        self.land_records = get_land_records_service()
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison."""
        if not name:
            return ""
        # Remove common titles and normalize
        name = name.lower().strip()
        name = re.sub(r'\b(shri|smt|mr|mrs|ms|late|dr)\b\.?\s*', '', name)
        name = re.sub(r'\s+', ' ', name)
        return name.strip()
    
    def _compare_names(self, name1: str, name2: str) -> float:
        """
        Compare two names and return similarity score (0-1).
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Similarity score
        """
        n1 = self._normalize_name(name1)
        n2 = self._normalize_name(name2)
        
        if not n1 or not n2:
            return 0.0
        
        # Simple word overlap comparison
        words1 = set(n1.split())
        words2 = set(n2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _compare_areas(self, extracted: float, official: float, tolerance: float = 0.1) -> tuple:
        """
        Compare extracted area with official record.
        
        Args:
            extracted: Extracted area value
            official: Official record area
            tolerance: Acceptable difference ratio (default 10%)
            
        Returns:
            Tuple of (is_match, difference_ratio)
        """
        if official == 0:
            return False, 1.0
        
        diff_ratio = abs(extracted - official) / official
        is_match = diff_ratio <= tolerance
        
        return is_match, diff_ratio
    
    def verify_document(
        self,
        document_id: int,
        case_id: int,
        extracted_data: Dict[str, Any]
    ) -> VerificationReport:
        """
        Verify extracted document data against land records.
        
        Args:
            document_id: Database document ID
            case_id: Associated case ID
            extracted_data: OCR-extracted structured data
            
        Returns:
            VerificationReport with discrepancies
        """
        discrepancies = []
        matched_record = None
        
        # Try to find matching land record
        survey_numbers = extracted_data.get("survey_numbers", [])
        khasra_numbers = extracted_data.get("khasra_numbers", [])
        owner_names = extracted_data.get("owner_names", [])
        
        # Search by survey number first
        for survey_num in survey_numbers:
            matched_record = self.land_records.search_by_survey_number(survey_num)
            if matched_record:
                break
        
        # Try khasra number if no match
        if not matched_record:
            for khasra_num in khasra_numbers:
                matched_record = self.land_records.search_by_khasra(khasra_num)
                if matched_record:
                    break
        
        # Try owner name if still no match
        if not matched_record and owner_names:
            for owner in owner_names:
                results = self.land_records.search_by_owner(owner)
                if results:
                    matched_record = results[0]
                    break
        
        # If no record found
        if not matched_record:
            return VerificationReport(
                document_id=document_id,
                case_id=case_id,
                verified_at=datetime.utcnow().isoformat(),
                is_verified=False,
                overall_status="not_verifiable",
                matched_record=None,
                discrepancies=[
                    Discrepancy(
                        field="land_record",
                        severity=DiscrepancySeverity.CRITICAL,
                        message="No matching land record found in the database",
                        extracted_value=f"Survey: {survey_numbers}, Khasra: {khasra_numbers}",
                        expected_value=None
                    )
                ],
                summary="Could not find a matching land record. Please verify the document details manually."
            )
        
        # Verify owner name
        official_owner = matched_record.get("owner_name", "")
        official_owner_hindi = matched_record.get("owner_name_hindi", "")
        
        best_name_match = 0.0
        matched_owner = None
        
        for extracted_owner in owner_names:
            score_en = self._compare_names(extracted_owner, official_owner)
            score_hi = self._compare_names(extracted_owner, official_owner_hindi) if official_owner_hindi else 0
            score = max(score_en, score_hi)
            
            if score > best_name_match:
                best_name_match = score
                matched_owner = extracted_owner
        
        if best_name_match < 0.5:
            discrepancies.append(Discrepancy(
                field="owner_name",
                severity=DiscrepancySeverity.CRITICAL,
                message="Owner name does not match land records",
                extracted_value=", ".join(owner_names) if owner_names else "Not found",
                expected_value=official_owner
            ))
        elif best_name_match < 0.8:
            discrepancies.append(Discrepancy(
                field="owner_name",
                severity=DiscrepancySeverity.WARNING,
                message=f"Owner name partially matches (similarity: {best_name_match:.0%})",
                extracted_value=matched_owner,
                expected_value=official_owner
            ))
        
        # Verify area
        area_measurements = extracted_data.get("area_measurements", [])
        official_area_acres = matched_record.get("area_acres", 0)
        official_area_bigha = matched_record.get("area_bigha")
        
        area_verified = False
        for area in area_measurements:
            extracted_value = area.get("value", 0)
            unit = area.get("unit", "")
            
            # Convert to acres for comparison
            if unit == "acres":
                compare_value = extracted_value
            elif unit == "bigha" and official_area_bigha:
                # Compare directly with bigha
                is_match, diff = self._compare_areas(extracted_value, official_area_bigha)
                if is_match:
                    area_verified = True
                    break
                continue
            elif unit == "hectares":
                compare_value = extracted_value * 2.471
            elif unit == "sq_ft":
                compare_value = extracted_value / 43560
            else:
                continue
            
            is_match, diff = self._compare_areas(compare_value, official_area_acres)
            if is_match:
                area_verified = True
                break
            elif diff < 0.25:  # Within 25%
                discrepancies.append(Discrepancy(
                    field="area",
                    severity=DiscrepancySeverity.WARNING,
                    message=f"Area differs by {diff:.0%} from official records",
                    extracted_value=f"{extracted_value} {unit}",
                    expected_value=f"{official_area_acres} acres"
                ))
                area_verified = True
                break
        
        if not area_verified and area_measurements:
            discrepancies.append(Discrepancy(
                field="area",
                severity=DiscrepancySeverity.WARNING,
                message="Extracted area does not match official records",
                extracted_value=str(area_measurements),
                expected_value=f"{official_area_acres} acres"
            ))
        
        # Check for encumbrances
        encumbrances = matched_record.get("encumbrances", [])
        if encumbrances:
            discrepancies.append(Discrepancy(
                field="encumbrances",
                severity=DiscrepancySeverity.WARNING,
                message="Land has recorded encumbrances",
                extracted_value=None,
                expected_value=", ".join(encumbrances)
            ))
        
        # Add info about the match
        discrepancies.append(Discrepancy(
            field="record_match",
            severity=DiscrepancySeverity.INFO,
            message=f"Matched with land record: {matched_record.get('survey_number')}",
            extracted_value=None,
            expected_value=f"{matched_record.get('village')}, {matched_record.get('district')}"
        ))
        
        # Determine overall status
        critical_count = sum(1 for d in discrepancies if d.severity == DiscrepancySeverity.CRITICAL)
        warning_count = sum(1 for d in discrepancies if d.severity == DiscrepancySeverity.WARNING)
        
        if critical_count > 0:
            overall_status = "issues_found"
            is_verified = False
            summary = f"Found {critical_count} critical issue(s) that require attention."
        elif warning_count > 0:
            overall_status = "verified_with_warnings"
            is_verified = True
            summary = f"Document verified with {warning_count} warning(s)."
        else:
            overall_status = "verified"
            is_verified = True
            summary = "Document successfully verified against land records."
        
        return VerificationReport(
            document_id=document_id,
            case_id=case_id,
            verified_at=datetime.utcnow().isoformat(),
            is_verified=is_verified,
            overall_status=overall_status,
            matched_record=matched_record,
            discrepancies=discrepancies,
            summary=summary
        )
    
    def generate_case_verification_report(
        self,
        case_id: int,
        document_extractions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a complete verification report for all case documents.
        
        Args:
            case_id: Case ID
            document_extractions: List of {document_id, extracted_data}
            
        Returns:
            Complete verification report
        """
        reports = []
        
        for doc in document_extractions:
            doc_id = doc.get("document_id", 0)
            extracted_data = doc.get("extracted_data", {})
            
            report = self.verify_document(doc_id, case_id, extracted_data)
            reports.append(report.to_dict())
        
        # Aggregate results
        total_critical = sum(r.get("critical_count", 0) for r in reports)
        total_warnings = sum(r.get("warning_count", 0) for r in reports)
        all_verified = all(r.get("is_verified", False) for r in reports)
        
        return {
            "case_id": case_id,
            "generated_at": datetime.utcnow().isoformat(),
            "total_documents": len(reports),
            "all_verified": all_verified,
            "total_critical_issues": total_critical,
            "total_warnings": total_warnings,
            "document_reports": reports,
            "recommendation": self._get_recommendation(total_critical, total_warnings, len(reports))
        }
    
    def _get_recommendation(self, critical: int, warnings: int, doc_count: int) -> str:
        """Generate a recommendation based on verification results."""
        if doc_count == 0:
            return "No documents to verify. Please upload relevant land documents."
        
        if critical > 0:
            return (
                f"ATTENTION REQUIRED: Found {critical} critical issue(s). "
                "Please verify document authenticity and consult with a legal expert."
            )
        elif warnings > 0:
            return (
                f"Documents verified with {warnings} warning(s). "
                "Review the warnings and obtain clarification if needed."
            )
        else:
            return "All documents successfully verified. Proceed with case processing."


# Singleton instance
_service: Optional[VerificationService] = None


def get_verification_service() -> VerificationService:
    """Get or create the verification service instance."""
    global _service
    if _service is None:
        _service = VerificationService()
    return _service
