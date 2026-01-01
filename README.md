# SQL Dashboard

A lightweight, intuitive dashboard for exploring SQLite databases with dynamic filtering and instant sharing capabilities!

Try it live [here](https://dashboard.accoumar.fr/).

<https://github.com/user-attachments/assets/93505239-b7a0-41ac-8912-46c1a2db0020>

P.S. Heavily helped by AI. Tbh Claude code is amazing when guided well!

## Introduction

- ⚡ **Dynamic Data Exploration** - View multiple tables simultaneously with real-time filtering across related tables
- 🔗 **URL State Management** - Your entire dashboard state (selected tables, filters) lives in the URL. Copy and paste to share results with colleagues instantly.
- 🎨 **Intuitive Interface** - Simple, clean design. Just upload your database file and start exploring - zero learning curve.
- 🔄 **Cross-Table Filtering** - Apply filters that automatically work across table relationships

## Development

See [development docs](./development.md).

## Deployment

We use [dokploy](https://github.com/Dokploy/dokploy) for deployment, via [this docker compose file](./docker-compose.yml).
