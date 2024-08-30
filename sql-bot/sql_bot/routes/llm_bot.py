"""Router for SQL DB connect."""
import logging
import fastapi
from fastapi import Depends
from pydantic import BaseModel, Field
import const
from sql_bot.lib.bot import QueryBot
from sql_bot.routes import validate_token

__version__ = "1.0.0"

logger = logging.getLogger(__file__)

# Create a single instance of QueryBot
query_bot = QueryBot()

bot_router = fastapi.APIRouter(
    prefix="/api/v1/bot",
    tags=["Query Bot"],
    on_startup=[query_bot.startup],
    on_shutdown=[query_bot.shutdown],
)

class BotQuery(BaseModel):
    """Model for querying LLM."""
    query: str = Field(..., title="Query string")

@bot_router.post(
    "/query",
    include_in_schema=True,
    response_model=None,
    dependencies=(
        [Depends(validate_token.verify_token)]
        if const.SERVICE_COM_TOKEN
        else []
    ),
)
def get_systems_from_query(bot_query: BotQuery) -> dict:
    """Get systems from query."""

    return query_bot.get_db_query(bot_query.query)


