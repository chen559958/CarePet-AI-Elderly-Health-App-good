from __future__ import annotations
from app.container import Container
from domain.models import UserProfile

class MemberViewModel:
    def __init__(self, container: Container):
        self.container = container
        self.user_repo = container.user_repo

    def load_profile(self) -> UserProfile:
        user = self.container.auth_service.get_current_user()
        if not user:
            raise Exception("User not authenticated")
        return self.user_repo.init_default_profile_if_empty(user.id)

    def load_drugs(self):
        user = self.container.auth_service.get_current_user()
        if not user:
            return []
        return self.container.drug_repo.list_active_drugs(user.id)

    async def delete_drug(self, drug_id: int):
        import asyncio
        user = self.container.auth_service.get_current_user()
        if not user:
            raise Exception("User not authenticated")
        await asyncio.to_thread(self.container.drug_repo.set_active, user.id, drug_id, False)

    async def save_profile(self, profile: UserProfile):
        import asyncio
        user = self.container.auth_service.get_current_user()
        if not user:
            raise Exception("User not authenticated")
        await asyncio.to_thread(self.user_repo.update_profile, user.id, profile)
