from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings

from app.routers.alert import router as alert_router
from app.routers.auth import router as auth_router
from app.routers.channel import router as channel_router
from app.routers.channel_assignment import router as channel_assignment_router
from app.routers.contract import router as contract_router
from app.routers.customer import router as customer_router
from app.routers.customer_channel_link import router as customer_channel_link_router
from app.routers.customer_views import router as customer_views_router
from app.routers.dashboard import router as dashboard_router
from app.routers.dict_item import router as dict_item_router
from app.routers.dispatch import router as dispatch_router
from app.routers.evaluation import router as evaluation_router
from app.routers.execution_plan import router as execution_plan_router
from app.routers.follow_up import router as follow_up_router
from app.routers.knowledge import router as knowledge_router
from app.routers.lead import router as lead_router
from app.routers.operation_log import router as operation_log_router
from app.routers.nine_a import router as nine_a_router
from app.routers.opportunity import router as opportunity_router
from app.routers.product import router as product_router
from app.routers.product_installation import router as product_installation_router
from app.routers.project import router as project_router
from app.routers.report import router as report_router
from app.routers.sales_target import router as sales_target_router
from app.routers.unified_target import router as unified_target_router
from app.routers.user import router as user_router
from app.routers.work_order import router as work_order_router

app = FastAPI(title="普悦销管系统 API", description="普悦销管系统后端接口")
settings = get_settings()
allowed_origins = [
    origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(channel_router)
app.include_router(channel_assignment_router)
app.include_router(unified_target_router)
app.include_router(execution_plan_router)
app.include_router(work_order_router)
app.include_router(evaluation_router)
app.include_router(knowledge_router)
app.include_router(product_installation_router)
app.include_router(customer_router)
app.include_router(customer_views_router)
app.include_router(lead_router)
app.include_router(opportunity_router)
app.include_router(nine_a_router)
app.include_router(contract_router)
app.include_router(follow_up_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(project_router)
app.include_router(dict_item_router)
app.include_router(operation_log_router)
app.include_router(report_router)
app.include_router(dashboard_router)
app.include_router(alert_router)
app.include_router(sales_target_router)
app.include_router(dispatch_router)
app.include_router(customer_channel_link_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
