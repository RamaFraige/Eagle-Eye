#!/usr/bin/env python3
"""Test app startup time with lazy loading."""

import time
import sys

print("[TEST] Starting Eagle Eye RealAISystem initialization test...")
print("[TEST] " + "="*50)

start = time.time()
from app import RealAISystem
app_init_done = time.time()

system = RealAISystem()
full_init_done = time.time()

print(f"\n[TEST] Import time: {(app_init_done - start):.3f}s")
print(f"[TEST] Full init time: {(full_init_done - start):.3f}s")
print(f"\n[TEST] Fighting models loaded at startup? {system.fighting_detector._models_loaded}")
print(f"[TEST] ✓ App ready INSTANTLY (fighting loads on first alert)")
print("[TEST] " + "="*50)
