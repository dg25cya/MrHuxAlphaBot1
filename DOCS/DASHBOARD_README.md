# Hux Alpha Bot Dashboard

## Overview

The Hux Alpha Bot now includes a comprehensive multi-platform search dashboard that allows users to search across Telegram groups, X (Twitter) profiles, DexScreener, and Pump.fun platforms from a single interface.

## Features

### 🔍 Multi-Platform Search
- **DexScreener**: Search for token pairs and trading data
- **Pump.fun**: Find token launches and launch data
- **X (Twitter)**: Search for profiles and trending topics
- **Telegram**: Find groups and channels

### 📊 Dashboard Interface
- Modern, responsive web interface
- Real-time search across all platforms
- Trending data from all platforms
- Detailed view modals for tokens, groups, and profiles
- Beautiful gradient design with smooth animations

### 🚀 API Endpoints

#### Search Endpoints
- `GET /dashboard/search/all?query={query}&limit={limit}` - Search across all platforms
- `GET /dashboard/search/dexscreener?query={query}&limit={limit}` - Search DexScreener
- `GET /dashboard/search/pumpfun?query={query}&limit={limit}` - Search Pump.fun
- `GET /dashboard/search/x?query={query}&limit={limit}` - Search X profiles
- `GET /dashboard/search/telegram?query={query}&limit={limit}` - Search Telegram groups

#### Trending Data
- `GET /dashboard/trending` - Get trending data from all platforms

#### Detail Endpoints
- `GET /dashboard/token/{address}` - Get detailed token information
- `GET /dashboard/group/{username}` - Get Telegram group details
- `GET /dashboard/profile/{username}` - Get X profile details

## Usage

### Access the Dashboard
1. Start the bot: `python -m src.main`
2. Open your browser to: `http://localhost:8002/dashboard/`

### Search Functionality
1. Enter your search query in the search box
2. Select which platforms to search (checkboxes)
3. Click "Search All" to get results from all selected platforms
4. Click on any result to view detailed information

### Trending Data
The dashboard automatically loads trending data from all platforms, including:
- Popular token pairs from DexScreener
- Active token launches from Pump.fun
- Trending topics from X
- Popular crypto-related Telegram groups

## Technical Details

### Architecture
- **Backend**: FastAPI with async/await support
- **Frontend**: Vanilla JavaScript with modern CSS
- **APIs**: Integrated clients for DexScreener, Pump.fun, X, and Telegram
- **Styling**: Gradient-based modern UI with responsive design

### API Clients
- **DexscreenerClient**: Real token pair data from DexScreener API
- **PumpfunClient**: Token launch data from Pump.fun API
- **XClient**: Mock implementation for X profile search (ready for real API integration)
- **TelegramGroupsClient**: Mock implementation for group search (ready for real API integration)

### File Structure
```
src/
├── static/
│   ├── index.html          # Dashboard HTML
│   ├── css/dashboard.css   # Dashboard styles
│   └── js/dashboard.js     # Dashboard JavaScript
├── api/
│   ├── routes/
│   │   └── dashboard_search.py  # Dashboard API endpoints
│   └── clients/
│       ├── dexscreener.py       # DexScreener API client
│       ├── pumpfun.py           # Pump.fun API client
│       ├── x_client.py          # X API client (mock)
│       └── telegram_groups.py   # Telegram groups client (mock)
```

## Configuration

The dashboard runs on the same port as the main bot application. You can configure the port in the `.env` file:

```env
PORT=8002
```

## Future Enhancements

1. **Real X Integration**: Replace mock data with actual X API integration
2. **Real Telegram Search**: Implement actual Telegram group search
3. **Authentication**: Add user authentication for personalized features
4. **Favorites**: Allow users to save favorite tokens/groups/profiles
5. **Alerts**: Set up alerts for specific search criteria
6. **Charts**: Add price charts and analytics visualization
7. **Export**: Export search results and trending data

## Examples

### Search Example
```javascript
// Search for "Solana" across all platforms
fetch('/dashboard/search/all?query=Solana&limit=10')
  .then(response => response.json())
  .then(data => console.log(data));
```

### Get Trending Data
```javascript
// Get trending data from all platforms
fetch('/dashboard/trending')
  .then(response => response.json())
  .then(data => console.log(data));
```

## Support

For issues or feature requests related to the dashboard, please refer to the main project documentation or create an issue in the project repository.
