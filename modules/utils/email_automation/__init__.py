from .email_automation import EmailAutomation

# Create a singleton instance
email_automation = EmailAutomation()

# Export what should be available
__all__ = ['email_automation']