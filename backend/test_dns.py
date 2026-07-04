import asyncio
import socket

async def main():
    try:
        loop = asyncio.get_event_loop()
        res = await loop.getaddrinfo('aws-0-ap-south-1.pooler.supabase.com', 6543)
        print("Success:", res)
    except Exception as e:
        print("Failed:", repr(e))

asyncio.run(main())
