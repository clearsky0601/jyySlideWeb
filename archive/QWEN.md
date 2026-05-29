# jyySlideWeb - Project Context

## Project Overview

jyySlideWeb is a web-based presentation tool that allows users to create and edit slides using Markdown syntax. The application provides real-time conversion of Markdown content into interactive slideshows with features like automatic saving, image upload, and live preview. It's built using Django with WebSocket support for real-time functionality.

### Key Features
- Real-time Markdown to slide conversion
- Live preview synchronized with editing position
- Automatic saving functionality (every minute, on window close, and when returning to homepage)
- Automatic title extraction from the first H1 header
- Drag-and-drop or paste-to-upload image functionality
- Public sharing with read-only mode for published slides
- Support for fragment animations and section transitions

### Architecture
- Backend: Django with Django Channels for WebSocket support
- Frontend: HTML, CSS, JavaScript with real-time editing capabilities
- Database: SQLite3 (default) with option to use PostgreSQL via environment configuration
- Server: Daphne ASGI server for handling both HTTP and WebSocket connections
- File Storage: Local file system for uploaded images

## Building and Running

### Docker Deployment (Recommended)
```bash
# Using prebuilt image
docker-compose up
```

### From Source
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
daphne -p 10001 jyy_slide_web.asgi:application
```

### Windows Binary
The project can be run directly using the compiled executable from releases, though real-time conversion may be slower than other deployment methods.

## Configuration

- Default port: 10001
- Default admin user: 'admin' with password 'admin@django'
- Static files location: `/static/` 
- Media files location: `/media/` (for uploaded images)
- Database: `db.sqlite3` (can be changed to PostgreSQL via environment variables)

## Development Conventions

- The application uses Django's MTV (Model-Template-View) pattern
- WebSocket connections handle real-time slide updates and previews
- Markdown content is converted to slides using a custom converter based on jyyslide-md
- Security: CSRF protection with configurable trusted origins
- Authentication: Standard Django authentication for editing capabilities

## Project Structure
```
jyySlideWeb/
├── jyy_slide_web/          # Django project settings
├── slideapp/              # Main application logic
│   ├── models.py          # Slide data model
│   ├── views.py           # Request handling logic
│   ├── consumers.py       # WebSocket handlers
│   ├── src/converter.py   # Markdown to HTML conversion
│   └── templates/         # HTML templates
├── staticfiles/           # Static assets (CSS, JS, images)
├── media/                 # Uploaded media files
└── db.sqlite3             # Default SQLite database
```

## Key Components

### Core Functionality
- **Slide model**: Represents a presentation with title, content, creation time, and lock status
- **WebSocket consumers**: Handle real-time editing and preview updates
- **Markdown converter**: Custom implementation for converting Markdown to Reveal.js slides
- **Image upload**: Direct upload with automatic URL insertion into editor

### Security
- Slides are private by default (locked)
- Public slides are read-only
- Standard Django authentication for editing access
- CSRF protection with configurable trusted origins

### Deployment
- Docker support with automatic updates via Watchtower
- Nginx configuration examples for both HTTP and HTTPS
- Static file serving via WhiteNoise