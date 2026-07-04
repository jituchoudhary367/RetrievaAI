import asyncio
import socket

async def main():
    try:
        loop = asyncio.get_event_loop()
        res = await loop.getaddrinfo('aws-1-ap-southeast-2.pooler.supabase.com', 5432)
        print("Success:", res)
    except Exception as e:
        print("Failed:", repr(e))

asyncio.run(main())
