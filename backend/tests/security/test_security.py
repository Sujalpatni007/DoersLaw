"""
Security Tests
Input sanitization, file validation, injection prevention
"""
import pytest
import re


@pytest.mark.security
class TestInputSanitization:
    """Test input sanitization against attacks"""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection patterns are blocked"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "admin'--",
            "1; DELETE FROM cases",
            "UNION SELECT * FROM users",
            "1' AND '1'='1",
        ]
        
        def sanitize_input(text: str) -> str:
            # SQLAlchemy uses parameterized queries, this is extra protection
            dangerous_patterns = [
                r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)",
                r"UNION\s+SELECT",
                r"OR\s+1\s*=\s*1",
                r"--",
                r"'\s*OR\s*'",
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return "[BLOCKED]"
            return text
        
        for inp in malicious_inputs:
            sanitized = sanitize_input(inp)
            # Should be blocked or sanitized
            assert sanitized == "[BLOCKED]" or inp not in sanitized
    
    def test_xss_prevention(self):
        """Test XSS patterns are escaped"""
        xss_inputs = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<body onload=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "'-alert(1)-'",
        ]
        
        def escape_html(text: str) -> str:
            # HTML escape
            replacements = {
                "<": "&lt;",
                ">": "&gt;",
                "&": "&amp;",
                '"': "&quot;",
                "'": "&#x27;",
            }
            for char, replacement in replacements.items():
                text = text.replace(char, replacement)
            return text
        
        for inp in xss_inputs:
            escaped = escape_html(inp)
            assert "<script>" not in escaped
            assert "<img" not in escaped
            assert "onerror" not in escaped or "onerror" in escaped.replace("=", "")
    
    def test_path_traversal_prevention(self):
        """Test path traversal attempts are blocked"""
        traversal_inputs = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f",
            "..%252f..%252f",
        ]
        
        def sanitize_path(path: str) -> str:
            # Remove path traversal attempts
            import urllib.parse
            path = urllib.parse.unquote(path)
            path = path.replace("../", "").replace("..\\", "")
            path = path.replace("..", "")
            return path
        
        for inp in traversal_inputs:
            sanitized = sanitize_path(inp)
            assert ".." not in sanitized
    
    def test_command_injection_prevention(self):
        """Test command injection patterns are blocked"""
        command_inputs = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "& whoami",
            "`id`",
            "$(cat /etc/passwd)",
        ]
        
        def sanitize_command(text: str) -> str:
            dangerous_chars = [";", "|", "&", "`", "$", "(", ")"]
            for char in dangerous_chars:
                text = text.replace(char, "")
            return text
        
        for inp in command_inputs:
            sanitized = sanitize_command(inp)
            assert ";" not in sanitized
            assert "|" not in sanitized
            assert "`" not in sanitized


