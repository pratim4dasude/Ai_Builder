from app.tools.tool_registry import ToolRegistry
from app.tools.logistics_tools import (
    AssignWarehouseTool,
    CreateClustersTool,
    GenerateRoutesTool,
    AnalyzeRiskTool,
)

tool_registry = ToolRegistry()

tool_registry.register(AssignWarehouseTool())
tool_registry.register(CreateClustersTool())
tool_registry.register(GenerateRoutesTool())
tool_registry.register(AnalyzeRiskTool())