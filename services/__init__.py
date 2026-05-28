from config import settings
from services.skin_analyzer import SkinAnalyzer


def get_analyzer() -> SkinAnalyzer:
    if settings.skin_analyzer_backend == "ml_engine":
        from services.ml_engine import MLEngineAnalyzer
        return MLEngineAnalyzer()
    from services.openai_service import OpenAIAnalyzer
    return OpenAIAnalyzer()
