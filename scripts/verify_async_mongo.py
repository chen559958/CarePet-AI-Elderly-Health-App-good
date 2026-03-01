import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from data.database import init_async_pool, get_async_pool
from app.container import Container
from domain.models import PetState

async def verify():
    print("1. Initializing Async Pool...")
    pool = await init_async_pool()
    if not pool:
        print("FAILED: Could not init pool. Is DB running? Env vars set?")
        # Just in case, print env vars (masked)
        print(f"DB_HOST: {os.getenv('DB_HOST')}")
        return

    print("2. Building Container...")
    container = Container.get_instance()
    
    # Check if pet_repo has pool
    if not container.pet_repo.pool:
        print("FAILED: PetRepository has no pool!")
        return
    else:
        print("SUCCESS: PetRepository has pool.")

    print("3. Testing get_pet (Async)...")
    # Assuming user_id 1 exists or we can try any.
    # We will try user_id=1.
    try:
        user_id = 1
        pet = await container.pet_repo.get_pet(user_id)
        print(f"get_pet result: {pet}")
        
        if pet:
            print(f"Pet Name: {pet.pet_name}")
            print(f"Level: {pet.level}")
        else:
            print("No pet found for user 1 (This is verifyable behavior)")
            
    except Exception as e:
        print(f"FAILED: get_pet raised exception: {e}")
        import traceback
        traceback.print_exc()
        return

    print("4. Testing update_pet (Async)...")
    if pet:
        try:
            await container.pet_repo.update_pet(user_id, mood=pet.mood, stamina=pet.stamina)
            print("SUCCESS: update_pet completed without error.")
        except Exception as e:
             print(f"FAILED: update_pet raised exception: {e}")

    print("Verification Completed.")

if __name__ == "__main__":
    try:
        asyncio.run(verify())
    except KeyboardInterrupt:
        pass
