#!/usr/bin/env python3
"""
Test script to verify expedition functionality works correctly
"""

import asyncio
import os
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv()

async def test_expedition():
    """Test the expedition functionality"""
    try:
        # Initialize database
        db = Database()
        await db.initialize()
        print("✅ Database initialized successfully")
        
        # Test creating a user
        await db.upsert_user("test_user_123", "TestUser")
        print("✅ User created successfully")
        
        # Test creating an expedition
        expedition_id = await db.create_expedition(
            "test_user_123", 
            "TestUser", 
            50000, 
            10.0,  # 10% harvester share
            50     # sand per melange
        )
        print(f"✅ Expedition created successfully with ID: {expedition_id}")
        
        # Test adding expedition participants
        participants = [
            ("participant_1", "Jack", 10000),  # 10,000 sand
            ("participant_2", "Tobar", 10000), # 10,000 sand
            ("participant_3", "Shon", 10000),  # 10,000 sand
            ("participant_4", "Billy", 10000), # 10,000 sand
        ]
        
        for user_id, username, sand_amount in participants:
            # Add participant
            await db.add_expedition_participant(
                expedition_id,
                user_id,
                username,
                sand_amount,
                sand_amount // 50,  # melange
                sand_amount % 50    # leftover
            )
            print(f"✅ Added participant: {username} with {sand_amount:,} sand")
            
            # Add expedition deposit
            await db.add_expedition_deposit(
                user_id,
                username,
                sand_amount,
                expedition_id
            )
            print(f"✅ Added expedition deposit for {username}")
        
        # Test getting expedition participants
        expedition_participants = await db.get_expedition_participants(expedition_id)
        print(f"✅ Retrieved {len(expedition_participants)} expedition participants")
        
        for participant in expedition_participants:
            print(f"   - {participant['username']}: {participant['sand_amount']:,} sand, {participant['melange_amount']:,} melange")
        
        # Test getting user deposits
        for user_id, username, _ in participants:
            deposits = await db.get_user_deposits(user_id)
            print(f"✅ Retrieved {len(deposits)} deposits for {username}")
            for deposit in deposits:
                print(f"   - {deposit['sand_amount']:,} sand ({deposit['type']}) - Expedition #{deposit['expedition_id']}")
        
        print("\n🎉 All expedition tests passed!")
        
    except Exception as e:
        print(f"❌ Expedition test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_expedition())
