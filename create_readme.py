#!/usr/bin/env python
# -*- coding: utf-8 -*-

readme_content = """<div align="center">

# 🚀 BMSgo - Smart Business Management System

### Complete Inventory, Sales & Financial Management Solution

[![Live Demo](https://img.shields.io/badge/Live-Demo-success?style=for-the-badge&logo=google-chrome)](https://bmsgo.online)
[![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?style=for-the-badge&logo=bootstrap)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**[Try Demo](https://bmsgo.online) • [Documentation](./INSTALLATION.md) • [Report Bug](https://github.com/MfFischer/smart-inventory-management/issues) • [Request Feature](https://github.com/MfFischer/smart-inventory-management/issues)**

</div>

---

## 📋 Table of Contents

- [About](#-about)
- [Key Features](#-key-features)
- [Demo Mode](#-demo-mode)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Deployment Options](#-deployment-options)
- [Architecture](#-architecture)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🎯 About

**BMSgo** is a comprehensive business management system designed for small to medium-sized businesses. It provides powerful inventory tracking, point-of-sale functionality, financial management, and detailed reporting - all in a modern, easy-to-use interface.

### Why BMSgo?

✅ **Complete Solution** - Inventory, sales, expenses, suppliers, and reports in one place  
✅ **Modern UI** - Beautiful, responsive design that works on any device  
✅ **Demo Mode** - Try all features instantly without signing up  
✅ **Offline Capable** - Available as standalone desktop application  
✅ **Role-Based Access** - Owner, Admin, and Staff roles with granular permissions  
✅ **Real-Time Alerts** - Low stock notifications and automated reminders  
✅ **Export Ready** - Generate PDF and Excel reports  

---

## ✨ Key Features

### 📦 Inventory Management
- Real-time stock tracking across multiple locations
- Low stock alerts with email notifications
- Barcode scanning support
- Returns and damaged items tracking
- Automatic reorder point calculations

### 💰 Sales & POS
- Fast checkout process
- Receipt generation and printing
- Sales history and search
- Profit margin tracking
- Customer management

### 💵 Financial Management
- Expense tracking and categorization
- Accounts receivable and payable
- Profit & loss reports
- Cash flow monitoring
- Overdue payment alerts

### 📊 Reports & Analytics
- Sales reports (daily, weekly, monthly)
- Inventory reports with valuation
- Financial reports (P&L, cash flow)
- Accounts receivable/payable aging
- Returned/damaged items reports
- Export to PDF and Excel

### 👥 User Management
- Multi-user support
- Role-based access control (Owner, Admin, Staff)
- Activity tracking
- Secure authentication with Flask-Login

### 🏢 Business Settings
- Customizable business profile
- Email configuration
- Subscription management (Stripe integration)
- Announcement system

---

## 🎮 Demo Mode

Try BMSgo **instantly** without creating an account!

**[Click here to try the demo](https://bmsgo.online)** → Click "Try Demo Now"

**Demo Features:**
- ✅ Full access to all features
- ✅ Pre-loaded sample data (products, sales, expenses)
- ✅ Safe environment - no data is saved
- ✅ Perfect for evaluating the system

**Note:** Demo data is stored in your browser session and automatically cleared when you exit.

---

## 🛠️ Tech Stack

### Backend
- **Python 3.12** - Core programming language
- **Flask 3.0** - Web framework
- **SQLAlchemy** - ORM for database operations
- **MySQL** - Primary database
- **Flask-Login** - User authentication
- **APScheduler** - Scheduled tasks and alerts

### Frontend
- **Bootstrap 5.3** - Responsive UI framework
- **Chart.js 4.4** - Interactive charts and visualizations
- **Font Awesome 6.4** - Icons
- **Vanilla JavaScript** - Client-side interactivity

### Integrations
- **Stripe** - Payment processing for subscriptions
- **Gmail SMTP** - Email notifications
- **FPDF** - PDF report generation
- **Pandas** - Excel export functionality

### DevOps
- **PyInstaller** - Standalone executable builder
- **Gunicorn** - WSGI HTTP server
- **Nginx** - Reverse proxy (production)
"""

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme_content)

print("README.md created successfully!")

