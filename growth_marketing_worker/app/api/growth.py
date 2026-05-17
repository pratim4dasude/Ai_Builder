from fastapi import APIRouter

from app.connectors.product_connector import ProductConnector
from app.connectors.sales_connector import SalesConnector
from app.connectors.campaign_connector import CampaignConnector
from app.connectors.customer_connector import CustomerConnector
from app.connectors.content_calendar_connector import ContentCalendarConnector
from app.services.data_validation_service import GrowthDataValidationService


router = APIRouter(prefix="/growth", tags=["Growth"])


@router.get("/validate")
def validate_growth_data():
    products_df = ProductConnector().load_data()
    sales_df = SalesConnector().load_data()
    campaigns_df = CampaignConnector().load_data()
    customers_df = CustomerConnector().load_data()
    content_df = ContentCalendarConnector().load_data()

    result = GrowthDataValidationService().validate_all(
        products_df=products_df,
        sales_df=sales_df,
        campaigns_df=campaigns_df,
        customers_df=customers_df,
        content_df=content_df,
    )

    return result

from app.config import USE_LLM, OPENAI_MODEL, OPENAI_API_KEY, USE_LLM_RAW
from app.services.llm_service import LLMService


@router.get("/llm/status")
def llm_status():
    service = LLMService()

    return {
        "use_llm_raw": USE_LLM_RAW,
        "use_llm_from_config": USE_LLM,
        "model": OPENAI_MODEL,
        "api_key_loaded": bool(OPENAI_API_KEY),
        "api_key_preview": OPENAI_API_KEY[:7] + "..." if OPENAI_API_KEY else None,
        "llm_service_enabled": service.enabled,
    }