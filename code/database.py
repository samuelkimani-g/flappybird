import sqlite3
from typing import List, Tuple, Optional
import time

class GameDatabase:
    def __init__(self, db_name: str = 'flappy_bird.db'):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize database with proper schema migration"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scores'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                cursor.execute('''
                    CREATE TABLE scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        coins INTEGER DEFAULT 0,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                # Add missing columns if needed
                cursor.execute("PRAGMA table_info(scores)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'name' not in columns:
                    cursor.execute("ALTER TABLE scores ADD COLUMN name TEXT DEFAULT 'Unknown'")
                if 'coins' not in columns:
                    cursor.execute("ALTER TABLE scores ADD COLUMN coins INTEGER DEFAULT 0")
                if 'timestamp' not in columns:
                    cursor.execute("ALTER TABLE scores ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP")
    
    def save_score(self, name: str, score: int, coins: int = 0) -> bool:
        """Save a new score to the database"""
        if score <= 0:
            return False
        
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO scores (name, score, coins, timestamp) VALUES (?, ?, ?, datetime("now"))', 
                    (name, score, coins)
                )
                return True
        except sqlite3.Error:
            return False
    
    def get_high_score(self) -> int:
        """Get the highest score from the database"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT MAX(score) FROM scores')
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0
        except sqlite3.Error:
            return 0
    
    def get_leaderboard(self, limit: int = 10) -> List[Tuple[str, int, int]]:
        """Get top scores from the database"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT name, score, coins FROM scores ORDER BY score DESC LIMIT ?', 
                    (limit,)
                )
                return cursor.fetchall()
        except sqlite3.Error:
            return []
    
    def get_player_stats(self, name: str) -> dict:
        """Get statistics for a specific player"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*), MAX(score), AVG(score), SUM(coins) 
                    FROM scores WHERE name = ?
                ''', (name,))
                games, best, avg, coins = cursor.fetchone()
                return {
                    'games_played': games or 0,
                    'best_score': best or 0,
                    'average_score': round(avg, 1) if avg else 0,
                    'total_coins': coins or 0
                }
        except sqlite3.Error:
            return {'games_played': 0, 'best_score': 0, 'average_score': 0, 'total_coins': 0}
