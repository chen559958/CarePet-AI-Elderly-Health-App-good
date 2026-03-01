from __future__ import annotations

class LevelEngine:
    """Handles pet leveling logic."""
    
    MAX_LEVEL = 12
    
    @staticmethod
    def get_required_exp(level: int) -> int:
        """Return XP required to reach the NEXT level from the current one."""
        if level <= 5:
            return 20
        elif level <= 10:
            return 50
        elif level < 12:
            return 80
        return 999999 # Max level
        
    @classmethod
    def calculate_level(cls, current_level: int, current_exp: int) -> tuple[int, int]:
        """
        Calculate new level and remaining exp.
        Returns (new_level, new_exp)
        """
        level = current_level
        exp = current_exp
        
        while level < cls.MAX_LEVEL:
            req = cls.get_required_exp(level)
            if exp >= req:
                exp -= req
                level += 1
            else:
                break
                
        return level, exp
