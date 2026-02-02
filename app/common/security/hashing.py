import asyncio

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hash_password):
    return pwd_context.verify(plain_password, hash_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def verify_password_async(plain_password, hash_password):
    return await asyncio.to_thread(verify_password, plain_password, hash_password)


async def get_password_hash_async(password):
    return await asyncio.to_thread(get_password_hash, password)
