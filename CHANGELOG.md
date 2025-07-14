# Changelog

All notable changes to the Falco AI Alert System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.5] - 2024-12-19

### Added
- Enhanced dark/light mode compatibility across all UI components
- Improved notification system with better visibility in both themes
- Added proper spacing between navigation bar and filter controls
- Enhanced responsive design for mobile and desktop experiences

### Changed
- Updated pagination system in runtime events page for better usability
- Improved filter button functionality and styling
- Enhanced notification styling using dynamic CSS variables
- Optimized default pagination size to 25 items per page

### Fixed
- Fixed pagination visibility issues in light mode
- Resolved notification background transparency issues
- Removed debug styles and console logs from production code
- Fixed filter controls spacing and layout issues
- Improved code maintainability and readability

### Technical
- Updated Docker image version to v2.0.5
- Enhanced CSS variable usage for better theme consistency
- Improved error handling and user feedback
- Streamlined UI component structure

## [2.0.0] - 2024-12-18

### Added
- Complete MCP (Model Context Protocol) integration with 15 security tools
- Multilingual support for AI analysis
- Enhanced web dashboard with dark/light mode toggle
- Kubernetes production deployment with auto-scaling
- Comprehensive Slack integration
- Weaviate vector database integration for AI-enhanced search

### Changed
- Major UI/UX overhaul with modern design
- Improved alert processing and analysis pipeline
- Enhanced security features and configurations
- Updated deployment scripts and documentation

### Fixed
- Various bug fixes and performance improvements
- Enhanced error handling and logging
- Improved container security and resource management

## [1.0.0] - 2024-12-01

### Added
- Initial release of Falco AI Alert System
- Basic webhook processing for Falco alerts
- Simple web dashboard
- OpenAI integration for alert analysis
- Basic Docker deployment

---

## Version History

- **v2.0.5**: UI/UX improvements and bug fixes
- **v2.0.0**: Major release with MCP integration and enhanced features
- **v1.0.0**: Initial release with basic functionality 