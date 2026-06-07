# Case Study: 不朽杯S2 主办方查询

## What happened

User asked "主办方是谁" for 2026 Dota2 老头杯 (不朽杯S2).

### Wrong approach (what the agent did first)
1. Searched Bing → empty results
2. Switched to Bilibili search → found lots of video content
3. Assumed S2 organizer = S1 organizer (斗鱼+OB) without verification → **wrong**
4. User challenged the assumption → agent admitted it was unverified
5. User suggested searching 虎牙 → agent found "虎牙不朽杯" in Bilibili video titles
6. **Inertial error**: agent stayed on Bilibili instead of jumping to huya.com
7. User explicitly asked "在虎牙看看 team B 什么时候开始比赛" → agent finally went to huya.com

### Correct approach (what should have been done)
1. Identify the entity: this is a 虎牙-sponsored event (虎牙不朽杯)
2. Go to huya.com directly → search "不朽杯S2" → find official tournament page
3. Tournament page shows: full schedule, organizer info, all match times

### Key insight
虎牙's own tournament page had the complete schedule including B-team match time (17:00), which was the user's actual question. Going to the primary source answered both questions at once.

## Additional lessons from this session

### Inertial searching
After Bilibili returned rich results for match videos, the agent kept searching there for *every* related question — including organizer info and schedule. The right source depends on the question type:
- Match videos/clips → Bilibili is fine
- Organizer/schedule/official info → go to the organizer's platform

### "Follow the lead"
When Bilibili video titles revealed "虎牙不朽杯", that should have immediately triggered: "Go to huya.com." The video title is a signpost, not the destination.

### User correction workflow
1. User challenged the unverified assumption (S2 = S1 organizer)
2. Agent admitted the gap
3. User gave a hint ("搜索下虎牙呢")
4. Agent found the lead on Bilibili but didn't follow it to the source
5. User gave a direct instruction ("在虎牙看看")
6. Agent finally went to the primary source and found everything

The user shouldn't need to give two rounds of steering. After step 3, the agent should have gone directly to huya.com.

## B-team match time (from 虎牙 official page)

| Time | Match | Teams |
|------|-------|-------|
| 14:00 | 总决赛-A | 锁妖塔-A vs 奶龙影业-A |
| **17:00** | **总决赛-B** | **锁妖塔-B vs 奶龙影业-B** |
| 20:30 | 总决赛-Ace | 锁妖塔-ACE vs 奶龙影业-ACE |
