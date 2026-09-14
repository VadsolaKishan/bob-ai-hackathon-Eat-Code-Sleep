"""
GridPulse AI — IBM watsonx.ai Integration
Connects to IBM Granite models for AI advisory generation.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WatsonxClient:
    """
    Client for IBM watsonx.ai Granite models.
    Falls back gracefully when credentials are not available.
    """

    def __init__(self, api_key: str, project_id: str, url: str, model_id: str):
        self.api_key = api_key
        self.project_id = project_id
        self.url = url
        self.model_id = model_id
        self._client = None
        self._initialized = False

        if api_key and project_id:
            self._initialize()

    def _initialize(self):
        """Lazily initialize the watsonx.ai client."""
        try:
            from ibm_watsonx_ai import APIClient, Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference
            from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

            credentials = Credentials(
                url=self.url,
                api_key=self.api_key,
            )
            self._client = ModelInference(
                model_id=self.model_id,
                credentials=credentials,
                project_id=self.project_id,
                params={
                    GenParams.MAX_NEW_TOKENS: 600,
                    GenParams.TEMPERATURE: 0.3,
                    GenParams.TOP_P: 0.9,
                    GenParams.REPETITION_PENALTY: 1.1,
                },
            )
            self._initialized = True
            logger.info(f"watsonx.ai initialized with model: {self.model_id}")
        except ImportError:
            logger.warning("ibm-watsonx-ai package not installed. Using local fallback.")
        except Exception as e:
            logger.warning(f"watsonx.ai initialization failed: {e}. Using local fallback.")

    def is_available(self) -> bool:
        """Check if watsonx.ai client is ready."""
        return self._initialized and self._client is not None

    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Generate text using IBM Granite model.
        Returns empty string if unavailable (caller handles fallback).
        """
        if not self.is_available():
            return ""

        try:
            from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
            response = self._client.generate_text(
                prompt=prompt,
                params={GenParams.MAX_NEW_TOKENS: max_tokens}
            )
            return response.strip() if response else ""
        except Exception as e:
            logger.warning(f"watsonx.ai generation failed: {e}")
            return ""
