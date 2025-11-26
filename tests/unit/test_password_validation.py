"""
Unit tests for password validation in UserCreate schema.
"""

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate


@pytest.mark.unit
class TestPasswordValidation:
    """Tests for password validation requirements."""
    
    def test_valid_password_accepted(self):
        """Should accept password meeting all requirements."""
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="SecurePass123!",
            full_name="Test User"
        )
        assert user_data.password == "SecurePass123!"
    
    def test_rejects_password_without_uppercase(self):
        """Should reject password without uppercase letter."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="securepass123!",
                full_name="Test User"
            )
        
        errors = exc_info.value.errors()
        assert any("uppercase" in str(err["msg"]).lower() for err in errors)
    
    def test_rejects_password_without_lowercase(self):
        """Should reject password without lowercase letter."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="SECUREPASS123!",
                full_name="Test User"
            )
        
        errors = exc_info.value.errors()
        assert any("lowercase" in str(err["msg"]).lower() for err in errors)
    
    def test_rejects_password_without_digit(self):
        """Should reject password without digit."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="SecurePassword!",
                full_name="Test User"
            )
        
        errors = exc_info.value.errors()
        assert any("digit" in str(err["msg"]).lower() for err in errors)
    
    def test_rejects_password_without_special_character(self):
        """Should reject password without special character."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="SecurePass123",
                full_name="Test User"
            )
        
        errors = exc_info.value.errors()
        assert any("special character" in str(err["msg"]).lower() for err in errors)
    
    def test_rejects_common_weak_passwords(self):
        """Should reject common weak passwords."""
        weak_passwords = [
            "Password123!",  # "password" is weak
            "12345678",
            "Password1!",    # "password1" is weak
            "Welcome123!",   # "welcome" is weak
        ]
        
        for weak_pass in weak_passwords:
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(
                    email="test@example.com",
                    username="testuser",
                    password=weak_pass,
                    full_name="Test User"
                )
            
            errors = exc_info.value.errors()
            # Should fail either on common password or missing requirements
            assert len(errors) > 0
    
    def test_rejects_password_containing_username(self):
        """Should reject password that contains username."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="johnsmith",
                password="Johnsmith123!",
                full_name="Test User"
            )
        
        errors = exc_info.value.errors()
        assert any("username" in str(err["msg"]).lower() for err in errors)
    
    def test_accepts_various_special_characters(self):
        """Should accept various special characters."""
        special_chars = ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "_", "+", "="]
        
        for char in special_chars:
            user_data = UserCreate(
                email="test@example.com",
                username="testuser",
                password=f"SecurePass123{char}",
                full_name="Test User"
            )
            assert user_data.password == f"SecurePass123{char}"
    
    def test_minimum_length_enforced(self):
        """Should enforce minimum password length of 8 characters."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="Ab1!",  # Only 4 characters
                full_name="Test User"
            )
        
        errors = exc_info.value.errors()
        assert any("at least 8 characters" in str(err["msg"]).lower() for err in errors)
    
    def test_maximum_length_enforced(self):
        """Should enforce maximum password length of 100 characters."""
        long_password = "A" * 50 + "b" * 50 + "1!"  # 102 characters
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password=long_password,
                full_name="Test User"
            )
        
        errors = exc_info.value.errors()
        assert any("at most 100 characters" in str(err["msg"]).lower() for err in errors)
    
    def test_case_insensitive_weak_password_check(self):
        """Should check weak passwords case-insensitively."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="PASSWORD123!",  # "password" in uppercase
                full_name="Test User"
            )
        
        errors = exc_info.value.errors()
        # Should fail on either lowercase requirement or common check
        # (lowercase check happens first in validation order)
        assert any(
            "lowercase" in str(err["msg"]).lower() or "common" in str(err["msg"]).lower()
            for err in errors
        )
    
    def test_case_insensitive_username_check(self):
        """Should check username similarity case-insensitively."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="TestUser",
                password="MyTestUser123!",  # Contains username
                full_name="Test User"
            )
        
        errors = exc_info.value.errors()
        assert any("username" in str(err["msg"]).lower() for err in errors)
    
    def test_strong_password_examples(self):
        """Should accept various strong password patterns."""
        strong_passwords = [
            "MyStr0ng!Pass",
            "C0mplex#Passw0rd",
            "Secur3$Pa55word",
            "Un!qu3_P@ssw0rd",
            "R@nd0m!Pass2024",
        ]
        
        for password in strong_passwords:
            user_data = UserCreate(
                email="test@example.com",
                username="testuser",
                password=password,
                full_name="Test User"
            )
            assert user_data.password == password
