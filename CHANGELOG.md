# Changelog

All notable changes to the Falco AI Alert System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.1] - 2025-01-17

### Added
- **Comprehensive Operational Commands Guide**: New `k8s/OPERATIONAL_COMMANDS.md` with 500+ operational commands
- **Multi-Architecture EKS Support**: Enhanced EKS overlay with proper AMD64 and ARM64 support
- **Cost Optimization Features**: ARM64 Graviton instance support for 20-40% cost savings
- **EKS-Specific Troubleshooting**: Dedicated troubleshooting commands for AWS EKS deployments
- **Architecture Verification Commands**: Tools to verify multi-architecture deployments
- **Post-Deployment Operations**: Comprehensive port forwarding, UI access, and monitoring commands
- **Database Operations Guide**: Backup, restore, and maintenance procedures
- **Performance Monitoring**: Resource usage analysis and optimization commands
- **Emergency Commands**: Quick reference for critical situations

### Enhanced
- **EKS Configuration**: Updated `overlays/eks/kustomization.yaml` with proper node affinity for multi-architecture
- **Installation Scripts**: Added operational commands references to `install.sh` and `install-dynamic.sh`
- **Cloud Documentation**: Enhanced all cloud deployment guides with operational commands references
- **README Documentation**: Updated main README with comprehensive operational commands section

### Fixed
- **EKS Node Selection**: Removed hard-coded AMD64-only node selector, now supports both architectures
- **Multi-Architecture Images**: Verified and documented existing multi-arch container support
- **Cost Optimization**: Proper ARM64 Graviton instance support for AWS cost savings

### Operational
- **Port Forwarding**: Commands for all environments (dev/prod) and components (app/ollama/weaviate)
- **Log Management**: Comprehensive log checking, filtering, and export procedures
- **Status Monitoring**: Health checks, deployment status, and resource monitoring
- **Configuration Management**: ConfigMap and Secret management with restart procedures
- **Scaling Operations**: Manual scaling, HPA monitoring, and resource management
- **Troubleshooting**: Common issue resolution and debugging procedures

## [2.1.0] - 2025-01-17

### Added
- **JSON-RPC MCP Integration**: Universal AI client compatibility via stdio protocol
- **Unified MCP Hub**: Consolidated all MCP interfaces into single dashboard
- **Multi-Protocol MCP Support**: JSON-RPC, Claude-optimized, gRPC, and Standard MCP
- **Auto-Setup Scripts**: Automated configuration for Claude Desktop, VS Code, and Cursor
- **Web-Based MCP Configuration**: Real-time setup and testing interface
- **15 Security Tools for AI Clients**: Complete toolset accessible via MCP protocol
- **Comprehensive Alert Filtering**: Filter by rule, container, user, process, command, file path, Kubernetes data, alert content, AI analysis status
- **Advanced Sorting Options**: Sort by timestamp, priority, rule name (ascending/descending)
- **Filter Status Indicator**: Real-time display of active filters with count and descriptions
- **Filter Save/Load**: Save frequently used filter configurations for quick access
- **Debounced Text Filtering**: Smooth performance with automatic filtering as you type
- **Dashboard Filter Enhancement**: Extended Dashboard with same comprehensive filtering system as Runtime Events

### Changed
- **Navigation Simplification**: Consolidated 3 MCP menu items into 1 dropdown
- **Unified Styling**: Applied consistent design across all MCP interfaces
- **Enhanced User Experience**: Single location for all MCP setup and configuration
- **Improved Documentation**: Streamlined integration guides and setup instructions
- **Dashboard Parity**: Dashboard now supports identical filtering capabilities as Runtime Events page

### Fixed
- **Backward Compatibility**: All legacy MCP URLs redirect to appropriate tabs
- **Route Consolidation**: Eliminated duplicate configuration pages
- **Documentation Cleanup**: Removed redundant MD files and consolidated information
- **Runtime Events Filters**: Fixed non-functional filter buttons (Total, Critical, Unread, Recent)
- **Filter Error Handling**: Added robust error handling and validation for filter operations
- **Dashboard Filter System**: Replaced basic Dashboard filters with comprehensive multi-row filter grid

### Removed
- **Redundant Templates**: Deleted 3 old MCP templates (consolidated into unified dashboard)
- **Duplicate Documentation**: Removed MCP_CONSOLIDATION_SUMMARY.md and JSON_RPC_STDIO_GUIDE.md
- **Navigation Clutter**: Simplified from 3 separate MCP menu items to 1 organized dropdown

### Technical
- **Template Unification**: Reduced 3 separate templates to 1 unified dashboard
- **Smart URL Routing**: Tab-based navigation with parameter support
- **Enhanced Testing**: Comprehensive test suites for all MCP protocols
- **Configuration Templates**: Auto-generated client configs with correct paths

## [2.0.0] - 2024-12-19

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
- Updated Docker image version to v2.0.0
- Enhanced CSS variable usage for better theme consistency
- Improved error handling and user feedback
- Streamlined UI component structure

## [1.6.0] - 2024-12-18

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

- **v2.0.0**: Major release with UI/UX improvements, MCP integration and enhanced features
- **v1.6.0**: MCP integration and multilingual support
- **v1.0.0**: Initial release with basic functionality 