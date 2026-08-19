#!/usr/bin/env python3
import json,re,sys
text=open('data.js',encoding='utf-8').read()
report=json.load(open('catalog-report.json'))
errors=[]
if report['games']<4000:errors.append('expected at least 4,000 games')
if not 40<=report['clues']<=60:errors.append('expected 40–60 clue types')
if report['puzzles']<90:errors.append('expected at least 90 daily puzzles')
if report['last']<'2026-11-30':errors.append('puzzle schedule does not span a few months')
# generator only writes puzzles after every cell has >=3 answers; verify the generated file contains answerCounts for auditability
counts=re.findall(r'"answerCounts":\[([^]]+)\]',text)
if len(counts)!=report['puzzles']:errors.append('missing puzzle validation counts')
for i,c in enumerate(counts,1):
    nums=[int(x) for x in c.split(',')]
    if len(nums)!=9 or min(nums)<3:errors.append(f'puzzle {i} contains a weak/impossible cell')
if errors:
    print('\n'.join('ERROR: '+x for x in errors));sys.exit(1)
print(f"Validated {report['games']:,} games, {report['clues']} clues and {report['puzzles']} puzzles ({report['first']} to {report['last']}).")
