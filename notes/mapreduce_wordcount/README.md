# MapReduce Word Count

A simple MapReduce word count implementation using separate mapper/reducer scripts and Linux `sort` for the shuffle phase.

## Files

- `mapper.py` - Map stage: reads text and emits (word, 1) pairs
- `reducer.py` - Reduce stage: sums counts for each word
- Linux `sort` - Shuffle stage: groups identical keys together

## Usage

Basic usage:
```bash
cat input.txt | python3 mapper.py | sort | python3 reducer.py
```

Sort by word count (most frequent first):
```bash
cat input.txt | python3 mapper.py | sort | python3 reducer.py | sort -t$'\t' -k2 -nr
```

Or make scripts executable:
```bash
chmod +x mapper.py reducer.py
cat input.txt | ./mapper.py | sort | ./reducer.py | sort -t$'\t' -k2 -nr
```

## How It Works

1. **Map**: `mapper.py` reads input line by line, splits into words, and outputs `word\t1`
2. **Shuffle**: `sort` groups all identical words together
3. **Reduce**: `reducer.py` sums the counts for each word group

## Example

```bash
echo "hello world hello" | python3 mapper.py | sort | python3 reducer.py
```

Output:
```
hello	2
world	1
```
