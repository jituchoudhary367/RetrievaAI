import asyncio
from app.config import get_settings
from services.runtime_settings import get_runtime_settings

async def main():
    s = get_settings()
    settings = await get_runtime_settings().get_all_for_tenant('00000000-0000-0000-0000-000000000001')
    print('groq api key from app_settings:', getattr(s, 'groq_api_key', None))
    print('settings from DB:', settings)
    if getattr(s, 'groq_api_key', None):
        settings['GROQ_API_KEY'] = s.groq_api_key
    print('final response:', settings)

if __name__ == "__main__":
    asyncio.run(main())