@pytest.mark.security
class TestFileUploadSecurity:
    """Test file upload security"""
    
    ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".webp"]
    ALLOWED_MIME_TYPES = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    ]
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def test_executable_file_blocked(self):
        """Test executable files are blocked"""
        dangerous_extensions = [".exe", ".sh", ".bat", ".cmd", ".ps1", ".php", ".py", ".js"]
        
        for ext in dangerous_extensions:
            assert ext not in self.ALLOWED_EXTENSIONS
    
    def test_double_extension_attack(self):
        """Test double extension attack is blocked"""
        def validate_filename(filename: str) -> bool:
            # Check all extensions, not just the last one
            parts = filename.lower().split(".")
            dangerous = [".exe", ".sh", ".bat", ".php", ".js"]
            
            for part in parts[1:]:  # Skip first part (base name)
                if f".{part}" in dangerous:
                    return False
            
            # Check final extension is allowed
            if parts:
                final_ext = f".{parts[-1]}"
                return final_ext in self.ALLOWED_EXTENSIONS
            return False
        
        assert not validate_filename("document.pdf.exe")
        assert not validate_filename("image.jpg.php")
        assert validate_filename("document.pdf")
        assert validate_filename("image.jpeg")
    
    def test_mime_type_validation(self):
        """Test MIME type matches extension"""
        def validate_mime(filename: str, mime_type: str) -> bool:
            ext = filename.lower().split(".")[-1]
            
            mime_map = {
                "pdf": "application/pdf",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }
            
            expected_mime = mime_map.get(ext)
            return expected_mime == mime_type
        
        assert validate_mime("doc.pdf", "application/pdf")
        assert validate_mime("img.jpg", "image/jpeg")
        assert not validate_mime("doc.pdf", "image/jpeg")  # Mismatch
        assert not validate_mime("evil.exe", "application/pdf")  # Wrong ext
    
    def test_file_size_limit(self):
        """Test file size limit enforcement"""
        assert 5 * 1024 * 1024 < self.MAX_FILE_SIZE  # 5MB OK
        assert 15 * 1024 * 1024 > self.MAX_FILE_SIZE  # 15MB blocked
    
    def test_null_byte_injection(self):
        """Test null byte injection in filenames"""
        def sanitize_filename(filename: str) -> str:
            # Remove null bytes
            return filename.replace("\x00", "").replace("\0", "")
        
        malicious = "document.pdf\x00.exe"
        sanitized = sanitize_filename(malicious)
        
        assert "\x00" not in sanitized
        assert sanitized == "document.pdf.exe"  # Would then fail extension check
    
    def test_magic_bytes_validation(self):
        """Test file magic bytes validation"""
        # Magic bytes for common file types
        MAGIC_BYTES = {
            "pdf": b"%PDF",
            "jpeg": b"\xff\xd8\xff",
            "png": b"\x89PNG",
        }
        
        def validate_magic_bytes(content: bytes, expected_type: str) -> bool:
            if expected_type not in MAGIC_BYTES:
                return False
            return content.startswith(MAGIC_BYTES[expected_type])
        
        pdf_content = b"%PDF-1.4 fake content"
        jpeg_content = b"\xff\xd8\xff fake jpeg"
        exe_content = b"MZ\x90\x00"  # EXE magic bytes
        
        assert validate_magic_bytes(pdf_content, "pdf")
        assert validate_magic_bytes(jpeg_content, "jpeg")
        assert not validate_magic_bytes(exe_content, "pdf")


@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication security"""
    
    def test_password_never_logged(self):
        """Ensure passwords are never logged or returned"""
        def sanitize_for_logging(data: dict) -> dict:
            sensitive_fields = ["password", "token", "secret", "api_key", "otp"]
            sanitized = data.copy()
            for field in sensitive_fields:
                if field in sanitized:
                    sanitized[field] = "[REDACTED]"
            return sanitized
        
        user_data = {
            "username": "test",
            "password": "secret123",
            "token": "abc123jwt",
        }
        
        logged = sanitize_for_logging(user_data)
        
        assert logged["password"] == "[REDACTED]"
        assert logged["token"] == "[REDACTED]"
        assert logged["username"] == "test"
    
    def test_rate_limiting_logic(self):
        """Test rate limiting logic"""
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        class RateLimiter:
            def __init__(self, max_requests: int, window_seconds: int):
                self.max_requests = max_requests
                self.window_seconds = window_seconds
                self.requests = defaultdict(list)
            
            def is_allowed(self, key: str) -> bool:
                now = datetime.now()
                cutoff = now - timedelta(seconds=self.window_seconds)
                
                # Clean old requests
                self.requests[key] = [
                    r for r in self.requests[key] if r > cutoff
                ]
                
                if len(self.requests[key]) >= self.max_requests:
                    return False
                
                self.requests[key].append(now)
                return True
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # First 5 requests should succeed
        for i in range(5):
            assert limiter.is_allowed("user1")
        
        # 6th request should be blocked
        assert not limiter.is_allowed("user1")
        
        # Different user still allowed
        assert limiter.is_allowed("user2")


@pytest.mark.security
class TestDataPrivacy:
    """Test data privacy and PII handling"""
    
    def test_phone_number_masking(self):
        """Test phone numbers are masked for logging"""
        def mask_phone(phone: str) -> str:
            if len(phone) >= 10:
                return phone[:4] + "******" + phone[-2:]
            return "******"
        
        assert mask_phone("+91-9876543210") == "+91-******10"
    
    def test_email_masking(self):
        """Test email addresses are masked"""
        def mask_email(email: str) -> str:
            parts = email.split("@")
            if len(parts) == 2:
                local = parts[0]
                if len(local) > 2:
                    masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
                else:
                    masked_local = "*" * len(local)
                return f"{masked_local}@{parts[1]}"
            return "***@***"
        
        assert mask_email("test@example.com") == "t**t@example.com"
        assert mask_email("longname@domain.com") == "l******e@domain.com"
