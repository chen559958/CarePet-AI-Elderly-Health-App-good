
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.container import Container

import asyncio

async def set_mood(user_id: int, target_mood: int):
    container = Container.get_instance()
    # Ensure pool is initialized
    await container.database.init_async_pool()
    
    pet = await container.pet_repo.get_pet(user_id)
    if pet:
        print(f"Current pet mood: {pet.mood}. Updating to {target_mood}...")
        await container.pet_repo.update_pet(
            user_id=user_id,
            mood=target_mood,
            stamina=pet.stamina,
            level=pet.level,
            exp=pet.exp,
            state=pet.state,
            bowl_expires_at=pet.bowl_expires_at
        )
        print("Mood updated successfully.")
    else:
        print(f"No pet found for user {user_id} in database.")

if __name__ == "__main__":
    # Assuming user_id 1 for demo script
    asyncio.run(set_mood(1, 80))
