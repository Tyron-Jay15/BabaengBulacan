# BabaengBulacan Frontend

A comprehensive frontend implementation for the BabaengBulacan web system - Gender-Based Violence Reporting and Women Empowerment Platform for Bulacan Province.

## Overview

This frontend provides a user-friendly, accessible, and secure interface for:
- Anonymous incident reporting
- Case tracking and management
- Program enrollment and management
- Resource access and service directory
- Analytics and reporting dashboard

## Technology Stack

- **HTML5**: Semantic markup
- **CSS3**: Custom styles with Bootstrap 5
- **JavaScript**: Vanilla JS with jQuery for DOM manipulation
- **Bootstrap 5**: Responsive framework
- **Chart.js**: Data visualization
- **SweetAlert2**: Beautiful alerts and confirmations
- **Django Templates**: Server-side rendering

## Project Structure

```
babaengbulacan-frontend/
├── templates/
│   ├── base.html                 # Base template with navigation
│   ├── components/               # Reusable components
│   │   ├── navbar.html          # Navigation bar
│   │   ├── footer.html          # Site footer
│   │   ├── alerts.html          # Message alerts
│   │   ├── sidebar.html         # Sidebar navigation
│   │   └── safe-exit-button.html # Emergency exit button
│   ├── pages/
│   │   ├── home.html            # Homepage
│   │   ├── about.html           # About page
│   │   ├── contact.html         # Contact page
│   │   └── privacy.html         # Privacy policy
│   ├── reports/
│   │   ├── anonymous_report.html # Incident reporting form
│   │   ├── track_case.html      # Case tracking
│   │   └── report_success.html  # Success confirmation
│   ├── cases/
│   │   └── dashboard.html       # Case management dashboard
│   ├── programs/
│   │   └── program_list.html    # Program catalog
│   ├── resources/
│   │   └── resource_center.html # Resource center
│   ├── analytics/
│   │   └── dashboard.html       # Analytics dashboard
│   ├── accounts/
│   │   └── login.html           # User login
│   └── errors/
│       └── 404.html             # Error pages
├── static/
│   ├── css/
│   │   ├── main.css            # Main stylesheet
│   │   └── components.css      # Component styles
│   ├── js/
│   │   ├── main.js             # Main JavaScript
│   │   └── utils.js            # Utility functions
│   └── images/                  # Static images
└── README.md
```

## Key Features

### 1. Anonymous Reporting System
- Multi-step form wizard
- File upload capability
- Privacy assurance messaging
- Safe exit button for user safety

### 2. Case Management Dashboard
- Interactive data tables
- Advanced filtering and search
- Status tracking and visualization
- Export functionality

### 3. Program Enrollment
- Program catalog with filters
- Enrollment management
- Progress tracking

### 4. Resource Center
- Legal information
- Service directory
- FAQ section
- Emergency contacts

### 5. Analytics Dashboard
- Chart.js visualizations
- Date range filtering
- Data export options

## Security Features

- Safe exit button (ESC key + floating button)
- Anonymous reporting options
- Input validation and sanitization
- CSRF protection
- Secure session management

## Accessibility

- WCAG 2.1 AA compliance
- Screen reader support
- Keyboard navigation
- High contrast options
- Mobile-responsive design

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers

## Development Setup

1. Ensure Django is installed and configured
2. Place templates in the correct Django template directories
3. Update Django settings for static files and templates
4. Run migrations and start the development server

## CDN Dependencies

All external libraries are loaded via CDN for quick setup:

- Bootstrap 5.3.0
- Font Awesome 6.4.0
- jQuery 3.7.0
- Chart.js 4.3.0
- SweetAlert2 11.x
- DataTables 1.13.6

## Customization

### Color Scheme
Primary: #7B2CBF (Purple)
Secondary: #FF6B35 (Orange)
Success: #28a745 (Green)
Danger: #dc3545 (Red)

### Typography
- Inter font family
- Responsive font sizes
- High contrast ratios

## Performance

- Optimized images and assets
- Lazy loading where applicable
- Minified CSS and JavaScript
- Efficient DOM manipulation

## Future Enhancements

- Progressive Web App (PWA) capabilities
- Offline functionality
- Real-time notifications
- Advanced map integrations
- Multi-language support

## Contributing

1. Follow the established coding standards
2. Ensure accessibility compliance
3. Test across multiple browsers
4. Document any new features
5. Maintain security best practices

## License

This project is developed for the Province of Bulacan, Philippines, as part of the gender-based violence prevention and women empowerment initiatives.