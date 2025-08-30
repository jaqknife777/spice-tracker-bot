#!/usr/bin/env python3
"""
Simple test script to verify database changes work correctly
"""

import asyncio
import os
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv()

async def test_database():
    """Test the database functionality"""
    try:
        # Initialize database
        db = Database()
        await db.initialize()
        print("✅ Database initialized successfully")
        
        # Test creating a user
        await db.upsert_user("test_user_123", "TestUser")
        print("✅ User created successfully")
        
        # Test adding a solo deposit
        await db.add_deposit("test_user_123", "TestUser", 1000)
        print("✅ Solo deposit added successfully")
        
        # Test creating an expedition
        expedition_id = await db.create_expedition(
            "test_user_123", 
            "TestUser", 
            5000, 
            25.0, 
            50
        )
        print(f"✅ Expedition created successfully with ID: {expedition_id}")
        
        # Test adding expedition participant
        await db.add_expedition_participant(
            expedition_id,
            "test_user_123",
            "TestUser",
            1250,  # 25% of 5000
            25,    # 1250 / 50
            0      # no leftover
        )
        print("✅ Expedition participant added successfully")
        
        # Test adding expedition deposit
        await db.add_expedition_deposit(
            "test_user_123",
            "TestUser",
            1250,
            expedition_id
        )
        print("✅ Expedition deposit added successfully")
        
        # Test getting user deposits
        deposits = await db.get_user_deposits("test_user_123")
        print(f"✅ Retrieved {len(deposits)} deposits")
        for deposit in deposits:
            print(f"   - {deposit['sand_amount']} sand ({deposit['type']})")
        
        # Test getting expedition participants
        participants = await db.get_expedition_participants(expedition_id)
        print(f"✅ Retrieved {len(participants)} expedition participants")
        for participant in participants:
            print(f"   - {participant['username']}: {participant['sand_amount']} sand")
        
        print("\n🎉 All database tests passed!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database())

