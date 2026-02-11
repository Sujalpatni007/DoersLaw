"""
PDF Certificate Generator using ReportLab
Generates verification certificates for land records
"""

from datetime import datetime
from typing import Dict, Optional
import os
import uuid
import logging

logger = logging.getLogger("PDF_GENERATOR")

# Check if reportlab is available
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch, cm
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not installed. PDF generation will be simulated.")


class PDFCertificateGenerator:
    """
    Generates PDF verification certificates
    """
    
    def __init__(self):
        self.output_dir = "/tmp/doer_certificates"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Colors
        self.primary_color = HexColor("#1e40af") if REPORTLAB_AVAILABLE else None
        self.secondary_color = HexColor("#16a34a") if REPORTLAB_AVAILABLE else None
        self.text_color = HexColor("#1f2937") if REPORTLAB_AVAILABLE else None
    
    def generate_verification_certificate(
        self,
        verification_id: str,
        land_record: Dict,
        verification_status: str,
        confidence: float,
        discrepancies: list,
        user_name: str,
        case_id: str = None,
    ) -> str:
        """
        Generate land record verification certificate
        Returns path to generated PDF
        """
        if not REPORTLAB_AVAILABLE:
            logger.info(f"[PDF SIMULATION] Certificate for {verification_id}")
            return f"{self.output_dir}/{verification_id}_simulated.pdf"
        
        filename = f"{self.output_dir}/verification_{verification_id}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Header with logo
        c.setFillColor(self.primary_color)
        c.rect(0, height - 100, width, 100, fill=True)
        
        c.setFillColor(HexColor("#ffffff"))
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height - 50, "DOER Platform")
        c.setFont("Helvetica", 14)
        c.drawCentredString(width/2, height - 75, "Land Record Verification Certificate")
        
        # Certificate ID
        c.setFillColor(self.text_color)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, height - 130, f"Certificate ID: {verification_id}")
        c.drawRightString(width - 50, height - 130, f"Date: {datetime.now().strftime('%d %B %Y')}")
        
        # Status badge
        y = height - 170
        status_color = self.secondary_color if verification_status == "verified" else HexColor("#dc2626")
        c.setFillColor(status_color)
        c.roundRect(50, y - 30, 150, 35, 5, fill=True)
        c.setFillColor(HexColor("#ffffff"))
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(125, y - 18, verification_status.upper())
        
        # Confidence
        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 12)
        c.drawString(220, y - 15, f"Confidence Score: {int(confidence * 100)}%")
        
        # Land Record Details
        y -= 80
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Land Record Details")
        c.line(50, y - 5, width - 50, y - 5)
        
        y -= 30
        c.setFont("Helvetica", 11)
        details = [
            ("State", land_record.get("state", "N/A")),
            ("District", land_record.get("district", "N/A")),
            ("Tehsil", land_record.get("tehsil", "N/A")),
            ("Village", land_record.get("village", "N/A")),
            ("Khasra Number", land_record.get("khasra", "N/A")),
            ("Owner", land_record.get("owner", "N/A")),
            ("Area", f"{land_record.get('area_acres', 'N/A')} acres"),
            ("Cultivation Type", land_record.get("cultivation", "N/A")),
            ("Encumbrances", land_record.get("encumbrances", "None")),
        ]
        
        for label, value in details:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, f"{label}:")
            c.setFont("Helvetica", 10)
            c.drawString(180, y, str(value))
            y -= 20
        
        # Discrepancies
        if discrepancies:
            y -= 20
            c.setFillColor(HexColor("#dc2626"))
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "⚠ Discrepancies Found:")
            c.setFillColor(self.text_color)
            c.setFont("Helvetica", 10)
            for disc in discrepancies:
                y -= 18
                c.drawString(70, y, f"• {disc}")
        
        # Case reference
        if case_id:
            y -= 40
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, f"Associated Case: {case_id}")
        
        # Footer
        c.setFillColor(HexColor("#6b7280"))
        c.setFont("Helvetica", 8)
        c.drawCentredString(width/2, 60, "This certificate is digitally generated by DOER Platform")
        c.drawCentredString(width/2, 48, "For verification, visit doer-platform.gov.in/verify")
        c.drawCentredString(width/2, 36, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # QR placeholder
        c.rect(width - 100, 30, 60, 60)
        c.setFont("Helvetica", 6)
        c.drawCentredString(width - 70, 25, "Scan to verify")
        
        c.save()
        logger.info(f"📄 Certificate generated: {filename}")
        
        return filename
    
    def generate_court_fee_receipt(
        self,
        payment_id: str,
        transaction_id: str,
        amount: float,
        payment_type: str,
        user_name: str,
        case_id: str = None,
    ) -> str:
        """Generate court fee payment receipt"""
        if not REPORTLAB_AVAILABLE:
            logger.info(f"[PDF SIMULATION] Receipt for {payment_id}")
            return f"{self.output_dir}/{payment_id}_receipt_simulated.pdf"
        
        filename = f"{self.output_dir}/receipt_{payment_id}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Header
        c.setFillColor(self.primary_color)
        c.rect(0, height - 80, width, 80, fill=True)
        c.setFillColor(HexColor("#ffffff"))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height - 45, "PAYMENT RECEIPT")
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, height - 65, "DOER Platform - Digital Payment Gateway")
        
        # Receipt details
        y = height - 120
        c.setFillColor(self.text_color)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, f"Receipt No: {payment_id[:8].upper()}")
        c.drawRightString(width - 50, y, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
        
        y -= 50
        c.setFont("Helvetica", 11)
        fields = [
            ("Transaction ID", transaction_id),
            ("Payment Type", payment_type.replace("_", " ").title()),
            ("Payer Name", user_name),
            ("Case Reference", case_id or "N/A"),
        ]
        
        for label, value in fields:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, f"{label}:")
            c.setFont("Helvetica", 10)
            c.drawString(180, y, str(value))
            y -= 25
        
        # Amount box
        y -= 20
        c.setFillColor(self.secondary_color)
        c.roundRect(50, y - 40, width - 100, 50, 5, fill=True)
        c.setFillColor(HexColor("#ffffff"))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, y - 22, f"₹ {amount:,.2f}")
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, y - 38, "Amount Paid")
        
        # Status
        y -= 80
        c.setFillColor(self.text_color)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width/2, y, "✓ PAYMENT SUCCESSFUL")
        
        # Footer
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#6b7280"))
        c.drawCentredString(width/2, 50, "This is a computer-generated receipt and does not require signature")
        c.drawCentredString(width/2, 38, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        c.save()
        logger.info(f"🧾 Receipt generated: {filename}")
        
        return filename


# Singleton
_pdf_generator: Optional[PDFCertificateGenerator] = None

def get_pdf_generator() -> PDFCertificateGenerator:
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = PDFCertificateGenerator()
    return _pdf_generator
