import asyncio
import os
from data.database import init_pool, get_or_init_connection
from data.repositories.pet_repo import PetRepository

async def test_pet_repo():
    print("Initializing DB Pool...")
    init_pool()
    
    def conn_factory():
        return get_or_init_connection()
    
    print("Initializing PetRepository with conn_factory...")
    repo = PetRepository(conn_factory)
    
    user_id = 1
    print(f"Testing get_pet for user {user_id}...")
    try:
        # Should call my new get_pet which uses asyncio.to_thread(_get_pet_sync)
        pet = await asyncio.wait_for(repo.get_pet(user_id), timeout=10)
        if pet:
            print(f"SUCCESS: Found pet: {pet.pet_name}, Level: {pet.level}")
        else:
            print("SUCCESS: No pet found (expected if DB empty), but no hang!")
    except asyncio.TimeoutError:
        print("FAILED: get_pet timed out!")
    except Exception as e:
        print(f"FAILED: get_pet raised error: {e}")

if __name__ == "__main__":
    asyncio.run(test_pet_repo())
