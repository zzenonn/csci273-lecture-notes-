#!/usr/bin/env python3
import sys

for line in sys.stdin:
    for word in line.lower().split():
        word = word.strip('.,!?;:"()[]')
        if word:
            print(f"{word}\t1")
