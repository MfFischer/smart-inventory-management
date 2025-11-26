from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from datetime import datetime
import os
from flask import current_app
from modules.utils.logger import setup_logger
from dotenv import load_dotenv

load_dotenv()

logger = setup_logger('email_automation')


class EmailAutomation:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmailAutomation, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.app = None
            self.scheduler = BackgroundScheduler()
            # Move Gmail credentials to init_app to ensure they're loaded with app context
            self.gmail_user = None
            self.gmail_password = None
            self.initialized = True

    def init_app(self, app):
        """Initialize with Flask app context"""
        self.app = app
        # Load Gmail credentials from environment or app config
        self.gmail_user = app.config.get('MAIL_USERNAME') or os.environ.get('GMAIL_USER')
        self.gmail_password = app.config.get('MAIL_PASSWORD') or os.environ.get('GMAIL_APP_PASSWORD')

        if not self.gmail_user or not self.gmail_password:
            logger.error("Gmail credentials not configured!")
            return

        try:
            self.scheduler.start()
            self.scheduler.add_job(
                func=self.check_trial_reminders,
                trigger=CronTrigger(hour=9),
                id='trial_reminder_check',
                name='Check trial expiration and send reminders'
            )
            logger.info("Email automation scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start email automation scheduler: {str(e)}")

    def send_email(self, to_email, subject, html_content):
        print(f"\nStarting email send process...")
        print(f"To: {to_email}")
        print(f"From: {self.gmail_user}")
        print(f"Subject: {subject}")

        if not self.gmail_user or not self.gmail_password:
            print("ERROR: Missing Gmail credentials!")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"BMSgo <{self.gmail_user}>"
        msg['To'] = to_email

        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        try:
            print("\nAttempting SMTP connection...")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as smtp_server:
                print("SMTP connection established")

                print("Attempting login...")
                smtp_server.login(self.gmail_user, self.gmail_password)
                print("Login successful")

                print("Sending email...")
                smtp_server.sendmail(self.gmail_user, to_email, msg.as_string())
                print("Email sent successfully!")

                return True
        except smtplib.SMTPAuthenticationError as auth_error:
            print(f"Authentication failed: {str(auth_error)}")
            return False
        except smtplib.SMTPException as smtp_error:
            print(f"SMTP error occurred: {str(smtp_error)}")
            return False
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return False

    def send_welcome_email(self, user):
        """Send strategic welcome email highlighting BMSgo's value proposition"""
        subject = "Welcome to BMSgo - Your All-in-One Business Management Solution!"
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5282;">Welcome to the Future of Business Management, {user.first_name}! 🚀</h2>
                    <p>Congratulations on taking the first step towards transforming your business with BMSgo - your all-in-one smart business management solution!</p>

                    <div style="background-color: #f7fafc; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #2c5282; margin: 0 0 15px 0;">🌟 Unleash Your Business Potential</h3>
                        <p>BMSgo brings you a powerful suite of tools designed to streamline your operations:</p>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>Smart Inventory Control:</strong> Never miss a sale or overstock again</li>
                            <li><strong>Real-time Analytics:</strong> Make data-driven decisions with confidence</li>
                            <li><strong>Seamless Sales Management:</strong> From quote to payment, all in one place</li>
                            <li><strong>Financial Intelligence:</strong> Keep your finances healthy and growing</li>
                        </ul>
                    </div>

                    <div style="background-color: #ebf8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #2c5282; margin: 0 0 15px 0;">💡 Quick Start Guide</h3>
                        <p><strong>Here's your 3-step path to success:</strong></p>
                        <ol style="margin: 0; padding-left: 20px;">
                            <li>Set up your business profile and add your team members</li>
                            <li>Import your inventory and connect with suppliers</li>
                            <li>Start tracking sales and watching your business grow</li>
                        </ol>
                    </div>

                    <div style="background-color: #e6fffa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #2c5282; margin: 0 0 15px 0;">🎯 Your 30-Day Success Journey</h3>
                        <p>During your trial until {user.trial_expiry_date.strftime('%B %d, %Y')}, you'll have full access to:</p>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Comprehensive business analytics and reporting</li>
                            <li>Automated inventory management</li>
                            <li>Integrated supplier and customer management</li>
                            <li>Complete financial tracking and insights</li>
                        </ul>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <p style="font-size: 18px; font-weight: bold; color: #2c5282;">Ready to revolutionize your business?</p>
                        <a href="https://bmsgo.online/getting-started" style="background-color: #4299e1; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">Get Started Now</a>
                    </div>

                    <p style="margin-top: 20px;">To your success,<br>The BMSgo Team</p>
                </div>
            </body>
        </html>
        """
        self.send_email(user.email, subject, html)

    def send_trial_expiry_reminder(self, user, days_remaining):
        """Send strategic trial expiration reminder"""
        subject = f"Don't Miss Out! Your BMSgo Trial Ends in {days_remaining} Days"
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5282;">Keep Your Business Growing with BMSgo!</h2>
                    <p>Hello {user.first_name},</p>

                    <div style="background-color: #fff5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="font-size: 16px; font-weight: bold;">⏰ Your trial ends in {days_remaining} days!</p>
                        <p>Don't lose access to the tools that are helping you:</p>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Streamline your operations</li>
                            <li>Boost your sales</li>
                            <li>Optimize your inventory</li>
                            <li>Grow your business</li>
                        </ul>
                    </div>

                    <div style="background-color: #f7fafc; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #2c5282; margin: 0 0 15px 0;">🌟 Exclusive Subscription Benefits</h3>
                        <div style="margin-bottom: 15px;">
                            <p style="font-weight: bold; margin: 0;">Monthly Plan: $14.99/month</p>
                            <ul style="margin: 5px 0 0 0; padding-left: 20px;">
                                <li>Full access to all features</li>
                                <li>Regular updates and improvements</li>
                                <li>Priority customer support</li>
                            </ul>
                        </div>

                        <div style="background-color: #ebf8ff; padding: 10px; border-radius: 5px;">
                            <p style="font-weight: bold; margin: 0;">Annual Plan: $149.90/year (Save 17%!)</p>
                            <ul style="margin: 5px 0 0 0; padding-left: 20px;">
                                <li>All monthly plan features</li>
                                <li>2 months free</li>
                                <li>Advanced analytics</li>
                                <li>VIP support</li>
                            </ul>
                        </div>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://bmsgo.online/subscribe" style="background-color: #4299e1; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">Upgrade Now & Save</a>
                    </div>

                    <p>Still evaluating? Our team is here to help you make the most of BMSgo. Reply to this email with your questions!</p>

                    <p style="margin-top: 20px;">Best regards,<br>The BMSgo Team</p>
                </div>
            </body>
        </html>
        """
        self.send_email(user.email, subject, html)

    def send_subscription_confirmation(self, user, plan_type):
        """Send strategic subscription confirmation"""
        plan_details = "monthly" if plan_type == "monthly" else "annual"
        subject = "Welcome to the BMSgo Family! Your Subscription is Active"
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5282;">Thank You for Choosing BMSgo!</h2>
                    <p>Dear {user.first_name},</p>

                    <div style="background-color: #f0fff4; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #2c5282; margin: 0 0 15px 0;">🎉 Your {plan_details} subscription is now active!</h3>
                        <p>You now have unlimited access to BMSgo's complete suite of business management tools.</p>
                    </div>

                    <div style="background-color: #f7fafc; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #2c5282; margin: 0 0 15px 0;">📈 Next Steps for Success</h3>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Explore our advanced reporting features</li>
                            <li>Set up automated inventory alerts</li>
                            <li>Customize your dashboard</li>
                            <li>Connect with your team members</li>
                        </ul>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <p>Need help maximizing BMSgo for your business?</p>
                        <a href="https://bmsgo.online/support" style="background-color: #4299e1; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">Schedule a Free Consultation</a>
                    </div>

                    <p style="margin-top: 20px;">Here's to your business success!<br>The BMSgo Team</p>
                </div>
            </body>
        </html>
        """
        self.send_email(user.email, subject, html)

    def send_low_inventory_alert(self, user, low_stock_items):
        """Send low inventory alert email"""
        subject = "BMSgo - Low Inventory Alert!"
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5282;">⚠️ Low Inventory Alert</h2>
                    <p>Hello {user.first_name},</p>

                    <div style="background-color: #fff5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p>The following items have reached their reorder point:</p>
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background-color: #fed7d7;">
                                    <th style="padding: 8px; text-align: left;">Product</th>
                                    <th style="padding: 8px; text-align: center;">Current Stock</th>
                                    <th style="padding: 8px; text-align: center;">Reorder Point</th>
                                </tr>
                            </thead>
                            <tbody>
                                {self._generate_low_stock_rows(low_stock_items)}
                            </tbody>
                        </table>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{current_app.config.get('SITE_URL', 'https://bmsgo.online')}/inventory" 
                           style="background-color: #4299e1; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Manage Inventory
                        </a>
                    </div>

                    <p style="margin-top: 20px;">Best regards,<br>The BMSgo Team</p>
                </div>
            </body>
        </html>
        """
        self.send_email(user.email, subject, html)

    def send_payment_failed_notification(self, user, error_message=None):
        """Send payment failure notification"""
        subject = "BMSgo - Important: Payment Failed"
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5282;">⚠️ Payment Failed</h2>
                    <p>Hello {user.first_name},</p>

                    <div style="background-color: #fff5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p>We were unable to process your recent payment for your BMSgo subscription.</p>
                        {f'<p><strong>Error details:</strong> {error_message}</p>' if error_message else ''}
                        <p>Please update your payment information to ensure uninterrupted access to BMSgo.</p>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{current_app.config.get('SITE_URL', 'https://bmsgo.online')}/billing" 
                           style="background-color: #4299e1; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Update Payment Method
                        </a>
                    </div>

                    <p style="margin-top: 20px;">Best regards,<br>The BMSgo Team</p>
                </div>
            </body>
        </html>
        """
        self.send_email(user.email, subject, html)

    def check_trial_reminders(self):
        """Check and send trial reminders"""
        with self.app.app_context():
            try:
                from modules.users.models import User  # Import here to avoid circular imports

                # Get users with active trials
                users = User.query.filter(
                    User.trial_expiry_date.isnot(None),
                    User.notification_sent == False
                ).all()

                for user in users:
                    days_remaining = (user.trial_expiry_date - datetime.now()).days
                    if days_remaining in [7, 3, 1]:  # Send reminders at these intervals
                        self.send_trial_expiry_reminder(user, days_remaining)
                        user.notification_sent = True
                        user.save()

            except Exception as e:
                logger.error(f"Error in check_trial_reminders: {str(e)}")

    def check_low_inventory(self):
        """Check and send low inventory alerts"""
        with self.app.app_context():
            try:
                from modules.users.models import User, Inventory  # Import here to avoid circular imports

                # Get all items with low stock
                low_stock_items = Inventory.query.filter(
                    Inventory.quantity <= Inventory.reorder_point
                ).all()

                # Group items by user
                user_items = {}
                for item in low_stock_items:
                    if item.user_id not in user_items:
                        user_items[item.user_id] = []
                    user_items[item.user_id].append(item)

                # Send alerts to each user
                for user_id, items in user_items.items():
                    user = User.query.get(user_id)
                    if user and user.email:
                        self.send_low_inventory_alert(user, items)

            except Exception as e:
                logger.error(f"Error in check_low_inventory: {str(e)}")

    def _generate_low_stock_rows(self, items):
        """Helper method to generate HTML table rows for low stock items"""
        rows = ""
        for item in items:
            rows += f"""
                <tr>
                    <td style="padding: 8px; border-top: 1px solid #eee;">{item.name}</td>
                    <td style="padding: 8px; border-top: 1px solid #eee; text-align: center;">{item.quantity}</td>
                    <td style="padding: 8px; border-top: 1px solid #eee; text-align: center;">{item.reorder_point}</td>
                </tr>
            """
        return rows

    def cleanup(self):
        """Cleanup method to be called when shutting down the application"""
        self.scheduler.shutdown()

# Create a single instance
email_automation = EmailAutomation()
