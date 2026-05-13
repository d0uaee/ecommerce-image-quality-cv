#!/usr/bin/env python
"""Quick test of analyzer with text prompt"""
import sys
from src.analyzer import analyze_image, global_score

# Test with electronics image and text prompt
result = analyze_image('data/raw_images/electronics/001_1.jpg', text_prompt='smartphone')
criteria = result['criteria']

print(f"\nAnalyzing: data/raw_images/electronics/001_1.jpg")
print(f"Text prompt: 'smartphone'")
print(f"\n{'Criterion':<20} {'Score':>6}  {'Value':>10}  Message")
print("-" * 65)
for name, data in criteria.items():
    print(f"{name:<20} {data['score']:>6.3f}  {str(data['value']):>10}  {data['message']}")

score = global_score(criteria)
print("-" * 65)
print(f"{'GLOBAL SCORE':<20} {score:>6.3f}")
