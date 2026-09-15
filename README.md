<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=180&section=header&text=Qilong%20Zhong&fontSize=42&fontColor=fff&animation=fadeIn&fontAlignY=32&desc=Backend%20%C2%B7%20IoT%20%C2%B7%20Full-stack&descAlignY=55&descSize=18" width="100%" />
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=3200&pause=1000&color=8B949E&center=true&vCenter=true&width=760&lines=Backend+engineer+who+ships+production+systems.;Contracts+first%2C+then+code.+Tests+and+CI+keep+it+honest.;IoT+%C2%B7+MQTT+%C2%B7+WebSocket+%C2%B7+real-time+control.;Server-authoritative+state+machines+over+in-memory+timers." alt="typing intro" />
</p>

<p align="center">
  <a href="mailto:dravenzhong27@gmail.com"><img src="https://img.shields.io/badge/Email-dravenzhong27%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" /></a>
  <a href="https://www.01weichuang.com"><img src="https://img.shields.io/badge/Website-01weichuang.com-0A0A0A?style=flat-square&logo=nextdotjs&logoColor=white" /></a>
  <img src="https://img.shields.io/badge/Location-Sydney%20%2F%20Shenzhen-2ea44f?style=flat-square" />
</p>

## 👋 About Me

- 🎓 **Bachelor of Advanced Computing @ The University of Sydney** (2024 – 2028) · GPA 3.8 / 4.0 · exchange semester @ **HKU** (2026, fully funded by the Vice Chancellor's Global Mobility Scholarship)
- 💼 **Backend lead at an early-stage IoT startup** in Shenzhen — sole software owner, shipped **3 production systems from 0 → 1** (an IoT robot teleoperation platform, an AI smart-helmet cloud backend, and a trilingual company website)
- 🤖 Currently building the cloud backend for an **AI smart helmet**: NestJS · Prisma · PostgreSQL 16 · EMQX (MQTT) · React Native
- 🧭 How I work: write the **API / event / device contracts** and decision records first, keep state **server-authoritative**, and gate every merge with **e2e tests + CI**
- 🔭 Exploring **LLM applications** — RAG, function calling, agentic workflows
- 📫 Open to **backend / full-stack internships** (Node.js / Python) — say hi via email

## 🚀 Featured Projects

| Project | Stack | What's inside |
| :-- | :-- | :-- |
| **[robot-charging-station-miniprogram](https://github.com/Dragolone/robot-charging-station-miniprogram)** <br/> <img src="https://img.shields.io/github/stars/Dragolone/robot-charging-station-miniprogram?style=flat-square&logo=github&label=stars" /> | uni-app (Vue 3) · uniCloud · MQTT · WebSocket | WeChat Mini Program for **real-time robot fleet management & teleoperation**. Live in beta with 80+ users. WebSocket with exponential-backoff reconnect + heartbeat + HTTP-polling fallback; 5 Hz velocity commands with a **1 s dead-man stop**; HMAC-SHA256 short-lived tokens for WS auth; passed two rounds of WeChat platform review. |
| **[ECS](https://github.com/Dragolone/ECS)** | Python · Flask · paho-mqtt · flask-sock | The **IoT gateway** behind the platform above. Merged two services into one process that handles MQTT → DB persistence, HTTP command dispatch, and WS broadcast — halved the ops footprint, telemetry latency dropped from 10 s polling to ~1 s. |
| **[01web](https://github.com/Dragolone/01web)** | Next.js · Nginx · Tencent Cloud | Trilingual (简 / 繁 / EN) **company website**, live at [01weichuang.com](https://www.01weichuang.com). Contact-form API with validation, IP rate limiting and graceful SMTP fallback; security headers; ICP-registered. |
| **[Background-Management](https://github.com/Dragolone/Background-Management)** | Vue 3 | Internal **admin dashboard** for ZeroOne Innovation's robot platform — the ops-side companion to the mini program. |
| **[Elec1601](https://github.com/Dragolone/Elec1601)** | C++ · Arduino AVR | **Autonomous maze-racing car** — state-machine architecture, DFS / wall-following path search, sensor filtering and debouncing. **Top 8 of 200+ teams**, 1st in class. |

> 🔒 **Closed-source, but happy to talk about it:** the AI smart-helmet backend — a modular NestJS monolith with a unified ingest layer (MQTT / webhook / BLE-relay), idempotent event dedup, a persisted **SOS state machine** that survives restarts, and a command-ack state machine (`pending → delivered → success / failed / offline`). Pre-launch hardening: 66 hardening + 8 stress cases surfaced 11 defects, all fixed same day; **24 e2e suites / 209 tests green** in CI, including an empty-DB migration check.

## 🛠️ Tech Stack

<table align="center">
  <tr>
    <td align="right"><b>Languages</b></td>
    <td><img src="https://skillicons.dev/icons?i=ts,js,python,java,cpp,r,bash" /></td>
  </tr>
  <tr>
    <td align="right"><b>Backend</b></td>
    <td><img src="https://skillicons.dev/icons?i=nodejs,nestjs,express,fastapi,flask" /></td>
  </tr>
  <tr>
    <td align="right"><b>Frontend</b></td>
    <td><img src="https://skillicons.dev/icons?i=react,vue,nextjs,reactnative,tailwind" /></td>
  </tr>
  <tr>
    <td align="right"><b>Data</b></td>
    <td><img src="https://skillicons.dev/icons?i=postgres,prisma,mongodb,mysql,sqlite,pytorch,sklearn" /></td>
  </tr>
  <tr>
    <td align="right"><b>DevOps & Tools</b></td>
    <td><img src="https://skillicons.dev/icons?i=docker,nginx,githubactions,jest,git,linux,arduino,latex" /></td>
  </tr>
</table>

<p align="center">
  <sub>Also: MQTT / EMQX · WebSocket · JWT + refresh auth · rate limiting & idempotency · Alembic / Prisma migrations · Docker Compose · Caddy · Tencent Cloud (CVM / COS / SMS / TRTC) · Render · Claude Code</sub>
</p>

## 📊 GitHub Stats

<p align="center">
  <img src="https://github-profile-summary-cards.vercel.app/api/cards/profile-details?username=Dragolone&theme=tokyonight" width="100%" alt="profile details" />
</p>

<p align="center">
  <img src="https://github-profile-summary-cards.vercel.app/api/cards/repos-per-language?username=Dragolone&theme=tokyonight" width="49%" alt="repos per language" />
  <img src="https://github-profile-summary-cards.vercel.app/api/cards/most-commit-language?username=Dragolone&theme=tokyonight" width="49%" alt="most commit language" />
</p>

<p align="center">
  <img src="https://ghchart.rshah.org/409ba5/Dragolone" width="100%" alt="contribution calendar" />
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Dragolone/Dragolone/output/github-contribution-grid-snake-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Dragolone/Dragolone/output/github-contribution-grid-snake.svg">
    <img alt="github contribution snake animation" src="https://raw.githubusercontent.com/Dragolone/Dragolone/output/github-contribution-grid-snake.svg">
  </picture>
</p>

## 👀 Profile Views

<p align="center">
  <img src="https://count.getloli.com/get/@Dragolone.github.readme" alt="profile views" />
  <br/>
  <sub>Counting since May 6, 2026</sub>
</p>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%" />
</p>
