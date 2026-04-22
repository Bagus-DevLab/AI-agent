"""
tests/test_config.py — Tests for config.py validation functions
================================================================

Priority 3: Ensure config validation catches missing/invalid settings.
"""

import pytest
from unittest.mock import patch

import config as config_module


# ============================================================================
# validate_config — LLM config validation
# ============================================================================

class TestValidateConfig:

    def test_all_set_returns_no_errors(self):
        """When both API key and URL are set, no errors."""
        with patch.object(config_module, "LLM_API_KEY", "sk-test-key"), \
             patch.object(config_module, "LLM_BASE_URL", "https://api.example.com"):
            errors = config_module.validate_config()
            assert errors == []

    def test_missing_api_key(self):
        with patch.object(config_module, "LLM_API_KEY", ""), \
             patch.object(config_module, "LLM_BASE_URL", "https://api.example.com"):
            errors = config_module.validate_config()
            assert len(errors) == 1
            assert "ENOWXAI_KEY" in errors[0]

    def test_missing_base_url(self):
        with patch.object(config_module, "LLM_API_KEY", "sk-test-key"), \
             patch.object(config_module, "LLM_BASE_URL", ""):
            errors = config_module.validate_config()
            assert len(errors) == 1
            assert "ENOWXAI_URL" in errors[0]

    def test_both_missing(self):
        with patch.object(config_module, "LLM_API_KEY", ""), \
             patch.object(config_module, "LLM_BASE_URL", ""):
            errors = config_module.validate_config()
            assert len(errors) == 2

    def test_returns_list_type(self):
        """validate_config always returns a list."""
        result = config_module.validate_config()
        assert isinstance(result, list)


# ============================================================================
# validate_r2_config — Cloudflare R2 config validation
# ============================================================================

class TestValidateR2Config:

    def test_all_set_returns_no_errors(self):
        with patch.object(config_module, "R2_ENDPOINT", "https://r2.example.com"), \
             patch.object(config_module, "R2_ACCESS_KEY", "access123"), \
             patch.object(config_module, "R2_SECRET_KEY", "secret456"), \
             patch.object(config_module, "R2_BUCKET_NAME", "my-bucket"):
            errors = config_module.validate_r2_config()
            assert errors == []

    def test_missing_endpoint(self):
        with patch.object(config_module, "R2_ENDPOINT", ""), \
             patch.object(config_module, "R2_ACCESS_KEY", "access123"), \
             patch.object(config_module, "R2_SECRET_KEY", "secret456"), \
             patch.object(config_module, "R2_BUCKET_NAME", "my-bucket"):
            errors = config_module.validate_r2_config()
            assert len(errors) == 1
            assert "R2_ENDPOINT" in errors[0]

    def test_missing_access_key(self):
        with patch.object(config_module, "R2_ENDPOINT", "https://r2.example.com"), \
             patch.object(config_module, "R2_ACCESS_KEY", ""), \
             patch.object(config_module, "R2_SECRET_KEY", "secret456"), \
             patch.object(config_module, "R2_BUCKET_NAME", "my-bucket"):
            errors = config_module.validate_r2_config()
            assert len(errors) == 1
            assert "R2_ACCESS_KEY" in errors[0]

    def test_missing_secret_key(self):
        with patch.object(config_module, "R2_ENDPOINT", "https://r2.example.com"), \
             patch.object(config_module, "R2_ACCESS_KEY", "access123"), \
             patch.object(config_module, "R2_SECRET_KEY", ""), \
             patch.object(config_module, "R2_BUCKET_NAME", "my-bucket"):
            errors = config_module.validate_r2_config()
            assert len(errors) == 1
            assert "R2_SECRET_KEY" in errors[0]

    def test_missing_bucket_name(self):
        with patch.object(config_module, "R2_ENDPOINT", "https://r2.example.com"), \
             patch.object(config_module, "R2_ACCESS_KEY", "access123"), \
             patch.object(config_module, "R2_SECRET_KEY", "secret456"), \
             patch.object(config_module, "R2_BUCKET_NAME", ""):
            errors = config_module.validate_r2_config()
            assert len(errors) == 1
            assert "R2_BUCKET_NAME" in errors[0]

    def test_all_missing(self):
        with patch.object(config_module, "R2_ENDPOINT", ""), \
             patch.object(config_module, "R2_ACCESS_KEY", ""), \
             patch.object(config_module, "R2_SECRET_KEY", ""), \
             patch.object(config_module, "R2_BUCKET_NAME", ""):
            errors = config_module.validate_r2_config()
            assert len(errors) == 4

    def test_returns_list_type(self):
        result = config_module.validate_r2_config()
        assert isinstance(result, list)
