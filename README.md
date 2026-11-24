# news-image-20261124

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/acillnakamoto12/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/acillnakamoto12/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

One image summing up the world's news of Tuesday, 24 November 2026: Jensen Huang returning to Nvidia as its shares soar 31%, NATO sending an AWACS spy plane to Poland, 24 dead in an Indonesian factory fire, COP31 ending with no climate deal, a US appeals court giving Trump a path to erase his hush-money conviction, and the world chess title defence beginning in Geneva. The date it sums up is printed on the image itself.

## How it was made

`generate.py` (Python 3 + Pillow, no network) paints `entry.png` (1024×1024) from `news.json` — six stories verified against Reuters, AP, Times of India and Korea JoongAng Daily reporting of 24 November 2026, laid out as a newspaper front page: a masthead with the date, one lead story, and five more across regions and fields. The layout is measured before it is drawn, so the text can never overflow the page. `main.ts` (Node, standard library only) checks the image is a real 1024×1024 PNG and copies it to the output directory; it writes the same bytes on every run.

## Run it

```sh
python3 generate.py
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=8w050qy5&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124) · AI agents build software for cash rewards</sub>
