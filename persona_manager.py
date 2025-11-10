#!/usr/bin/env python3
"""
Persona Manager - Save and rotate browser fingerprint personas across sessions
Stores personas in Docker volume for persistence across container restarts
"""

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path


class PersonaManager:
    """
    Manages browser fingerprint personas with persistence across sessions
    Stores personas in JSON format with rotation capabilities
    """
    
    def __init__(self, personas_dir='/app/data/personas'):
        """
        Initialize PersonaManager
        
        Args:
            personas_dir: Directory to store persona JSON files (Docker volume mount)
        """
        self.personas_dir = Path(personas_dir)
        self.personas_dir.mkdir(parents=True, exist_ok=True)
        self.personas_file = self.personas_dir / 'personas.json'
        self.personas = self._load_personas()
        
    def _load_personas(self):
        """Load existing personas from disk"""
        if self.personas_file.exists():
            try:
                with open(self.personas_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f'⚠️  Failed to load personas: {e}')
                return {'personas': [], 'metadata': {'total_created': 0}}
        return {'personas': [], 'metadata': {'total_created': 0}}
    
    def _save_personas(self):
        """Save personas to disk"""
        try:
            with open(self.personas_file, 'w', encoding='utf-8') as f:
                json.dump(self.personas, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f'⚠️  Failed to save personas: {e}')
    
    def create_persona(self, fingerprint_data):
        """
        Create and save a new persona
        
        Args:
            fingerprint_data: Dict containing all fingerprint parameters
            
        Returns:
            str: Persona ID
        """
        persona_id = f"persona_{self.personas['metadata']['total_created']:05d}_{int(datetime.now().timestamp())}"
        
        persona = {
            'id': persona_id,
            'created_at': datetime.now().isoformat(),
            'last_used': datetime.now().isoformat(),
            'use_count': 1,
            'fingerprint': fingerprint_data,
        }
        
        self.personas['personas'].append(persona)
        self.personas['metadata']['total_created'] += 1
        self._save_personas()
        
        print(f'✅ Created persona: {persona_id}')
        return persona_id
    
    def get_persona(self, persona_id):
        """
        Retrieve a specific persona by ID
        
        Args:
            persona_id: ID of persona to retrieve
            
        Returns:
            dict: Persona data or None
        """
        for persona in self.personas['personas']:
            if persona['id'] == persona_id:
                return persona
        return None
    
    def update_persona_usage(self, persona_id):
        """Update persona last used timestamp and use count"""
        for persona in self.personas['personas']:
            if persona['id'] == persona_id:
                persona['last_used'] = datetime.now().isoformat()
                persona['use_count'] += 1
                self._save_personas()
                break
    
    def get_random_persona(self, max_age_days=30, max_uses=100):
        """
        Get a random existing persona that hasn't been overused
        
        Args:
            max_age_days: Maximum age of persona to reuse
            max_uses: Maximum number of times to reuse persona
            
        Returns:
            dict: Persona data or None if no suitable persona exists
        """
        suitable_personas = []
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        for persona in self.personas['personas']:
            created_at = datetime.fromisoformat(persona['created_at'])
            if created_at > cutoff_date and persona['use_count'] < max_uses:
                suitable_personas.append(persona)
        
        if suitable_personas:
            return random.choice(suitable_personas)
        return None
    
    def get_persona_for_rotation(self, rotation_strategy='weighted'):
        """
        Get a persona using rotation strategy
        
        Args:
            rotation_strategy: 'weighted' (favor less-used), 'random', 'round-robin', 'new'
            
        Returns:
            dict: Persona data or None (if 'new' strategy)
        """
        if not self.personas['personas'] or rotation_strategy == 'new':
            return None
        
        if rotation_strategy == 'random':
            return random.choice(self.personas['personas'])
        
        elif rotation_strategy == 'weighted':
            # Weight personas inversely by use_count (less used = higher weight)
            personas_with_weights = []
            for persona in self.personas['personas']:
                weight = 1.0 / (persona['use_count'] + 1)  # +1 to avoid division by zero
                personas_with_weights.append((persona, weight))
            
            # Weighted random selection
            total_weight = sum(w for _, w in personas_with_weights)
            rand_val = random.uniform(0, total_weight)
            cumulative = 0
            
            for persona, weight in personas_with_weights:
                cumulative += weight
                if rand_val <= cumulative:
                    return persona
            
            return personas_with_weights[0][0]  # Fallback
        
        elif rotation_strategy == 'round-robin':
            # Return least recently used persona
            return min(self.personas['personas'], key=lambda p: p['last_used'])
        
        return None
    
    def clean_old_personas(self, max_age_days=90, max_personas=1000):
        """
        Clean up old or excessive personas
        
        Args:
            max_age_days: Remove personas older than this
            max_personas: Keep only this many most recent personas
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        # Filter by age
        filtered = [
            p for p in self.personas['personas']
            if datetime.fromisoformat(p['created_at']) > cutoff_date
        ]
        
        # Sort by last_used and keep most recent
        filtered.sort(key=lambda p: p['last_used'], reverse=True)
        filtered = filtered[:max_personas]
        
        removed_count = len(self.personas['personas']) - len(filtered)
        if removed_count > 0:
            print(f'🧹 Cleaned {removed_count} old personas')
            self.personas['personas'] = filtered
            self._save_personas()
    
    def get_statistics(self):
        """Get statistics about personas"""
        if not self.personas['personas']:
            return {
                'total_personas': 0,
                'total_created': self.personas['metadata']['total_created'],
                'avg_use_count': 0,
                'oldest_persona': None,
                'newest_persona': None,
            }
        
        use_counts = [p['use_count'] for p in self.personas['personas']]
        created_dates = [datetime.fromisoformat(p['created_at']) for p in self.personas['personas']]
        
        return {
            'total_personas': len(self.personas['personas']),
            'total_created': self.personas['metadata']['total_created'],
            'avg_use_count': sum(use_counts) / len(use_counts),
            'max_use_count': max(use_counts),
            'min_use_count': min(use_counts),
            'oldest_persona': min(created_dates).isoformat(),
            'newest_persona': max(created_dates).isoformat(),
        }


def fingerprint_to_dict(user_agent, accept_language, screen, gpu, hardware, 
                        connection, timezone_offset, battery, media_devices, 
                        fonts, webrtc, plugins_js):
    """
    Convert all fingerprint parameters to a serializable dictionary
    
    Args:
        All fingerprint generation function returns
        
    Returns:
        dict: Complete fingerprint data
    """
    return {
        'user_agent': user_agent,
        'accept_language': accept_language,
        'screen': screen,
        'gpu': gpu,
        'hardware': hardware,
        'connection': connection,
        'timezone_offset': timezone_offset,
        'battery': battery,
        'media_devices': media_devices,
        'fonts': fonts,
        'webrtc': webrtc,
        'plugins': plugins_js,
        'timestamp': datetime.now().isoformat(),
    }

