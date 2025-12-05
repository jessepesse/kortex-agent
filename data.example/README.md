# Data Examples

This folder contains **example data files** showing the expected structure for Kortex Agent.

> **Note:** These files are for reference only. They are NOT used by the application.

When you first run Kortex Agent, the `data/` folder is created automatically with empty default values.

## Data Files

| File | Purpose |
|------|---------|
| `profile.json` | User profile (name, location, timezone, language preferences) |
| `health.json` | Health tracking (physical, mental, energy levels) |
| `goals.json` | Short-term and long-term goals |
| `finance.json` | Financial accounts, transactions, budgets |
| `routines.json` | Daily and weekly routines |
| `values.json` | Personal values and principles |
| `active_projects.json` | Current projects and tasks |
| `tech_inventory.json` | Tech equipment and devices |
| `meal_rotation.json` | Meal planning and recipes |
| `pantry_staples.json` | Kitchen inventory |

## Conversations

The `data/conversations/` folder stores chat history. Each conversation is saved as a separate JSON file with the format:

```
{timestamp}_{uuid}.json
```

Example structure:
```json
{
  "id": "1234567890_abc12345",
  "title": "Planning my week",
  "timestamp": 1234567890,
  "lastModified": 1234567890,
  "pinned": false,
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

## Customization

Feel free to add your own JSON files to the `data/` folder. Kortex Agent will automatically detect and use them as context for the AI assistant.
